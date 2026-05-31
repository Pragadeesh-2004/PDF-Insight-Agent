"""
Pydantic models for request/response validation
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime


# Chat Models
class ChatMessage(BaseModel):
    """Single chat message"""
    role: str = Field(..., description="Message role (user/assistant)")
    content: str = Field(..., description="Message content")
    timestamp: Optional[datetime] = Field(None, description="Message timestamp")


class ChatRequest(BaseModel):
    """Chat API request"""
    session_id: str = Field(..., description="Session identifier")
    message: str = Field(..., description="User message/question")
    agent_type: str = Field("PDF_INSIGHT_AGENT", description="Agent type")


class ChatResponse(BaseModel):
    """Chat API response"""
    session_id: str
    message: str
    answer: str
    source: str = Field("DOCUMENT_RAG", description="Answer source")
    context_used: int = Field(0, description="Number of context chunks used")
    chunks_retrieved: Optional[int] = None
    chunks_with_context: Optional[int] = None
    model: str = "gemini-3.1-flash-lite"
    timestamp: datetime


# Document Upload Models
class UploadResponse(BaseModel):
    """Document upload response"""
    session_id: str
    document_id: str
    filename: str
    page_count: int
    chunks_created: int
    status: str = "success"
    message: str


# Session Models
class SessionInfo(BaseModel):
    """Session information"""
    session_id: str
    created_at: datetime
    last_accessed: datetime
    document_count: int
    message_count: int
    expires_at: datetime


class SessionResponse(BaseModel):
    """Session API response"""
    session_id: str
    status: str = "success"
    message: str


# Document Models
class DocumentMetadata(BaseModel):
    """Document metadata"""
    document_id: str
    filename: str
    page_count: int
    chunk_count: int
    uploaded_at: datetime
    size_bytes: int


class DocumentsResponse(BaseModel):
    """Documents listing response"""
    session_id: str
    documents: List[DocumentMetadata]
    total_count: int


# Chunk Models
class ChunkMetadata(BaseModel):
    """Chunk metadata"""
    chunk_index: int
    size: int
    has_embedding: bool = False
    similarity_score: Optional[float] = None


# Health Check Models
class HealthCheck(BaseModel):
    """Health check response"""
    status: str
    service: str
    version: str
    backend: str
    rag_engine: str
