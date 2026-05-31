"""
Session Management API Routes
Handles session lifecycle
"""

from fastapi import APIRouter, HTTPException
from app.models.schemas import SessionResponse, SessionInfo
from app.core.database import get_db
from app.core.config import settings
from datetime import datetime, timedelta
import logging
import uuid

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/create")
async def create_session() -> SessionResponse:
    """
    Create a new session
    
    Returns:
        SessionResponse with new session_id
    """
    try:
        session_id = str(uuid.uuid4())
        
        logger.info(f"🆕 Creating new session: {session_id}")
        
        db = get_db()
        sessions_collection = db[settings.MONGODB_SESSIONS_COLLECTION]
        
        session_record = {
            "_id": session_id,
            "created_at": datetime.utcnow(),
            "last_accessed": datetime.utcnow(),
            "document_count": 0,
            "message_count": 0,
            "expires_at": datetime.utcnow() + timedelta(hours=settings.SESSION_EXPIRY_HOURS),
        }
        
        await sessions_collection.insert_one(session_record)
        
        logger.info(f"✅ Session created: {session_id}")
        
        return SessionResponse(
            session_id=session_id,
            status="success",
            message="Session created successfully"
        )
        
    except Exception as e:
        logger.error(f"❌ Error creating session: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating session: {str(e)}")


@router.get("/{session_id}")
async def get_session(session_id: str) -> SessionInfo:
    """
    Get session information
    
    Args:
        session_id: Session identifier
        
    Returns:
        SessionInfo with session details
    """
    try:
        db = get_db()
        sessions_collection = db[settings.MONGODB_SESSIONS_COLLECTION]
        
        session = await sessions_collection.find_one({"_id": session_id})
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Get message count
        chat_history_collection = db[settings.MONGODB_CHAT_HISTORY_COLLECTION]
        message_count = await chat_history_collection.count_documents(
            {"sessionId": session_id}
        )
        
        logger.info(f"📋 Retrieved session info: {session_id}")
        
        return SessionInfo(
            session_id=session_id,
            created_at=session.get("created_at"),
            last_accessed=session.get("last_accessed"),
            document_count=session.get("document_count", 0),
            message_count=message_count,
            expires_at=session.get("expires_at")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting session: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving session: {str(e)}")


@router.delete("/{session_id}")
async def delete_session(session_id: str) -> SessionResponse:
    """
    Delete a session and all associated data
    
    Args:
        session_id: Session identifier
        
    Returns:
        SessionResponse with deletion status
    """
    try:
        logger.info(f"🗑️  Deleting session: {session_id}")
        
        db = get_db()
        
        # Delete session
        sessions_collection = db[settings.MONGODB_SESSIONS_COLLECTION]
        await sessions_collection.delete_one({"_id": session_id})
        
        # Delete chunks
        chunks_collection = db[settings.MONGODB_CHUNKS_COLLECTION]
        await chunks_collection.delete_many({"sessionId": session_id})
        
        # Delete documents
        documents_collection = db[settings.MONGODB_DOCUMENTS_COLLECTION]
        await documents_collection.delete_many({"sessionId": session_id})
        
        # Delete chat history
        chat_history_collection = db[settings.MONGODB_CHAT_HISTORY_COLLECTION]
        await chat_history_collection.delete_many({"sessionId": session_id})
        
        logger.info(f"✅ Session deleted: {session_id}")
        
        return SessionResponse(
            session_id=session_id,
            status="success",
            message="Session deleted successfully"
        )
        
    except Exception as e:
        logger.error(f"❌ Error deleting session: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting session: {str(e)}")


@router.post("/{session_id}/clear-documents")
async def clear_session_documents(session_id: str) -> SessionResponse:
    """
    Clear all documents and chunks from a session
    
    Args:
        session_id: Session identifier
        
    Returns:
        SessionResponse with clear status
    """
    try:
        logger.info(f"🗑️  Clearing documents for session: {session_id}")
        
        db = get_db()
        
        # Validate session
        sessions_collection = db[settings.MONGODB_SESSIONS_COLLECTION]
        session = await sessions_collection.find_one({"_id": session_id})
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Delete chunks
        chunks_collection = db[settings.MONGODB_CHUNKS_COLLECTION]
        await chunks_collection.delete_many({"sessionId": session_id})
        
        # Delete documents
        documents_collection = db[settings.MONGODB_DOCUMENTS_COLLECTION]
        await documents_collection.delete_many({"sessionId": session_id})
        
        # Update session
        await sessions_collection.update_one(
            {"_id": session_id},
            {"$set": {"document_count": 0, "last_document_id": None}}
        )
        
        logger.info(f"✅ Documents cleared: {session_id}")
        
        return SessionResponse(
            session_id=session_id,
            status="success",
            message="All documents cleared successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error clearing documents: {e}")
        raise HTTPException(status_code=500, detail=f"Error clearing documents: {str(e)}")
