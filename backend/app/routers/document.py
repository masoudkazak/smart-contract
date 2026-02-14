import uuid
import magic

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import desc, select

from app.db import get_session
from app.models import Document
from app.schemas import DocumentResponse
from app.config import get_settings
from app.services.embedding import process_and_store_document_chunks

from datetime import datetime, timezone
from typing import List
from loguru import logger

settings = get_settings()
router = APIRouter(prefix="/documents", tags=["Documents"])

ALLOWED_MIME_TYPES = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
}

UPLOAD_DIR = settings.upload_doc_dir


@router.get(
    "/",
    response_model=List[DocumentResponse],
    status_code=status.HTTP_200_OK,
)
async def list_documents(
    db: AsyncSession = Depends(get_session),
):
    result = await db.execute(
        select(Document).order_by(desc(Document.uploaded_at))
    )
    documents = result.scalars().all()
    return documents


@router.post(
    "/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(file: UploadFile = File(...), db: AsyncSession = Depends(get_session)):
    file_bytes = await file.read()
    mime = magic.from_buffer(file_bytes, mime=True)
    if mime not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=400, detail="Only PDF or DOCX files are allowed")
    file_type = ALLOWED_MIME_TYPES[mime]

    document_id = uuid.uuid4()
    filename = f"{document_id}.{file_type}"
    file_path = UPLOAD_DIR / filename

    try:
        logger.info(f"Uploading file to {file_path}...")
        with open(file_path, "wb") as f:
            f.write(file_bytes)
        logger.info("File uploaded")

        document = Document(
            id=document_id,
            filename=str(file_path),
            original_filename=file.filename,
            file_type=file_type,
            status="processing",
            meta_data=None,
            uploaded_at=datetime.now(timezone.utc),
        )
        db.add(document)
        await db.commit()
        await db.refresh(document)

        logger.info("Embedding document...")
        await process_and_store_document_chunks(file_bytes, str(document_id), db=db, file_type=file_type)

        document.status = "ready"
        await db.commit()
        await db.refresh(document)
        logger.info("Document embedded successfully")
        return document

    except Exception as exc:
        logger.exception(f"Error while uploading or processing document: {str(exc)}")
        await db.rollback()
        if "document" in locals():
            try:
                await db.delete(document)
                await db.commit()
            except Exception as e:
                logger.error(f"Error deleting document from DB: {e}")
        if file_path.exists():
            try:
                file_path.unlink()
            except Exception as e:
                logger.error(f"Error deleting file: {e}")
        raise HTTPException(status_code=500, detail=f"Document upload or processing failed: {str(exc)}")
