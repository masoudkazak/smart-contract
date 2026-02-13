from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_session
from app.models import Conversation, Message
from app.schemas import MessageCreate, MessageResponse
from app.services.ollama_client import chat_completion

router = APIRouter()


@router.post("/chat", response_model=MessageResponse)
async def chat(payload: MessageCreate, session: AsyncSession = Depends(get_session)) -> MessageResponse:
    conv: Conversation | None = None
    if payload.conversation_id:
        conv = await session.get(Conversation, payload.conversation_id)
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found.")
    else:
        conv = Conversation(document_id=None)
        session.add(conv)
        await session.flush()

    user_message = Message(
        conversation_id=conv.id,
        role="user",
        content=payload.question,
    )
    session.add(user_message)

    system_prompt = (
        "You are a helpful assistant. "
        "Always answer in the same language as the user."
    )
    final_prompt = f"User question:\n{payload.question}\n\nProvide a concise, well-structured answer."

    answer = await chat_completion(final_prompt, system_prompt=system_prompt)
    if isinstance(answer, str):
        final_answer = answer
    else:
        parts = []
        async for part in answer:
            parts.append(part)
        final_answer = "".join(parts)

    assistant_message = Message(
        conversation_id=conv.id,
        role="assistant",
        content=final_answer,
    )
    session.add(assistant_message)

    await session.commit()
    await session.refresh(conv)

    return MessageResponse(
        conversation_id=conv.id,
        answer=final_answer,
        intent=None,
        confidence=None,
    )
