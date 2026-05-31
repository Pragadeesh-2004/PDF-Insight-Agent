"""
MongoDB Atlas Vector Store Service
Handles storage and retrieval of chunks using MongoDB Atlas Vector Search
"""

import logging
from typing import List, Dict, Optional
from app.core.database import get_db
from app.core.config import settings

logger = logging.getLogger(__name__)


class MongoDBVectorStore:
    """
    Manages vector storage and retrieval using MongoDB Atlas Vector Search
    """
    
    def __init__(self):
        """
        Initialize MongoDB Vector Store
        """
        self.collection_name = settings.MONGODB_CHUNKS_COLLECTION
        logger.info(f"🔌 Initialized MongoDB Vector Store (collection: {self.collection_name})")
    
    async def store_chunks(self, chunks: List[Dict], session_id: str):
        """
        Store chunks in MongoDB with embeddings
        
        Args:
            chunks: List of chunk dictionaries
            session_id: Session identifier
        """
        try:
            logger.info(f"💾 Storing {len(chunks)} chunks in MongoDB...")
            
            db = get_db()
            collection = db[self.collection_name]
            
            # Add sessionId to each chunk and insert
            chunks_to_insert = []
            for chunk in chunks:
                chunk["sessionId"] = session_id
                chunks_to_insert.append(chunk)
            
            # Insert chunks
            result = await collection.insert_many(chunks_to_insert)
            
            logger.info(f"✅ Stored {len(result.inserted_ids)} chunks")
            return result.inserted_ids
            
        except Exception as e:
            logger.error(f"❌ Error storing chunks: {e}")
            raise
    
    async def add_chunks_with_embeddings(
        self,
        chunks: List[Dict],
        embeddings: List[List[float]],
        session_id: str
    ):
        """
        Add chunks with their embeddings to MongoDB
        
        Args:
            chunks: List of chunk dictionaries
            embeddings: List of embedding vectors
            session_id: Session identifier
        """
        try:
            logger.info(f"📦 Adding {len(chunks)} chunks with embeddings...")
            
            if len(chunks) != len(embeddings):
                raise ValueError(f"Chunk count ({len(chunks)}) != embedding count ({len(embeddings)})")
            
            db = get_db()
            collection = db[self.collection_name]
            
            # Combine chunks with embeddings
            chunks_with_embeddings = []
            for chunk, embedding in zip(chunks, embeddings):
                chunk["embedding"] = embedding
                chunk["sessionId"] = session_id
                chunks_with_embeddings.append(chunk)
            
            # Insert
            result = await collection.insert_many(chunks_with_embeddings)
            
            logger.info(f"✅ Added {len(result.inserted_ids)} chunks with embeddings")
            return result.inserted_ids
            
        except Exception as e:
            logger.error(f"❌ Error adding chunks with embeddings: {e}")
            raise
    
    async def search(
        self,
        query_embedding: List[float],
        session_id: str,
        top_k: int = settings.TOP_K_RETRIEVAL,
        similarity_threshold: float = settings.SIMILARITY_THRESHOLD
    ) -> List[Dict]:
        """
        Search for similar chunks using vector search
        
        Args:
            query_embedding: Query embedding vector
            session_id: Session identifier (filter results to this session)
            top_k: Number of results to return
            similarity_threshold: Minimum similarity score
            
        Returns:
            List of similar chunks
        """
        try:
            logger.info(f"🔍 Searching for {top_k} similar chunks...")
            
            db = get_db()
            collection = db[self.collection_name]
            
            # MongoDB Atlas Vector Search query
            pipeline = [
            {
                "$vectorSearch": {
                    "index": "vector_index",
                    "path": "embedding",
                    "queryVector": query_embedding,
                    "numCandidates": max(top_k * 10, 100),
                    "limit": top_k,
                }
            },
            {
                "$match": {
                    "sessionId": session_id
                }
            },
            {
                "$project": {
                    "_id": 1,
                    "chunkText": 1,
                    "documentId": 1,
                    "chunkIndex": 1,
                    "sessionId": 1,
                    "score": {
                        "$meta": "vectorSearchScore"
                    }
                }
            }
        ]
            
            results = await collection.aggregate(pipeline).to_list(length=None)
            
            logger.info(f"✅ Found {len(results)} similar chunks")
            return results
            
        except Exception as e:
            logger.error(f"❌ Error searching chunks: {e}")
            raise
    
    async def get_chunk_with_context(
        self,
        chunk_id: str,
        session_id: str
    ) -> Optional[Dict]:
        """
        Get a chunk with its surrounding context (previous and next chunks)
        
        Args:
            chunk_id: Chunk identifier
            session_id: Session identifier
            
        Returns:
            Chunk with context or None
        """
        try:
            db = get_db()
            collection = db[self.collection_name]
            
            # Get the chunk
            chunk = await collection.find_one(
                {"_id": chunk_id, "sessionId": session_id}
            )
            
            if  chunk is None:
                return None
            
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
            
            return {
                "main_chunk": chunk,
                "context_chunks": context_chunks
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting chunk with context: {e}")
            raise
    
    async def delete_session_chunks(self, session_id: str):
        """
        Delete all chunks for a session
        
        Args:
            session_id: Session identifier
        """
        try:
            logger.info(f"🗑️  Deleting chunks for session {session_id}...")
            
            db = get_db()
            collection = db[self.collection_name]
            
            result = await collection.delete_many({"sessionId": session_id})
            
            logger.info(f"✅ Deleted {result.deleted_count} chunks")
            return result.deleted_count
            
        except Exception as e:
            logger.error(f"❌ Error deleting session chunks: {e}")
            raise


# Singleton instance
_vector_store = None


def get_vector_store() -> MongoDBVectorStore:
    """
    Get or create MongoDBVectorStore instance
    """
    global _vector_store
    if _vector_store is None:
        _vector_store = MongoDBVectorStore()
    return _vector_store
