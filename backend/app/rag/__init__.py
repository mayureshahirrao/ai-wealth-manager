"""
app/rag/__init__.py — Public API for the RAG module.
"""

from app.rag.retriever import retrieve, format_context_for_prompt, get_rag_context
from app.rag.embedder import index_knowledge_docs

__all__ = [
    "retrieve",
    "format_context_for_prompt",
    "get_rag_context",
    "index_knowledge_docs",
]
