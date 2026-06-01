"""
embedder.py — Loads knowledge docs, chunks them, and indexes into ChromaDB.

Run once (or whenever docs change) via:
    python -m app.rag.embedder

Design:
- Splits each .txt doc into overlapping chunks (~500 tokens, 100 overlap)
- Embeds with sentence-transformers (all-MiniLM-L6-v2, runs locally)
- Stores in ChromaDB collection with doc metadata (source, section)
- Idempotent: clears collection before re-indexing

Dependencies: chromadb, sentence-transformers, config.py (Tier 2)
"""

import os
import re
import sys
from pathlib import Path
from typing import Iterator

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from app.core.config import get_settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)

KNOWLEDGE_DOCS_DIR = Path(__file__).parent / "knowledge_docs"
CHUNK_SIZE = 500        # characters per chunk (≈125 tokens)
CHUNK_OVERLAP = 100     # character overlap between chunks

# Metadata keys stored alongside each chunk
METADATA_FIELDS = ("source", "section", "chunk_index")


def _get_chroma_client() -> chromadb.HttpClient:
    """Return ChromaDB HTTP client connected to Docker container."""
    settings = get_settings()
    return chromadb.HttpClient(
        host=settings.CHROMA_HOST,
        port=settings.CHROMA_PORT,
    )


def _get_collection(client: chromadb.HttpClient) -> chromadb.Collection:
    """Get or create the knowledge collection."""
    settings = get_settings()
    ef = SentenceTransformerEmbeddingFunction(
        model_name=settings.CHROMA_EMBEDDING_MODEL,
    )
    return client.get_or_create_collection(
        name=settings.CHROMA_COLLECTION_NAME,
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"},
    )


def _detect_section(line: str) -> str | None:
    """Detect if a line is a section header (all caps, ===, or ===)."""
    stripped = line.strip()
    if re.match(r"^={4,}", stripped):
        return None  # separator line
    if re.match(r"^[A-Z][A-Z\s\-–()]+$", stripped) and len(stripped) > 5:
        return stripped
    return None


def _chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """
    Split text into overlapping chunks at paragraph/sentence boundaries.

    Tries to break at paragraph boundaries (double newline) first,
    then at sentence boundaries (. ? !), finally hard-splits at chunk_size.
    """
    chunks: list[str] = []
    text = text.strip()
    start = 0
    length = len(text)

    while start < length:
        end = min(start + chunk_size, length)

        if end < length:
            # Try to break at paragraph boundary
            para_break = text.rfind("\n\n", start, end)
            if para_break > start + chunk_size // 2:
                end = para_break
            else:
                # Try sentence boundary
                for delimiter in (". ", "? ", "! ", "\n"):
                    sent_break = text.rfind(delimiter, start + chunk_size // 2, end)
                    if sent_break > start:
                        end = sent_break + len(delimiter)
                        break

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        # Move forward with overlap
        start = end - overlap if end < length else length

    return chunks


def _load_doc(filepath: Path) -> Iterator[tuple[str, str, int]]:
    """
    Load a .txt knowledge doc and yield (chunk_text, section, chunk_index).

    Tracks the current section heading so each chunk is labelled with
    its section (e.g., "CAPITAL GAINS TAX — BUDGET 2024").
    """
    content = filepath.read_text(encoding="utf-8")

    # Extract global metadata from header lines
    lines = content.splitlines()
    current_section = "General"
    body_lines: list[str] = []

    for line in lines:
        section = _detect_section(line)
        if section:
            current_section = section
        body_lines.append(line)

    # Chunk the full document
    chunks = _chunk_text(content)

    # Re-detect section per chunk (scan first line of each chunk)
    chunk_index = 0
    for chunk in chunks:
        # Find which section this chunk likely belongs to
        first_meaningful = next(
            (l.strip() for l in chunk.splitlines() if l.strip() and not l.startswith("=")),
            ""
        )
        section_match = _detect_section(first_meaningful)
        section = section_match if section_match else current_section

        yield chunk, section, chunk_index
        chunk_index += 1


def index_knowledge_docs() -> int:
    """
    Index all .txt files in the knowledge_docs directory into ChromaDB.

    Returns:
        Total number of chunks indexed.
    """
    client = _get_chroma_client()
    collection = _get_collection(client)

    # Clear existing data for idempotent re-indexing
    existing = collection.count()
    if existing > 0:
        logger.info("clearing_existing_chunks", count=existing)
        collection.delete(where={"source": {"$ne": "__none__"}})

    all_docs: list[str] = []
    all_ids: list[str] = []
    all_metadata: list[dict] = []

    txt_files = sorted(KNOWLEDGE_DOCS_DIR.glob("*.txt"))
    if not txt_files:
        logger.warning("no_knowledge_docs_found", dir=str(KNOWLEDGE_DOCS_DIR))
        return 0

    for filepath in txt_files:
        source = filepath.stem  # e.g., "indian_tax_guide"
        logger.info("indexing_document", source=source)

        for chunk_text, section, chunk_idx in _load_doc(filepath):
            chunk_id = f"{source}_{chunk_idx:04d}"
            all_docs.append(chunk_text)
            all_ids.append(chunk_id)
            all_metadata.append({
                "source": source,
                "section": section[:100],   # ChromaDB metadata value limit
                "chunk_index": chunk_idx,
            })

    # Batch upsert (ChromaDB handles embedding internally)
    if all_docs:
        # ChromaDB max batch size is 5461
        batch_size = 500
        for i in range(0, len(all_docs), batch_size):
            collection.upsert(
                documents=all_docs[i:i+batch_size],
                ids=all_ids[i:i+batch_size],
                metadatas=all_metadata[i:i+batch_size],
            )
            logger.debug("batch_upserted", batch=i // batch_size + 1, count=len(all_docs[i:i+batch_size]))

    total = len(all_docs)
    logger.info("indexing_complete", total_chunks=total, documents=len(txt_files))
    print(f"✅ Indexed {total} chunks from {len(txt_files)} documents into ChromaDB.")
    return total


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    index_knowledge_docs()
