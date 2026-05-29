"""
chroma_client.py — Singleton ChromaDB client.

All RAG operations (indexing, retrieval) go through this client.
ChromaDB runs as a Docker service on port 8001.

Dependencies: config.py (Tier 2)
Consumed by: document_loader, embedder, retriever
"""

from functools import lru_cache
import chromadb
from chromadb.config import Settings as ChromaSettings

from skills.backend.core.config import get_settings
from skills.backend.core.logging_config import get_logger

logger = get_logger(__name__)


class ChromaClientWrapper:
    """
    Wrapper around the ChromaDB HttpClient.

    Usage:
        chroma = get_chroma_client()
        collection = chroma.get_or_create_collection()
        collection.add(documents=[...], ids=[...])
    """

    def __init__(self):
        settings = get_settings()
        self._client = chromadb.HttpClient(
            host=settings.CHROMA_HOST,
            port=settings.CHROMA_PORT,
            settings=ChromaSettings(allow_reset=True, anonymized_telemetry=False),
        )
        self._collection_name = settings.CHROMA_COLLECTION_NAME
        logger.info(
            "chroma_client_initialized",
            host=settings.CHROMA_HOST,
            port=settings.CHROMA_PORT,
            collection=self._collection_name,
        )

    def get_or_create_collection(self) -> chromadb.Collection:
        """
        Get existing collection or create it if it doesn't exist.
        Uses cosine similarity for financial document retrieval.
        """
        collection = self._client.get_or_create_collection(
            name=self._collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        logger.debug("collection_accessed", name=self._collection_name, count=collection.count())
        return collection

    def get_collection(self) -> chromadb.Collection:
        """Get existing collection (raises if doesn't exist)."""
        return self._client.get_collection(name=self._collection_name)

    def reset_collection(self) -> None:
        """Delete and recreate the collection (for re-indexing)."""
        try:
            self._client.delete_collection(self._collection_name)
        except Exception:
            pass
        self.get_or_create_collection()
        logger.info("collection_reset", name=self._collection_name)

    def health_check(self) -> bool:
        """Verify ChromaDB is accessible."""
        try:
            self._client.heartbeat()
            return True
        except Exception as exc:
            logger.error("chroma_health_check_failed", error=str(exc))
            return False


@lru_cache()
def get_chroma_client() -> ChromaClientWrapper:
    """
    Returns singleton ChromaDB client.

    Usage:
        from skills.backend.rag.chroma_client import get_chroma_client
        chroma = get_chroma_client()
        collection = chroma.get_or_create_collection()
    """
    return ChromaClientWrapper()
