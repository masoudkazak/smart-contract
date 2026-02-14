from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import AsyncGenerator, List

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db import get_session
from app.models import Conversation, Message
from app.schemas import MessageCreate, ConversationSchema, ConversationListSchema
from app.services.ollama_client import chat_completion

router = APIRouter()

MAX_TITLE_LENGTH = 50

@router.get("/conversations", response_model=List[ConversationListSchema])
async def list_conversations(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Conversation))
    conversations = result.scalars().all()
    return conversations


@router.get("/conversations/{conversation_id}", response_model=ConversationSchema)
async def get_conversation(conversation_id: str, session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(Conversation.id == conversation_id)
    )
    conv = result.scalars().first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return conv


@router.post("/chat/stream")
async def chat_stream(
    payload: MessageCreate,
    session: AsyncSession = Depends(get_session),
):
    is_new_conversation = False

    if payload.conversation_id:
        conv = await session.get(Conversation, payload.conversation_id)
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found.")
    else:
        conv = Conversation(document_id=None)
        session.add(conv)
        await session.flush()
        is_new_conversation = True

    user_message = Message(
        conversation_id=conv.id,
        role="user",
        content=payload.question,
    )
    session.add(user_message)

    if is_new_conversation:
        if len(payload.question) > MAX_TITLE_LENGTH:
            conv.title = payload.question[:MAX_TITLE_LENGTH].rstrip() + "..."
        else:
            conv.title = payload.question

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
