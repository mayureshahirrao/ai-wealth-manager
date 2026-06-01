"""
retriever.py — Semantic retrieval from ChromaDB knowledge base.

At query time, retrieves the top-k most relevant chunks for a user's query
and formats them for injection into Claude's system prompt.

Design:
- Uses the same embedding model as the embedder (all-MiniLM-L6-v2)
- Cosine similarity search in ChromaDB
- Filters by source document if query_type is specific (e.g., TAX → tax guide)
- Returns formatted context string ready for system prompt injection

Dependencies: chromadb, sentence-transformers, config.py (Tier 3)
"""

from functools import lru_cache
from typing import Optional

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

from app.core.config import get_settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)

# Number of chunks to retrieve per query
DEFAULT_TOP_K = 3
MAX_CONTEXT_CHARS = 3000     # Approx 750 tokens — keeps system prompt concise

# Map query types to relevant source documents (for filtered retrieval)
QUERY_TYPE_TO_SOURCES: dict[str, list[str]] = {
    "tax": ["indian_tax_guide", "sebi_ia_regulations"],
    "retirement": ["retirement_planning_guide", "indian_tax_guide"],
    "portfolio": ["mutual_funds_guide", "goal_based_investing"],
    "investment_advice": ["mutual_funds_guide", "goal_based_investing", "sebi_ia_regulations"],
    "market": ["mutual_funds_guide"],
    "behavioral": ["goal_based_investing", "retirement_planning_guide"],
    "general": [],   # Empty = search all sources
}


@lru_cache(maxsize=1)
def _get_collection() -> chromadb.Collection:
    """
    Lazy-initialise ChromaDB collection with embedding function.
    Cached for the lifetime of the process.
    """
    settings = get_settings()
    client = chromadb.HttpClient(
        host=settings.CHROMA_HOST,
        port=settings.CHROMA_PORT,
    )
    ef = SentenceTransformerEmbeddingFunction(
        model_name=settings.CHROMA_EMBEDDING_MODEL,
    )
    collection = client.get_or_create_collection(
        name=settings.CHROMA_COLLECTION_NAME,
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"},
    )
    return collection


def retrieve(
    query: str,
    query_type: str = "general",
    top_k: int = DEFAULT_TOP_K,
) -> list[dict]:
    """
    Retrieve the top-k most relevant knowledge chunks for a query.

    Args:
        query: User's natural language question
        query_type: One of the QueryType values (tax, retirement, portfolio, etc.)
        top_k: Number of chunks to return

    Returns:
        List of dicts with keys: text, source, section, score
    """
    try:
        collection = _get_collection()

        # Check if collection has any documents
        if collection.count() == 0:
            logger.warning("chroma_collection_empty", query=query[:50])
            return []

        # Build source filter for focused retrieval
        sources = QUERY_TYPE_TO_SOURCES.get(query_type, [])
        where_filter: Optional[dict] = None
        if sources:
            if len(sources) == 1:
                where_filter = {"source": sources[0]}
            else:
                where_filter = {"source": {"$in": sources}}

        # Query ChromaDB
        query_params: dict = {
            "query_texts": [query],
            "n_results": min(top_k, collection.count()),
            "include": ["documents", "metadatas", "distances"],
        }
        if where_filter:
            query_params["where"] = where_filter

        results = collection.query(**query_params)

        chunks = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            # ChromaDB cosine distance: 0 = identical, 2 = opposite
            # Convert to similarity score 0–1
            similarity = 1 - (dist / 2)
            chunks.append({
                "text": doc,
                "source": meta.get("source", "unknown"),
                "section": meta.get("section", ""),
                "score": round(similarity, 3),
            })

        logger.debug(
            "rag_retrieval",
            query=query[:60],
            query_type=query_type,
            chunks_found=len(chunks),
            top_score=chunks[0]["score"] if chunks else 0,
        )

        return chunks

    except Exception as exc:
        logger.error("rag_retrieval_failed", error=str(exc), query=query[:60])
        return []


def format_context_for_prompt(
    chunks: list[dict],
    min_score: float = 0.3,
) -> tuple[str, int]:
    """
    Format retrieved chunks into a context string for Claude's system prompt.

    Filters chunks below min_score threshold (low relevance).
    Truncates at MAX_CONTEXT_CHARS to avoid bloating the prompt.

    Args:
        chunks: Retrieved chunks from retrieve()
        min_score: Minimum similarity score to include (0.0–1.0)

    Returns:
        Tuple of (context_string, num_sources_used)
    """
    relevant = [c for c in chunks if c["score"] >= min_score]

    if not relevant:
        return "", 0

    parts: list[str] = ["### Relevant Knowledge Base Context\n"]
    total_chars = 0
    sources_used = 0

    for chunk in relevant:
        source_label = chunk["source"].replace("_", " ").title()
        section = chunk["section"]
        header = f"\n**{source_label}** — {section}:\n" if section else f"\n**{source_label}**:\n"
        body = chunk["text"].strip()

        addition = header + body + "\n"
        if total_chars + len(addition) > MAX_CONTEXT_CHARS:
            break

        parts.append(addition)
        total_chars += len(addition)
        sources_used += 1

    if sources_used == 0:
        return "", 0

    parts.append(
        "\n*Use the above context to ground your response in accurate Indian financial knowledge.*\n"
    )

    return "".join(parts), sources_used


async def get_rag_context(
    user_query: str,
    query_type: str = "general",
    top_k: int = DEFAULT_TOP_K,
    min_score: float = 0.3,
) -> tuple[str, int]:
    """
    Convenience async wrapper: retrieve + format in one call.

    Args:
        user_query: User's question
        query_type: Detected query type (from compliance_injector.classify_query)
        top_k: Number of chunks to retrieve
        min_score: Minimum relevance score

    Returns:
        Tuple of (formatted_context_string, num_sources_found)
        Empty string if no relevant context found.
    """
    chunks = retrieve(user_query, query_type, top_k)
    context, num_sources = format_context_for_prompt(chunks, min_score)
    return context, num_sources
