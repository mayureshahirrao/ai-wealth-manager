"""
embedder.py — Generate embeddings and index documents into ChromaDB.

Uses sentence-transformers (all-MiniLM-L6-v2) for embedding — runs locally,
no additional API cost, fast for demo purposes.

Dependencies: chroma_client.py, document_loader.py (Tier 3)
Consumed by: Startup indexing script, retriever.py
"""

from typing import Optional
from sentence_transformers import SentenceTransformer

from skills.backend.rag.chroma_client import get_chroma_client, ChromaClientWrapper
from skills.backend.rag.document_loader import DocumentChunk
from skills.backend.core.config import get_settings
from skills.backend.core.logging_config import get_logger

logger = get_logger(__name__)
settings = get_settings()

# Module-level model instance (loaded once)
_embedding_model: Optional[SentenceTransformer] = None


def get_embedding_model() -> SentenceTransformer:
    """Lazy-load the embedding model (only when first needed)."""
    global _embedding_model
    if _embedding_model is None:
        logger.info("loading_embedding_model", model=settings.CHROMA_EMBEDDING_MODEL)
        _embedding_model = SentenceTransformer(settings.CHROMA_EMBEDDING_MODEL)
        logger.info("embedding_model_loaded")
    return _embedding_model


def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Generate embeddings for a list of text strings.

    Args:
        texts: List of strings to embed

    Returns:
        List of embedding vectors (each a list of floats)
    """
    model = get_embedding_model()
    embeddings = model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
    return embeddings.tolist()


def index_chunks(
    chunks: list[DocumentChunk],
    chroma: Optional[ChromaClientWrapper] = None,
    batch_size: int = 50,
) -> int:
    """
    Embed and store chunks in ChromaDB.

    Args:
        chunks: List of DocumentChunk objects from document_loader
        chroma: ChromaDB client (uses singleton if not provided)
        batch_size: Number of chunks to embed per batch

    Returns:
        Number of chunks successfully indexed
    """
    if not chunks:
        logger.warning("no_chunks_to_index")
        return 0

    chroma = chroma or get_chroma_client()
    collection = chroma.get_or_create_collection()

    indexed_count = 0
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i: i + batch_size]

        texts = [chunk.text for chunk in batch]
        ids = [chunk.chunk_id for chunk in batch]
        metadatas = [
            {
                "source_doc": chunk.source_doc,
                "section_title": chunk.section_title or "",
                "chunk_index": chunk.chunk_index,
                "total_chunks": chunk.total_chunks,
                **(chunk.metadata or {}),
            }
            for chunk in batch
        ]

        try:
            embeddings = embed_texts(texts)
            collection.upsert(
                ids=ids,
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas,
            )
            indexed_count += len(batch)
            logger.info(
                "chunks_indexed",
                batch=i // batch_size + 1,
                count=len(batch),
                total_so_far=indexed_count,
            )
        except Exception as exc:
            logger.error("chunk_indexing_failed", batch_start=i, error=str(exc))
            continue

    logger.info("indexing_complete", total_chunks=indexed_count)
    return indexed_count


async def index_all_documents_on_startup() -> int:
    """
    Index all knowledge documents at application startup.
    Skips re-indexing if collection already has documents.

    Returns:
        Number of chunks indexed (0 if already indexed)
    """
    from skills.backend.rag.document_loader import load_all_documents

    chroma = get_chroma_client()

    if not chroma.health_check():
        logger.error("chroma_not_available_skipping_indexing")
        return 0

    collection = chroma.get_or_create_collection()

    # Skip if already indexed
    if collection.count() > 0:
        logger.info("knowledge_base_already_indexed", chunks=collection.count())
        return 0

    chunks = load_all_documents()
    if not chunks:
        logger.warning("no_documents_to_index")
        return 0

    return index_chunks(chunks, chroma)
