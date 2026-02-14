from fastapi import FastAPI

from .config import get_settings
from app.routers import chat, document
from .logging_config import setup_logging 

settings = get_settings()
setup_logging()


app = FastAPI(
    title="Smart Backend",
    debug=False,
    root_path="/api"
)
app.include_router(chat.router)
app.include_router(document.router)

@app.get("/health", tags=["health"])
async def health_check() -> dict:
    return {"status": "ok"}
