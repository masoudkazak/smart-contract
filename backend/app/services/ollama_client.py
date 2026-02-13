from typing import Any, AsyncGenerator, Dict, List
import asyncio
import httpx
from loguru import logger

from ..config import get_settings

settings = get_settings()

_OLLAMA_SEMAPHORE = asyncio.Semaphore(1)

ALLOWED_MODELS = {
    settings.OLLAMA_MODEL_NAME,
}


class OllamaClient:
    def __init__(self) -> None:
        self._base_url = settings.ollama_base_url
        self._client: httpx.AsyncClient | None = None

    async def _ensure_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                timeout=httpx.Timeout(
                    connect=5.0,
                    read=120.0,
                    write=10.0,
                    pool=5.0,
                ),
                limits=httpx.Limits(
                    max_connections=5,
                    max_keepalive_connections=2,
                ),
            )
        return self._client

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def list_models(self) -> List[Dict[str, Any]]:
        client = await self._ensure_client()
        try:
            resp = await client.get("/api/tags", timeout=10.0)
            resp.raise_for_status()
            data = resp.json()

            return [
                {
                    "id": m.get("name"),
                    "object": "model",
                }
                for m in data.get("models", [])
            ]
        except Exception as e:
            logger.error(f"Ollama list_models failed: {e}")
            return []

    async def chat_stream(
        self,
        messages: List[Dict[str, Any]],
        model: str,
    ) -> AsyncGenerator[str, None]:
        if model not in ALLOWED_MODELS:
            logger.warning(f"Model '{model}' not allowed, fallback applied")
            model = settings.OLLAMA_MODEL_NAME

        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": True,
        }

        client = await self._ensure_client()

        async with _OLLAMA_SEMAPHORE:
            try:
                async with client.stream(
                    "POST",
                    "/api/chat",
                    json=payload,
                ) as resp:
                    resp.raise_for_status()

                    async for line in resp.aiter_lines():
                        if line and line.strip():
                            yield line

            except httpx.HTTPError as e:
                logger.error(f"Ollama streaming HTTP error: {e}")
                raise
            except Exception as e:
                logger.exception("Unexpected Ollama streaming error")
                raise


ollama_client = OllamaClient()
