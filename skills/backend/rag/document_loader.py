"""
document_loader.py — Load financial knowledge documents from knowledge_docs/.

Reads all .md and .txt files from the knowledge_docs directory, applies the
appropriate chunking strategy per document, and prepares chunks for embedding.

Dependencies: chroma_client.py, chunker.py (Tier 3)
Consumed by: embedder.py (during indexing), startup script
"""

import os
from pathlib import Path

from skills.backend.rag.chunker import (
    DocumentChunk,
    chunk_by_section,
    chunk_by_paragraph,
    chunk_qa_pairs,
    get_strategy_for_document,
    ChunkStrategy,
)
from skills.backend.core.logging_config import get_logger

logger = get_logger(__name__)

KNOWLEDGE_DOCS_PATH = Path(__file__).parents[3] / "knowledge_docs"


def load_document(file_path: Path) -> str:
    """Read a document file and return its text content."""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def load_and_chunk_document(file_path: Path) -> list[DocumentChunk]:
    """
    Load a single document and chunk it using the appropriate strategy.

    Args:
        file_path: Path to the .md or .txt knowledge document

    Returns:
        List of DocumentChunk objects ready for embedding
    """
    doc_name = file_path.stem  # filename without extension
    text = load_document(file_path)
    strategy = get_strategy_for_document(doc_name)

    logger.info(
        "document_loading",
        doc=doc_name,
        strategy=strategy.value,
        size_chars=len(text),
    )

    if strategy == ChunkStrategy.QA_PAIR:
        chunks = chunk_qa_pairs(text, doc_name)
        # Fallback to paragraph if no Q&A pairs found
        if not chunks:
            chunks = chunk_by_paragraph(text, doc_name)
    elif strategy == ChunkStrategy.SECTION:
        chunks = chunk_by_section(text, doc_name)
    else:
        chunks = chunk_by_paragraph(text, doc_name)

    logger.info("document_chunked", doc=doc_name, chunks=len(chunks))
    return chunks


def load_all_documents(docs_path: Path = KNOWLEDGE_DOCS_PATH) -> list[DocumentChunk]:
    """
    Load and chunk all documents from the knowledge_docs directory.

    Args:
        docs_path: Path to directory containing knowledge documents

    Returns:
        All chunks from all documents, ready for batch embedding
    """
    if not docs_path.exists():
        logger.warning("knowledge_docs_not_found", path=str(docs_path))
        return []

    all_chunks = []
    doc_files = list(docs_path.glob("*.md")) + list(docs_path.glob("*.txt"))

    if not doc_files:
        logger.warning("no_knowledge_docs_found", path=str(docs_path))
        return []

    for file_path in sorted(doc_files):
        try:
            chunks = load_and_chunk_document(file_path)
            all_chunks.extend(chunks)
        except Exception as exc:
            logger.error("document_load_failed", doc=file_path.name, error=str(exc))
            continue

    logger.info("all_documents_loaded", total_chunks=len(all_chunks), docs=len(doc_files))
    return all_chunks
