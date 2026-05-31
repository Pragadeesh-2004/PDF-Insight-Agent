"""
RAG (Retrieval-Augmented Generation) Service
Handles question answering using retrieved context
"""

import logging
import warnings
from typing import List, Dict, Optional
from google import genai
from app.core.config import settings
from app.services.embedding_service import get_embedding_service
from app.services.vector_store import get_vector_store
from app.core.database import get_db

# Suppress deprecation warning for google.generativeai
warnings.filterwarnings("ignore", category=FutureWarning, module="google.generativeai")

logger = logging.getLogger(__name__)


class RAGService:
    """
    Implements RAG pipeline for question answering
    """
    DOCUMENT_UNAVAILABLE_ANSWER = "This information is not available in the provided document."
    
    def __init__(self):
        """
        Initialize RAG service
        """
        self.client = genai.Client(
        api_key=settings.GEMINI_API_KEY
    )
        self.chat_model = settings.GEMINI_CHAT_MODEL
        self.top_k = settings.TOP_K_RETRIEVAL
        self.similarity_threshold = settings.SIMILARITY_THRESHOLD
        
        logger.info(f"🤖 Initialized RAG Service (model: {self.chat_model})")
    
    async def retrieve_relevant_chunks(
        self,
        query: str,
        session_id: str,
        top_k: Optional[int] = None
    ) -> List[Dict]:
        """
        Retrieve relevant chunks for a query
        
        Args:
            query: User query
            session_id: Session identifier
            top_k: Number of chunks to retrieve
            
        Returns:
            List of relevant chunks
        """
        try:
            logger.info(f"🔍 Retrieving chunks for query: '{query}'")
            
            # Get embedding service (not async)
            embedding_service = get_embedding_service()
            vector_store = get_vector_store()
            
            # Generate query embedding
            query_embedding = await embedding_service.embed_query(query)
            
            # Retrieve chunks
            top_k = top_k or self.top_k
            results = await vector_store.search(
                query_embedding=query_embedding,
                session_id=session_id,
                top_k=top_k,
                similarity_threshold=self.similarity_threshold
            )
            
            logger.info(f"✅ Retrieved {len(results)} relevant chunks")
            return results
            
        except Exception as e:
            logger.error(f"❌ Error retrieving chunks: {e}")
            raise
    
    async def expand_context(
        self,
        chunks: List[Dict],
        session_id: str
    ) -> List[Dict]:
        """
        Expand context by including previous and next chunks
        
        Args:
            chunks: Main retrieved chunks
            session_id: Session identifier
            
        Returns:
            Chunks with expanded context
        """
        try:
            logger.info(f"📖 Expanding context for {len(chunks)} chunks...")
            
            db = get_db()
            collection = db[settings.MONGODB_CHUNKS_COLLECTION]
            
            expanded_chunks = []
            seen_chunk_ids = set()
            
            for chunk in chunks:
                chunk_index = chunk.get("chunkIndex", 0)
                document_id = chunk.get("documentId")
                
                # Get surrounding chunks
                context_chunks = await collection.find({
                    "sessionId": session_id,
                    "documentId": document_id,
                    "chunkIndex": {
                        "$gte": chunk_index - 1,
                        "$lte": chunk_index + 1
                    }
                }).sort("chunkIndex", 1).to_list(length=None)
                
                # Add all chunks (avoiding duplicates)
                for ctx_chunk in context_chunks:
                    chunk_id = str(ctx_chunk.get("_id"))
                    if chunk_id not in seen_chunk_ids:
                        ctx_chunk["isMainChunk"] = (ctx_chunk.get("chunkIndex") == chunk_index)
                        expanded_chunks.append(ctx_chunk)
                        seen_chunk_ids.add(chunk_id)
            
            logger.info(f"✅ Expanded to {len(expanded_chunks)} chunks (with context)")
            return expanded_chunks
            
        except Exception as e:
            logger.error(f"❌ Error expanding context: {e}")
            # Return original chunks if expansion fails
            return chunks
    
    async def generate_answer(
        self,
        query: str,
        context_chunks: List[Dict]
    ) -> Dict:
        """
        Generate answer using Gemini with retrieved context
        
        Args:
            query: User question
            context_chunks: Retrieved and expanded context chunks
            
        Returns:
            Answer with metadata
        """
        try:
            logger.info(f"💬 Generating answer for query: '{query}'")
            
            # Build context from chunks
            context_text = self._build_context(context_chunks)
            
            # Create system prompt
            system_prompt = self._create_system_prompt(context_text)
            
            # Combine system prompt and query into single text
            combined_prompt = f"{system_prompt}\n\nQuestion: {query}"
            
            # Generate response using client - pass content as plain string
            response = self.client.models.generate_content(
                model=self.chat_model,
                contents=combined_prompt,
            )
            answer = response.text
            
            logger.info(f"✅ Generated answer ({len(answer)} chars)")
            
            return {
                "answer": answer,
                "context_used": len(context_chunks),
                "query": query,
                "model": self.chat_model,
                "status": (
                    "document_unavailable"
                    if self._is_document_unavailable_answer(answer)
                    else "success"
                )
            }
            
        except Exception as e:
            logger.error(f"❌ Error generating answer: {e}")
            raise
    
    def _build_context(self, chunks: List[Dict]) -> str:
        """
        Build context string from chunks
        """
        try:
            context_parts = []
            
            for i, chunk in enumerate(chunks):
                text = chunk.get("text", "")
                chunk_index = chunk.get("chunkIndex", i)
                is_main = chunk.get("isMainChunk", False)
                
                # Mark context chunks
                if is_main:
                    context_parts.append(f"[PRIMARY CHUNK {chunk_index}]\n{text}")
                else:
                    context_parts.append(f"[CONTEXT CHUNK {chunk_index}]\n{text}")
            
            context = "\n\n---\n\n".join(context_parts)
            return context
            
        except Exception as e:
            logger.warning(f"⚠️  Error building context: {e}")
            return ""
    
    def _create_system_prompt(self, context: str) -> str:
        """
        Create system prompt with context
        """
        return f"""You are a helpful document analysis assistant. Answer questions based ONLY on the provided document context.

CRITICAL RULES:
1. Only use information from the provided document chunks.
2. If the answer is not in the document, respond with: "{self.DOCUMENT_UNAVAILABLE_ANSWER}"
3. Do not generate or assume data that is not explicitly stated.
4. Preserve tables, lists, and structured data from the document when presenting answers.
5. Use markdown formatting for better readability.
6. Include relevant quotes from the document when appropriate.

DOCUMENT CONTEXT:
{context}

---
Now answer the user's question using ONLY the above context."""

    def _is_document_unavailable_answer(self, answer: str) -> bool:
        """
        Detect when the document-grounded prompt could not answer the query.
        """
        normalized_answer = (answer or "").strip().strip('"').strip("'").rstrip(".").lower()
        normalized_unavailable = self.DOCUMENT_UNAVAILABLE_ANSWER.rstrip(".").lower()
        return normalized_answer == normalized_unavailable
    
    async def generate_direct_answer(self, query: str) -> Dict:
        """
        Generate answer using direct LLM query (no RAG context)
        Used for GENERAL_ASSISTANT mode or when no PDF context is available
        
        Args:
            query: User question
            
        Returns:
            Answer with metadata
        """
        try:
            logger.info(f"💬 Generating direct LLM response for: '{query}'")
            
            # Create general system prompt (no document context)
            system_prompt = """You are a helpful AI assistant. Provide accurate, helpful, and concise answers to user questions.
If you're unsure about something, say so rather than making up information.
Use markdown formatting for better readability when appropriate."""
            
            # Combine system prompt and query into single text
            combined_prompt = f"{system_prompt}\n\nQuestion: {query}"
            
            # Generate response using client - pass content as plain string
            response = self.client.models.generate_content(
                model=self.chat_model,
                contents=combined_prompt,
            )
            answer = response.text
            
            logger.info(f"✅ Generated direct LLM response ({len(answer)} chars)")
            
            return {
                "answer": answer,
                "context_used": 0,
                "query": query,
                "model": self.chat_model,
                "chunks_retrieved": 0,
                "chunks_with_context": 0,
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"❌ Error generating direct answer: {e}")
            raise
    
    async def answer_question(
        self,
        query: str,
        session_id: str
    ) -> Dict:
        """
        Complete RAG pipeline: retrieve -> expand -> generate answer
        
        Args:
            query: User question
            session_id: Session identifier
            
        Returns:
            Answer with metadata
        """
        try:
            logger.info(f"🚀 RAG Pipeline: Answering '{query}'")
            
            # Step 1: Retrieve relevant chunks
            chunks = await self.retrieve_relevant_chunks(query, session_id)
            
            if not chunks:
                logger.warning("⚠️  No relevant chunks found")
                return {
                    "answer": "The requested information was not found in the uploaded document.",
                    "context_used": 0,
                    "query": query,
                    "status": "no_context"
                }
            
            # Step 2: Expand context
            expanded_chunks = await self.expand_context(chunks, session_id)
            
            # Step 3: Generate answer
            result = await self.generate_answer(query, expanded_chunks)
            
            # Add retrieval metadata
            result["chunks_retrieved"] = len(chunks)
            result["chunks_with_context"] = len(expanded_chunks)
            result["status"] = result.get("status", "success")
            
            logger.info(f"✅ RAG Pipeline complete: {len(chunks)} chunks -> {len(expanded_chunks)} with context")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ RAG Pipeline error: {e}")
            raise


# Singleton instance
_rag_service = None


def get_rag_service() -> RAGService:
    """
    Get or create RAGService instance
    """
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
