from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime

class MessageCreate(BaseModel):
    document_id: UUID | None = None
    conversation_id: UUID | None = None
    question: str = Field(..., min_length=1)


class DocumentResponse(BaseModel):
    id: UUID
    filename: str
    original_filename: str
    file_type: str
    status: str
    uploaded_at: datetime
    meta_data: str | None = None

