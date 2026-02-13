from pydantic import BaseModel, Field
from uuid import UUID

class MessageCreate(BaseModel):
    document_id: UUID | None = None
    conversation_id: UUID | None = None
    question: str = Field(..., min_length=1)


class MessageResponse(BaseModel):
    conversation_id: UUID
    answer: str
    intent: str | None = None
    confidence: float | None = None
