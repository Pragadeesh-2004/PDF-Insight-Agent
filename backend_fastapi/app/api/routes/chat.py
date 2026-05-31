"""
Chat API Routes
Handles messaging and question answering
"""

from fastapi import APIRouter, Depends, HTTPException
from app.models.schemas import ChatRequest, ChatResponse
from app.services.rag_service import get_rag_service
from app.core.database import get_db
from app.core.config import settings
from datetime import datetime
import logging
import uuid

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/message")
async def chat_message(request: ChatRequest) -> ChatResponse:
    """
    Send a message and get an answer based on agent type
    
    - GENERAL_ASSISTANT: Direct LLM query without RAG
    - PDF_INSIGHT_AGENT: RAG with fallback to direct LLM if no context
    
    Args:
        request: ChatRequest with session_id, message, agent_type
        
    Returns:
        ChatResponse with answer and metadata
    """
    try:
        logger.info(f"💬 Chat message from session {request.session_id}: '{request.message[:50]}...' (agent: {request.agent_type})")
        
        # Validate session exists
        try:
            db = get_db()
        except RuntimeError as e:
            logger.error(f"❌ Database not available: {e}")
            raise HTTPException(status_code=503, detail="Database connection not available")
        
        sessions_collection = db[settings.MONGODB_SESSIONS_COLLECTION]
        session = await sessions_collection.find_one({"_id": request.session_id})
        
        if not session:
            logger.warning(f"⚠️  Session not found: {request.session_id}")
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Initialize response
        rag_result = None
        
        # Route based on agent type
        if request.agent_type == "GENERAL_ASSISTANT":
            # ===== GENERAL ASSISTANT MODE: Direct LLM query =====
            logger.info("🤖 GENERAL_ASSISTANT mode: Querying LLM directly (no RAG)")
            try:
                rag_service = get_rag_service()
                rag_result = await rag_service.generate_direct_answer(request.message)
                rag_result["source"] = "DIRECT_LLM"
                rag_result["chunks_retrieved"] = 0
                logger.info(f"✅ Direct LLM response generated ({len(rag_result['answer'])} chars)")
            except Exception as e:
                logger.error(f"❌ Direct LLM query failed: {e}", exc_info=True)
                rag_result = {
                    "answer": f"I encountered an error: {str(e)}",
                    "chunks_retrieved": 0,
                    "status": "error",
                    "source": "DIRECT_LLM"
                }
        
        elif request.agent_type == "PDF_INSIGHT_AGENT":
            # ===== PDF INSIGHT AGENT MODE: RAG with fallback =====
            logger.info("📄 PDF_INSIGHT_AGENT mode: Attempting RAG retrieval")
            try:
                rag_service = get_rag_service()
                rag_result = await rag_service.answer_question(
                    query=request.message,
                    session_id=request.session_id
                )
                
                # If no chunks found, or the strict document prompt says the
                # answer is outside the PDF, fallback to direct LLM.
                chunks_found = rag_result.get("chunks_retrieved", 0)
                rag_status = rag_result.get("status")
                if chunks_found == 0 or rag_status in {"no_context", "document_unavailable"}:
                    logger.info("⚠️  PDF context unavailable for query, falling back to direct LLM")
                    rag_result = await rag_service.generate_direct_answer(request.message)
                    rag_result["source"] = "FALLBACK_LLM"
                else:
                    rag_result["source"] = "DOCUMENT_RAG"
                    
            except Exception as e:
                logger.error(f"❌ RAG pipeline failed: {e}", exc_info=True)
                # Fallback to direct LLM on error
                try:
                    rag_service = get_rag_service()
                    rag_result = await rag_service.generate_direct_answer(request.message)
                    rag_result["source"] = "FALLBACK_LLM"
                    logger.info("✅ Fallback to direct LLM successful")
                except Exception as fallback_e:
                    logger.error(f"❌ Fallback LLM also failed: {fallback_e}")
                    rag_result = {
                        "answer": f"I encountered errors in both RAG and direct query: {str(e)}",
                        "chunks_retrieved": 0,
                        "status": "error",
                        "source": "ERROR"
                    }
        
        else:
            logger.warning(f"⚠️  Unknown agent type: {request.agent_type}, defaulting to direct LLM")
            try:
                rag_service = get_rag_service()
                rag_result = await rag_service.generate_direct_answer(request.message)
                rag_result["source"] = "DIRECT_LLM"
            except Exception as e:
                rag_result = {
                    "answer": f"Unknown agent type. Error: {str(e)}",
                    "chunks_retrieved": 0,
                    "status": "error"
                }
        
        # Store chat message in history
        try:
            chat_history_collection = db[settings.MONGODB_CHAT_HISTORY_COLLECTION]
            
            message_record = {
                "_id": str(uuid.uuid4()),
                "sessionId": request.session_id,
                "userMessage": request.message,
                "assistantAnswer": rag_result["answer"],
                "agentType": request.agent_type,
                "contextChunksUsed": rag_result.get("chunks_retrieved", 0),
                "source": rag_result.get("source", "UNKNOWN"),
                "model": rag_result.get("model", "gemini-3.1-flash-lite"),
                "createdAt": datetime.utcnow(),
            }
            
            await chat_history_collection.insert_one(message_record)
        except Exception as e:
            logger.warning(f"⚠️  Failed to store chat history: {e}")
        
        # Update session last_accessed
        try:
            await sessions_collection.update_one(
                {"_id": request.session_id},
                {"$set": {"last_accessed": datetime.utcnow()}}
            )
        except Exception as e:
            logger.warning(f"⚠️  Failed to update session: {e}")
        
        logger.info(f"✅ Generated response ({len(rag_result['answer'])} chars, source: {rag_result.get('source', 'UNKNOWN')})")
        
        return ChatResponse(
            session_id=request.session_id,
            message=request.message,
            answer=rag_result["answer"],
            source=rag_result.get("source", "DOCUMENT_RAG"),
            context_used=rag_result.get("chunks_retrieved", 0),
            chunks_retrieved=rag_result.get("chunks_retrieved"),
            chunks_with_context=rag_result.get("chunks_with_context"),
            model=rag_result.get("model", "gemini-3.1-flash-lite"),
            timestamp=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error in chat message: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@router.get("/history/{session_id}")
async def get_chat_history(session_id: str, limit: int = 50):
    """
    Get chat history for a session
    
    Args:
        session_id: Session identifier
        limit: Maximum number of messages to return
        
    Returns:
        List of chat messages
    """
    try:
        db = get_db()
        
        # Validate session
        sessions_collection = db[settings.MONGODB_SESSIONS_COLLECTION]
        session = await sessions_collection.find_one({"_id": session_id})
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Get chat history
        chat_history_collection = db[settings.MONGODB_CHAT_HISTORY_COLLECTION]
        messages = await chat_history_collection.find(
            {"sessionId": session_id}
        ).sort("createdAt", -1).limit(limit).to_list(length=None)
        
        # Reverse to get chronological order
        messages.reverse()
        
        return {
            "session_id": session_id,
            "message_count": len(messages),
            "messages": messages
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting chat history: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving chat history: {str(e)}")
