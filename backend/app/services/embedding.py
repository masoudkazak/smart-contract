from __future__ import annotations
import os
import io
from typing import List, Tuple
from fastapi import HTTPException, UploadFile, Depends
from loguru import logger
import asyncio
from functools import lru_cache
from sentence_transformers import SentenceTransformer
from app.config import get_settings
from app.models import DocumentChunk
from app.db import get_session
from sqlalchemy.ext.asyncio import AsyncSession

try:
    from pypdf import PdfReader
except Exception:  # noqa: BLE001
    PdfReader = None

try:
    import docx
except Exception:  # noqa: BLE001
    docx = None

settings = get_settings()


async def extract_text(file: UploadFile) -> List[Tuple[int, str]]:
    content = await file.read()
    await file.seek(0)

    filename = file.filename.lower()
    if filename.endswith(".pdf"):
        if PdfReader is None:
            raise HTTPException(status_code=500, detail="PDF support not available.")
        reader = PdfReader(io.BytesIO(content))
        paragraphs: List[Tuple[int, str]] = []
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""
            for para in page_text.split("\n\n"):
                para = para.strip()
                if para:
                    paragraphs.append((i + 1, para))
        return paragraphs

    if filename.endswith(".docx"):
        if docx is None:
            raise HTTPException(status_code=500, detail="DOCX support not available.")
        document = docx.Document(io.BytesIO(content))
        paragraphs: List[Tuple[int, str]] = [(1, p.text.strip()) for p in document.paragraphs if p.text.strip()]
        return paragraphs

    raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported.")


def simple_paragraph_chunking_with_page(
    paragraphs: List[Tuple[int, str]],
    *,
    max_chars: int = 1200,
    overlap_chars: int = 200,
) -> List[Tuple[int, str, int, str]]:
    chunks = []
    buffer = ""
    idx = 0
    current_page = 0
    current_section = ""

    for page_number, para in paragraphs:
        if para.isupper() and len(para.split()) < 10:
            current_section = para

        if not buffer:
            buffer = para
            current_page = page_number
        elif len(buffer) + 2 + len(para) <= max_chars:
            buffer = buffer + "\n\n" + para
        else:
            if buffer:
                chunks.append((idx, buffer, current_page, current_section))
                idx += 1
            if len(para) > max_chars:
                start = 0
                while start < len(para):
                    end = min(start + max_chars, len(para))
                    part = para[start:end]
                    chunks.append((idx, part, page_number, current_section))
                    idx += 1
                    start = max(0, end - overlap_chars)
                buffer = ""
            else:
                buffer = para
                current_page = page_number

    if buffer:
        chunks.append((idx, buffer, current_page, current_section))

    return chunks


async def embed_texts(texts: List[str]) -> List[List[float]]:
    @lru_cache(maxsize=1)
    def _get_st_model() -> SentenceTransformer:
        model_path = os.getenv("EMBEDDING_MODEL_PATH")
        if not model_path:
            raise RuntimeError("EMBEDDING_MODEL_PATH not set")
        logger.info(f"Loading sentence-transformer model for embeddings: {model_path}")
        return SentenceTransformer(model_path, device="cpu")

    loop = asyncio.get_running_loop()
    model = _get_st_model()

    vectors = await loop.run_in_executor(
        None,
        lambda: model.encode(texts, convert_to_numpy=True, normalize_embeddings=True),
    )

    result: List[List[float]] = []
    for vec in vectors:
        arr = vec.tolist()
        if len(arr) < 384:
            arr += [0.0] * (384 - len(arr))
        else:
            arr = arr[:384]
        result.append(arr)
    return result


async def process_and_store_document_chunks(
    file: UploadFile | bytes,
    document_id: str,
    db: AsyncSession,
    file_type: str,
):
    if isinstance(file, bytes):
        file_io = io.BytesIO(file)
        
        class SimpleFile:
            filename = f"document.{file_type}"
            
            async def read(self):
                file_io.seek(0)
                return file_io.read()
            
            async def seek(self, position: int):
                file_io.seek(position)
        
        file = SimpleFile()

    paragraphs = await extract_text(file)
    chunks = simple_paragraph_chunking_with_page(paragraphs)
    embeddings = await embed_texts([c[1] for c in chunks])

    for (idx, content, page_number, section), emb in zip(chunks, embeddings):
        chunk = DocumentChunk(
            document_id=document_id,
            chunk_index=idx,
            content=content,
            embedding=emb,
            page_number=page_number,
            section=section
        )
        db.add(chunk)

    await db.commit()
