from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import List

class MessageCreate(BaseModel):
    document_filename: str | None = None
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


class ConversationListSchema(BaseModel):
    id: UUID
    document_id: UUID | None = None
    started_at: datetime
    title: str

class MessageSchema(BaseModel):
    id: UUID
    role: str
    content: str
    created_at: datetime

    class Config:
        orm_mode = True


class ConversationSchema(BaseModel):
    id: UUID
    document_id: UUID | None = None
    started_at: datetime
    messages: List[MessageSchema] = []

    class Config:
        orm_mode = True
