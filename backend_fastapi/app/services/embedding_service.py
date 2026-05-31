"""
Gemini Embeddings Service
Handles embedding generation using Google Gemini API
"""

import logging
import warnings
from typing import List, Optional
from google import genai
from app.core.config import settings

# Suppress deprecation warning for google.generativeai
warnings.filterwarnings("ignore", category=FutureWarning, module="google.generativeai")

logger = logging.getLogger(__name__)


class GeminiEmbeddingService:
    """
    Generates embeddings using Gemini text-embedding-004 model
    """
    
    def __init__(self):
        """
        Initialize Gemini embeddings service
        """
        try:
            # Configure Gemini API
            self.client = genai.Client(
            api_key=settings.GEMINI_API_KEY
        )
            self.model = settings.GEMINI_EMBEDDING_MODEL
            self.embedding_dimension = settings.EMBEDDING_DIMENSION
            
            logger.info(f"🔌 Initialized Gemini Embeddings Service")
            logger.info(f"   Model: {self.model}")
            logger.info(f"   Dimension: {self.embedding_dimension}")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Gemini service: {e}")
            raise
    
    async def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        try:
            # Use the correct API for google-generativeai
            response = self.client.models.embed_content(
                model=self.model,
                contents=text,
            )
            
            embedding = response.embeddings[0].values
            
            # Verify dimension
            if len(embedding) != self.embedding_dimension:
                logger.warning(
                    f"⚠️  Embedding dimension mismatch. "
                    f"Expected {self.embedding_dimension}, got {len(embedding)}"
                )
            
            return embedding
            
        except Exception as e:
            logger.error(f"❌ Error generating embedding: {e}")
            raise
    
    async def embed_texts(self, texts: List[str], batch_size: int = 100) -> List[List[float]]:
        """
        Generate embeddings for multiple texts
        
        Args:
            texts: List of texts to embed
            batch_size: Batch size for processing
            
        Returns:
            List of embeddings
        """
        try:
            logger.info(f"🔄 Generating embeddings for {len(texts)} texts...")
            
            embeddings = []
            
            # Process in batches to avoid API rate limits
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                
                for text in batch:
                    embedding = await self.embed_text(text)
                    embeddings.append(embedding)
                
                # Log progress
                progress = min(i + batch_size, len(texts))
                logger.info(f"   Generated {progress}/{len(texts)} embeddings")
            
            logger.info(f"✅ Generated {len(embeddings)} embeddings")
            return embeddings
            
        except Exception as e:
            logger.error(f"❌ Error generating embeddings: {e}")
            raise
    
    async def embed_query(self, query: str) -> List[float]:
        """
        Generate embedding for a query
        
        Args:
            query: Query text
            
        Returns:
            Query embedding
        """
        try:
            response = self.client.models.embed_content(
                model=self.model,
                contents=query,
            )
            
            embedding = response.embeddings[0].values
            return embedding
            
        except Exception as e:
            logger.error(f"❌ Error generating query embedding: {e}")
            raise


# Singleton instance
_embedding_service = None


def get_embedding_service() -> GeminiEmbeddingService:
    """
    Get or create GeminiEmbeddingService instance
    """
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = GeminiEmbeddingService()
    return _embedding_service
