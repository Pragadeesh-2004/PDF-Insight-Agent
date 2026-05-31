"""
PDF Insight Agent - FastAPI Backend
Production-grade RAG system using LangChain, MongoDB Atlas Vector Search, and Gemini APIs
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from dotenv import load_dotenv
import os

from app.core.config import settings
from app.core.database import connect_to_mongo, close_mongo_connection
from app.api.routes import chat, upload, session, documents

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    """
    # Startup
    logger.info("🚀 Starting PDF Insight Agent Backend")
    logger.info(f"📦 LangChain version: {__import__('langchain').__version__}")
    
    # Connect to MongoDB
    try:
        await connect_to_mongo()
    except Exception as e:
        logger.error(f"⚠️  MongoDB connection warning: {e}")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down PDF Insight Agent Backend")
    await close_mongo_connection()


# Create FastAPI app
app = FastAPI(
    title="PDF Insight Agent API",
    description="Production-grade RAG system with semantic search and Gemini integration",
    version="2.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001", "http://localhost:5173", "*","https://pdf-insight-agent.onrender.com"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(upload.router, prefix="/api/upload", tags=["upload"])
app.include_router(session.router, prefix="/api/session", tags=["session"])
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])


# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {
        "status": "healthy",
        "service": "PDF Insight Agent API",
        "version": "2.0.0",
        "backend": "FastAPI",
        "rag_engine": "LangChain + MongoDB Vector Search + Gemini"
    }


# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint with API information
    """
    return {
        "name": "PDF Insight Agent API",
        "version": "2.0.0",
        "description": "Production-grade RAG system",
        "endpoints": {
            "health": "/health",
            "chat": "/api/chat/message",
            "upload": "/api/upload/document",
            "session": "/api/session/{session_id}",
            "documents": "/api/documents/{session_id}"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
