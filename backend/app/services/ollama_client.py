from __future__ import annotations
from typing import Any, AsyncGenerator, Dict
import httpx
from loguru import logger
from app.config import get_settings


settings = get_settings()


def _get_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=settings.ollama_base_url,
        timeout=60.0,
    )


async def chat_completion(
    prompt: str,
    system_prompt: str,
    temperature: int = 0.7,
    top_p: int = 0.8,
    top_k: int = 20,
    num_predict: int = 300,
) -> AsyncGenerator[str, None]:
    payload: Dict[str, Any] = {
        "model": settings.OLLAMA_MODEL_NAME,
        "messages": [],
        "temperature": temperature,
        "top_p": top_p,
        "top_k": top_k,
        "num_predict": num_predict,
        "stream": True,
    }

    payload["messages"].append(
        {"role": "system", "content": system_prompt}
    )

    payload["messages"].append(
        {"role": "user", "content": prompt}
    )

    client = _get_client()

    async def _stream_generator() -> AsyncGenerator[str, None]:
        try:
            async with client.stream(
                "POST",
                "/api/chat",
                json=payload,
            ) as resp:
                resp.raise_for_status()

                async for line in resp.aiter_lines():
                    if not line:
                        continue

                    try:
                        data = httpx.Response(200, text=line).json()
                    except Exception:
                        continue

                    message = data.get("message", {})
                    content = message.get("content")

                    if content:
                        yield content

        except Exception as exc:  # noqa: BLE001
            logger.error(f"Ollama streaming error: {exc}")
            raise
        finally:
            await client.aclose()

    return _stream_generator()
