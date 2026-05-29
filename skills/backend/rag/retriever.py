"""
retriever.py — Hybrid retrieval from ChromaDB knowledge base.

Retrieves relevant financial knowledge chunks using:
1. Dense (semantic) retrieval via embeddings
2. Optional keyword filtering for precise financial terms

Dependencies: chroma_client.py, embedder.py, chunker.py (Tier 4)
Consumed by: QueryFinancialKnowledgeTool, base_agent.py
"""

from dataclasses import dataclass
from typing import Optional

from skills.backend.rag.chroma_client import get_chroma_client
from skills.backend.rag.embedder import embed_texts
from skills.backend.core.exceptions import RAGRetrievalError
from skills.backend.core.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class RetrievedChunk:
    """A retrieved chunk with relevance metadata."""
    text: str
    source_doc: str
    section_title: str
    distance: float           # Cosine distance (lower = more similar)
    relevance_score: float    # 1 - distance (higher = more relevant)
    chunk_id: str


def retrieve(
    query: str,
    n_results: int = 5,
    source_filter: Optional[str] = None,
    min_relevance: float = 0.3,
) -> list[RetrievedChunk]:
    """
    Retrieve relevant knowledge chunks for a query.

    Args:
        query: User's question or search query
        n_results: Maximum number of chunks to return
        source_filter: If set, only retrieve from this source document
        min_relevance: Minimum relevance score (0-1) to include

    Returns:
        List of RetrievedChunk objects sorted by relevance (highest first)

    Raises:
        RAGRetrievalError if ChromaDB query fails

    Example:
        chunks = retrieve("What is the LTCG tax rate on equity mutual funds?", n_results=3)
        context = "\\n\\n".join(c.text for c in chunks)
    """
    chroma = get_chroma_client()

    if not chroma.health_check():
        raise RAGRetrievalError(query=query, reason="ChromaDB is not accessible")

    try:
        collection = chroma.get_or_create_collection()
        count = collection.count()

        if count == 0:
            logger.warning("knowledge_base_empty", query=query[:50])
            return []

        # Generate query embedding
        query_embedding = embed_texts([query])[0]

        # Build query kwargs
        query_kwargs = {
            "query_embeddings": [query_embedding],
            "n_results": min(n_results, count),
            "include": ["documents", "metadatas", "distances"],
        }

        if source_filter:
            query_kwargs["where"] = {"source_doc": source_filter}

        results = collection.query(**query_kwargs)

        # Parse results
        chunks = []
        if results["documents"] and results["documents"][0]:
            for i, (doc, metadata, distance) in enumerate(zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            )):
                relevance = round(1.0 - distance, 3)
                if relevance >= min_relevance:
                    chunks.append(RetrievedChunk(
                        text=doc,
                        source_doc=metadata.get("source_doc", "unknown"),
                        section_title=metadata.get("section_title", ""),
                        distance=distance,
                        relevance_score=relevance,
                        chunk_id=results["ids"][0][i],
                    ))

        logger.info(
            "retrieval_complete",
            query_preview=query[:50],
            results_found=len(chunks),
            top_score=chunks[0].relevance_score if chunks else 0,
        )
        return sorted(chunks, key=lambda c: c.relevance_score, reverse=True)

    except RAGRetrievalError:
        raise
    except Exception as exc:
        raise RAGRetrievalError(query=query, reason=str(exc)) from exc


def format_context_for_llm(
    chunks: list[RetrievedChunk],
    max_chars: int = 3000,
) -> str:
    """
    Format retrieved chunks as context text for Claude's system prompt.

    Args:
        chunks: Retrieved chunks from retrieve()
        max_chars: Maximum total characters to include

    Returns:
        Formatted context string ready to inject into system prompt
    """
    if not chunks:
        return ""

    context_parts = []
    total_chars = 0

    for chunk in chunks:
        header = f"[Source: {chunk.source_doc} — {chunk.section_title}]"
        entry = f"{header}\n{chunk.text}"

        if total_chars + len(entry) > max_chars:
            break

        context_parts.append(entry)
        total_chars += len(entry)

    return "\n\n---\n\n".join(context_parts)


def retrieve_and_format(query: str, n_results: int = 4) -> dict:
    """
    Retrieve and format context in one call — used by QueryFinancialKnowledgeTool.

    Returns:
        Dict with keys: context_text, sources_found, top_relevance
    """
    chunks = retrieve(query, n_results=n_results)
    context = format_context_for_llm(chunks)

    return {
        "context_text": context,
        "sources_found": len(chunks),
        "top_relevance": chunks[0].relevance_score if chunks else 0.0,
        "sources": [
            {"doc": c.source_doc, "section": c.section_title, "relevance": c.relevance_score}
            for c in chunks
        ],
    }
