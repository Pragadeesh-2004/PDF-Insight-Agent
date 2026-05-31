"""
Documents API Routes
Handles document listing and retrieval
"""

from fastapi import APIRouter, HTTPException
from app.models.schemas import DocumentsResponse, DocumentMetadata
from app.core.database import get_db
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/{session_id}")
async def get_session_documents(session_id: str) -> DocumentsResponse:
    """
    Get all documents for a session
    
    Args:
        session_id: Session identifier
        
    Returns:
        DocumentsResponse with list of documents
    """
    try:
        logger.info(f"📚 Retrieving documents for session: {session_id}")
        
        db = get_db()
        
        # Validate session
        sessions_collection = db[settings.MONGODB_SESSIONS_COLLECTION]
        session = await sessions_collection.find_one({"_id": session_id})
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Get documents
        documents_collection = db[settings.MONGODB_DOCUMENTS_COLLECTION]
        documents = await documents_collection.find(
            {"sessionId": session_id}
        ).sort("uploaded_at", -1).to_list(length=None)
        
        # Build response
        doc_list = []
        for doc in documents:
            doc_list.append(
                DocumentMetadata(
                    document_id=doc["_id"],
                    filename=doc.get("filename", "Unknown"),
                    page_count=doc.get("page_count", 0),
                    chunk_count=doc.get("chunk_count", 0),
                    uploaded_at=doc.get("uploaded_at"),
                    size_bytes=doc.get("size_bytes", 0)
                )
            )
        
        logger.info(f"✅ Retrieved {len(doc_list)} documents")
        
        return DocumentsResponse(
            session_id=session_id,
            documents=doc_list,
            total_count=len(doc_list)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error retrieving documents: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving documents: {str(e)}")


@router.get("/{session_id}/{document_id}")
async def get_document_info(session_id: str, document_id: str) -> DocumentMetadata:
    """
    Get information about a specific document
    
    Args:
        session_id: Session identifier
        document_id: Document identifier
        
    Returns:
        DocumentMetadata with document details
    """
    try:
        logger.info(f"📄 Retrieving document: {document_id} (session: {session_id})")
        
        db = get_db()
        
        # Validate session
        sessions_collection = db[settings.MONGODB_SESSIONS_COLLECTION]
        session = await sessions_collection.find_one({"_id": session_id})
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Get document
        documents_collection = db[settings.MONGODB_DOCUMENTS_COLLECTION]
        document = await documents_collection.find_one(
            {
                "_id": document_id,
                "sessionId": session_id
            }
        )
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        logger.info(f"✅ Retrieved document info: {document_id}")
        
        return DocumentMetadata(
            document_id=document["_id"],
            filename=document.get("filename", "Unknown"),
            page_count=document.get("page_count", 0),
            chunk_count=document.get("chunk_count", 0),
            uploaded_at=document.get("uploaded_at"),
            size_bytes=document.get("size_bytes", 0)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error retrieving document: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving document: {str(e)}")


@router.delete("/{session_id}/{document_id}")
async def delete_document(session_id: str, document_id: str):
    """
    Delete a specific document and its chunks
    
    Args:
        session_id: Session identifier
        document_id: Document identifier
        
    Returns:
        Status response
    """
    try:
        logger.info(f"🗑️  Deleting document: {document_id} (session: {session_id})")
        
        db = get_db()
        
        # Validate session
        sessions_collection = db[settings.MONGODB_SESSIONS_COLLECTION]
        session = await sessions_collection.find_one({"_id": session_id})
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Delete document
        documents_collection = db[settings.MONGODB_DOCUMENTS_COLLECTION]
        doc = await documents_collection.find_one(
            {
                "_id": document_id,
                "sessionId": session_id
            }
        )
        
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        
        await documents_collection.delete_one(
            {
                "_id": document_id,
                "sessionId": session_id
            }
        )
        
        # Delete chunks
        chunks_collection = db[settings.MONGODB_CHUNKS_COLLECTION]
        await chunks_collection.delete_many(
            {
                "documentId": document_id,
                "sessionId": session_id
            }
        )
        
        # Update session
        await sessions_collection.update_one(
            {"_id": session_id},
            {"$inc": {"document_count": -1}}
        )
        
        logger.info(f"✅ Document deleted: {document_id}")
        
        return {
            "status": "success",
            "message": "Document deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting document: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}")
