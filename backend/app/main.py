from fastapi import FastAPI

from .config import get_settings
from contextlib import asynccontextmanager
from .services.ollama_client import ollama_client
from .logging_config import setup_logging 
from loguru import logger

settings = get_settings()
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Backend starting...")
    yield
    
    # Shutdown
    logger.info("Backend shutting down...")
    await ollama_client.close()
    logger.info("OllamaClient closed")


app = FastAPI(
    title="Smart Backend",
    debug=False,
    lifespan=lifespan
)


@app.get("/health", tags=["health"])
async def health_check() -> dict:
    return {"status": "ok"}
