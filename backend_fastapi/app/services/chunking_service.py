"""
Chunking Service using LangChain
Handles text splitting with RecursiveCharacterTextSplitter
"""

from langchain_text_splitters import RecursiveCharacterTextSplitter
import logging
from typing import List, Dict
from app.core.config import settings

logger = logging.getLogger(__name__)


class ChunkingService:
    """
    Handles document chunking using LangChain
    """
    
    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        """
        Initialize chunking service
        
        Args:
            chunk_size: Size of chunks in characters
            chunk_overlap: Overlap between chunks
        """
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP
        
        # Initialize RecursiveCharacterTextSplitter
        # Splits on these separators in order: \n\n (paragraphs), \n (lines), . (sentences), " " (words)
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=[
                "\n\n",     # Paragraph breaks
                "\n",       # Line breaks
                ". ",       # Sentence breaks
                " ",        # Word boundaries
                ""          # Character level (last resort)
            ],
            length_function=len,
        )
        
        logger.info(
            f"📌 Initialized ChunkingService: "
            f"chunk_size={self.chunk_size}, "
            f"chunk_overlap={self.chunk_overlap}"
        )
    
    def split_text(self, text: str) -> List[str]:
        """
        Split text into chunks
        
        Args:
            text: Text to split
            
        Returns:
            List of text chunks
        """
        try:
            logger.info(f"✂️  Splitting text ({len(text)} chars) into chunks...")
            
            chunks = self.splitter.split_text(text)
            
            logger.info(
                f"✅ Split text into {len(chunks)} chunks. "
                f"Avg size: {len(text) // len(chunks) if chunks else 0} chars"
            )
            
            return chunks
            
        except Exception as e:
            logger.error(f"❌ Error splitting text: {e}")
            raise
    
    def create_chunks_with_metadata(
        self,
        text: str,
        document_id: str,
        session_id: str,
        page_number: int = None
    ) -> List[Dict]:
        """
        Split text and create chunks with metadata
        
        Args:
            text: Text to chunk
            document_id: Document identifier
            session_id: Session identifier
            page_number: Page number (optional)
            
        Returns:
            List of chunk dictionaries with metadata
        """
        try:
            logger.info(f"📦 Creating chunks with metadata for document {document_id}")
            
            # Split text into chunks
            text_chunks = self.split_text(text)
            
            # Create chunks with metadata
            chunks = []
            for index, chunk_text in enumerate(text_chunks):
                chunk = {
                    "chunkIndex": index,
                    "documentId": document_id,
                    "sessionId": session_id,
                    "text": chunk_text,
                    "pageNumber": page_number,
                    "size": len(chunk_text),
                    "tokenCount": len(chunk_text.split()),
                }
                chunks.append(chunk)
            
            logger.info(f"✅ Created {len(chunks)} chunks with metadata")
            return chunks
            
        except Exception as e:
            logger.error(f"❌ Error creating chunks with metadata: {e}")
            raise


# Singleton instance
_chunking_service = None


def get_chunking_service() -> ChunkingService:
    """
    Get or create ChunkingService instance
    """
    global _chunking_service
    if _chunking_service is None:
        _chunking_service = ChunkingService()
    return _chunking_service
