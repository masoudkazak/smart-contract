from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import AsyncGenerator

from app.db import get_session
from app.models import Conversation, Message
from app.schemas import MessageCreate
from app.services.ollama_client import chat_completion

router = APIRouter()


@router.post("/chat/stream")
async def chat_stream(
    payload: MessageCreate,
    session: AsyncSession = Depends(get_session),
):
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
    await session.commit()

    system_prompt = (
        "You are a helpful assistant. "
        "Always answer in the same language as the user."
    )
    final_prompt = f"User question:\n{payload.question}\n\nProvide a concise, well-structured answer."

    ollama_stream = await chat_completion(
        final_prompt,
        system_prompt=system_prompt,
    )

    async def event_generator() -> AsyncGenerator[str, None]:
        parts: list[str] = []

        async for chunk in ollama_stream:
            parts.append(chunk)
            yield chunk

        final_answer = "".join(parts)

        assistant_message = Message(
            conversation_id=conv.id,
            role="assistant",
            content=final_answer,
        )
        session.add(assistant_message)
        await session.commit()

    return StreamingResponse(
        event_generator(),
        media_type="text/plain",
        headers={
            "X-Conversation-Id": str(conv.id),
        },
    )
