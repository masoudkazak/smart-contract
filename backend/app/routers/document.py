import uuid
import magic
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db import get_session
from app.models import Document
from app.schemas import DocumentResponse
from app.config import get_settings
from datetime import datetime, timezone

settings = get_settings()
router = APIRouter(prefix="/documents", tags=["Documents"])

ALLOWED_MIME_TYPES = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
}

UPLOAD_DIR = settings.upload_doc_dir

@router.post(
    "/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_session),
):
    file_bytes = await file.read()

    mime = magic.from_buffer(file_bytes, mime=True)
    if mime not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Only PDF or DOCX files are allowed",
        )

    file_type = ALLOWED_MIME_TYPES[mime]

    document_id = uuid.uuid4()
    filename = f"{document_id}.{file_type}"
    file_path = UPLOAD_DIR / filename

    with open(file_path, "wb") as f:
        f.write(file_bytes)

    document = Document(
        id=document_id,
        filename=str(file_path),
        original_filename=file.filename,
        file_type=file_type,
        status="uploaded",
        meta_data=None,
        uploaded_at=datetime.now(timezone.utc),
    )

    db.add(document)
    await db.commit()
    await db.refresh(document)

    return document
