"""
Document Upload API Routes
Handles document upload and processing
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from app.models.schemas import UploadResponse
from app.services.pdf_processor import get_pdf_processor
from app.services.chunking_service import get_chunking_service
from app.services.embedding_service import get_embedding_service
from app.services.vector_store import get_vector_store
from app.core.database import get_db
from app.core.config import settings
from datetime import datetime
import logging
import uuid
import os

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/document")
async def upload_document(
    session_id: str = Form(...),
    file: UploadFile = File(...)
) -> UploadResponse:
    """
    Upload and process a supported document
    
    Args:
        session_id: Session identifier
        file: PDF or DOCX file to upload
        
    Returns:
        UploadResponse with document metadata and processing results
    """
    try:
        logger.info(f"📤 Uploading document: {file.filename} (session: {session_id})")
        
        # Validate file
        lower_filename = file.filename.lower()
        if not lower_filename.endswith((".pdf", ".docx")):
            raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported")
        
        # Check file size
        file_content = await file.read()
        file_size_mb = len(file_content) / (1024 * 1024)
        
        if file_size_mb > settings.MAX_PDF_SIZE_MB:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size: {settings.MAX_PDF_SIZE_MB}MB"
            )
        
        # Validate session exists
        db = get_db()
        sessions_collection = db[settings.MONGODB_SESSIONS_COLLECTION]
        session = await sessions_collection.find_one({"_id": session_id})
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Generate document ID
        document_id = str(uuid.uuid4())
        
        # Step 1: Process document
        pdf_processor = get_pdf_processor()
        pdf_data = await pdf_processor.process_document(file_content, file.filename)
        
        page_count = pdf_data["metadata"].get("page_count", 0)
        file_type = pdf_data["metadata"].get("file_type", lower_filename.rsplit(".", 1)[-1])
        extracted_text = pdf_data["text"]
        if not extracted_text.strip():
            raise HTTPException(status_code=400, detail="Could not extract text from this document")
        
        logger.info(f"📄 Processed PDF: {page_count} pages, {len(extracted_text)} chars")
        
        # Step 2: Create chunks
        chunking_service = get_chunking_service()
        chunks = chunking_service.create_chunks_with_metadata(
            text=extracted_text,
            document_id=document_id,
            session_id=session_id,
            page_number=1
        )
        
        logger.info(f"✂️  Created {len(chunks)} chunks")
        
        # Step 3: Generate embeddings
        chunk_texts = [chunk["text"] for chunk in chunks]
        embedding_service = get_embedding_service()
        embeddings = await embedding_service.embed_texts(chunk_texts)
        
        logger.info(f"🔢 Generated {len(embeddings)} embeddings")
        
        # Step 4: Store chunks with embeddings
        vector_store = get_vector_store()
        await vector_store.add_chunks_with_embeddings(
            chunks=chunks,
            embeddings=embeddings,
            session_id=session_id
        )
        
        # Step 5: Store document metadata
        documents_collection = db[settings.MONGODB_DOCUMENTS_COLLECTION]
        document_record = {
            "_id": document_id,
            "sessionId": session_id,
            "filename": file.filename,
            "page_count": page_count,
            "file_type": file_type,
            "chunk_count": len(chunks),
            "size_bytes": len(file_content),
            "uploaded_at": datetime.utcnow(),
            "status": "processed",
        }
        
        await documents_collection.insert_one(document_record)
        
        # Update session
        await sessions_collection.update_one(
            {"_id": session_id},
            {
                "$set": {
                    "last_accessed": datetime.utcnow(),
                    "last_document_id": document_id
                },
                "$inc": {"document_count": 1}
            }
        )
        
        logger.info(f"✅ Document uploaded successfully (ID: {document_id})")
        
        return UploadResponse(
            session_id=session_id,
            document_id=document_id,
            filename=file.filename,
            page_count=page_count,
            chunks_created=len(chunks),
            status="success",
            message=f"Document processed: {len(chunks)} chunks created from {page_count} pages"
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Error uploading document: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing document: {str(e)}"
        )


@router.post("/summary")
async def generate_summary(document_id: str):
    """
    Generate a summary of the uploaded document
    
    Args:
        document_id: Document identifier
        
    Returns:
        Summary text
    """
    try:
        from app.services.rag_service import get_rag_service
        
        logger.info(f"📋 Generating summary for document: {document_id}")
        
        db = get_db()
        documents_collection = db[settings.MONGODB_DOCUMENTS_COLLECTION]
        chunks_collection = db[settings.MONGODB_CHUNKS_COLLECTION]
        
        # Get document
        document = await documents_collection.find_one({"_id": document_id})
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        session_id = document["sessionId"]
        
        # Get all chunks for this document
        chunks = await chunks_collection.find(
            {"documentId": document_id, "sessionId": session_id}
        ).sort("chunkIndex", 1).to_list(length=None)
        
        if not chunks:
            raise HTTPException(status_code=404, detail="No content found for document")
        
        # Combine all text
        full_text = "\n\n".join([chunk.get("text", "") for chunk in chunks])
        
        # Generate summary
        rag_service = get_rag_service()
        
        summary_prompt = f"""Please provide a concise summary (2-3 paragraphs) of the following document:

{full_text[:3000]}..."""  # Limit to first 3000 chars for faster processing
        
        response = await rag_service.generate_direct_answer(summary_prompt)
        
        logger.info(f"✅ Summary generated for document: {document_id}")
        
        return {
            "document_id": document_id,
            "summary": response["answer"],
            "status": "success"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error generating summary: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating summary: {str(e)}")


@router.post("/key-points")
async def generate_key_points(document_id: str):
    """
    Extract key points from the uploaded document
    
    Args:
        document_id: Document identifier
        
    Returns:
        Key points list
    """
    try:
        from app.services.rag_service import get_rag_service
        
        logger.info(f"🔑 Extracting key points from document: {document_id}")
        
        db = get_db()
        documents_collection = db[settings.MONGODB_DOCUMENTS_COLLECTION]
        chunks_collection = db[settings.MONGODB_CHUNKS_COLLECTION]
        
        # Get document
        document = await documents_collection.find_one({"_id": document_id})
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        session_id = document["sessionId"]
        
        # Get all chunks for this document
        chunks = await chunks_collection.find(
            {"documentId": document_id, "sessionId": session_id}
        ).sort("chunkIndex", 1).to_list(length=None)
        
        if not chunks:
            raise HTTPException(status_code=404, detail="No content found for document")
        
        # Combine all text
        full_text = "\n\n".join([chunk.get("text", "") for chunk in chunks])
        
        # Generate key points
        rag_service = get_rag_service()
        
        keypoints_prompt = f"""Extract the top 5-7 key points from the following document. Format as a numbered list:

{full_text[:3000]}..."""  # Limit to first 3000 chars for faster processing
        
        response = await rag_service.generate_direct_answer(keypoints_prompt)
        
        logger.info(f"✅ Key points extracted from document: {document_id}")
        
        return {
            "document_id": document_id,
            "keyPoints": response["answer"],
            "status": "success"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error extracting key points: {e}")
        raise HTTPException(status_code=500, detail=f"Error extracting key points: {str(e)}")


@router.post("/important-questions")
async def generate_important_questions(document_id: str):
    """
    Generate important questions based on the uploaded document
    
    Args:
        document_id: Document identifier
        
    Returns:
        Questions list
    """
    try:
        from app.services.rag_service import get_rag_service
        
        logger.info(f"❓ Generating important questions for document: {document_id}")
        
        db = get_db()
        documents_collection = db[settings.MONGODB_DOCUMENTS_COLLECTION]
        chunks_collection = db[settings.MONGODB_CHUNKS_COLLECTION]
        
        # Get document
        document = await documents_collection.find_one({"_id": document_id})
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        session_id = document["sessionId"]
        
        # Get all chunks for this document
        chunks = await chunks_collection.find(
            {"documentId": document_id, "sessionId": session_id}
        ).sort("chunkIndex", 1).to_list(length=None)
        
        if not chunks:
            raise HTTPException(status_code=404, detail="No content found for document")
        
        # Combine all text
        full_text = "\n\n".join([chunk.get("text", "") for chunk in chunks])
        
        # Generate questions
        rag_service = get_rag_service()
        
        questions_prompt = f"""Based on the following document, generate 5 important questions that help understand the key concepts:

{full_text[:3000]}..."""  # Limit to first 3000 chars for faster processing
        
        response = await rag_service.generate_direct_answer(questions_prompt)
        
        logger.info(f"✅ Important questions generated for document: {document_id}")
        
        return {
            "document_id": document_id,
            "questions": response["answer"],
            "status": "success"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error generating questions: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating questions: {str(e)}")
