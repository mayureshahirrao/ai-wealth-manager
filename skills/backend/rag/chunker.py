"""
chunker.py — Text chunking strategies for financial documents.

Different document types need different chunking strategies:
- Regulatory docs (SEBI rules): section-level chunks (preserve legal context)
- Tax guides: Q&A pairs (high precision retrieval)
- Planning guides: paragraph-level (conceptual continuity)

Dependencies: None (Tier 3)
Consumed by: document_loader.py, indexer
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ChunkStrategy(str, Enum):
    FIXED_SIZE = "fixed_size"           # Fixed token/character windows
    PARAGRAPH = "paragraph"             # Split on double newlines
    SECTION = "section"                 # Split on markdown headers (##, ###)
    QA_PAIR = "qa_pair"                 # Extract Q&A pairs from structured docs
    SENTENCE = "sentence"               # Split on sentence boundaries


@dataclass
class DocumentChunk:
    """A single chunk of a document ready for embedding."""
    text: str
    chunk_id: str
    source_doc: str
    section_title: Optional[str] = None
    chunk_index: int = 0
    total_chunks: int = 0
    metadata: dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


def chunk_by_section(
    text: str,
    doc_name: str,
    min_chunk_size: int = 200,
    max_chunk_size: int = 1500,
) -> list[DocumentChunk]:
    """
    Split document by markdown headers (## Section Name).
    Best for regulatory documents and structured guides.

    Args:
        text: Full document text
        doc_name: Source document name (for chunk ID and metadata)
        min_chunk_size: Merge sections smaller than this
        max_chunk_size: Split sections larger than this

    Returns:
        List of DocumentChunk objects
    """
    sections = re.split(r"\n(?=#{1,3} )", text)
    chunks = []
    current_title = "Introduction"

    for section in sections:
        lines = section.strip().split("\n")
        title_line = lines[0] if lines else ""

        # Extract section title from markdown header
        if title_line.startswith("#"):
            current_title = re.sub(r"^#+\s*", "", title_line)
            content = "\n".join(lines[1:]).strip()
        else:
            content = section.strip()

        if not content:
            continue

        # If section is too large, split into paragraphs
        if len(content) > max_chunk_size:
            sub_chunks = chunk_by_paragraph(content, doc_name, min_chunk_size, max_chunk_size)
            for sc in sub_chunks:
                sc.section_title = current_title
            chunks.extend(sub_chunks)
        elif len(content) >= min_chunk_size:
            chunks.append(DocumentChunk(
                text=f"{current_title}\n\n{content}",
                chunk_id=f"{doc_name}_sec_{len(chunks)}",
                source_doc=doc_name,
                section_title=current_title,
                chunk_index=len(chunks),
            ))

    # Set total_chunks
    for i, chunk in enumerate(chunks):
        chunk.chunk_index = i
        chunk.total_chunks = len(chunks)

    return chunks


def chunk_by_paragraph(
    text: str,
    doc_name: str,
    min_chunk_size: int = 150,
    max_chunk_size: int = 1000,
) -> list[DocumentChunk]:
    """
    Split document by paragraphs (double newlines).
    Best for planning guides and general explanations.
    """
    paragraphs = [p.strip() for p in re.split(r"\n\n+", text) if p.strip()]

    chunks = []
    current_text = ""

    for para in paragraphs:
        if len(current_text) + len(para) < max_chunk_size:
            current_text = (current_text + "\n\n" + para).strip()
        else:
            if len(current_text) >= min_chunk_size:
                chunks.append(DocumentChunk(
                    text=current_text,
                    chunk_id=f"{doc_name}_para_{len(chunks)}",
                    source_doc=doc_name,
                    chunk_index=len(chunks),
                ))
            current_text = para

    if current_text and len(current_text) >= min_chunk_size:
        chunks.append(DocumentChunk(
            text=current_text,
            chunk_id=f"{doc_name}_para_{len(chunks)}",
            source_doc=doc_name,
            chunk_index=len(chunks),
        ))

    for i, chunk in enumerate(chunks):
        chunk.chunk_index = i
        chunk.total_chunks = len(chunks)

    return chunks


def chunk_qa_pairs(text: str, doc_name: str) -> list[DocumentChunk]:
    """
    Extract Q&A pairs from structured FAQ-format documents.
    Best for tax guides where precision retrieval is critical.

    Expected format:
        Q: What is the LTCG tax rate on equity?
        A: The LTCG tax rate...

    Args:
        text: Document text with Q&A format
        doc_name: Source document name
    """
    qa_pattern = re.compile(r"Q:\s*(.+?)\nA:\s*(.+?)(?=\nQ:|$)", re.DOTALL)
    pairs = qa_pattern.findall(text)

    chunks = []
    for i, (question, answer) in enumerate(pairs):
        qa_text = f"Q: {question.strip()}\nA: {answer.strip()}"
        chunks.append(DocumentChunk(
            text=qa_text,
            chunk_id=f"{doc_name}_qa_{i}",
            source_doc=doc_name,
            section_title=question.strip()[:80],
            chunk_index=i,
            total_chunks=len(pairs),
        ))

    return chunks


def get_strategy_for_document(doc_name: str) -> ChunkStrategy:
    """
    Recommend chunking strategy based on document name.

    Args:
        doc_name: Filename without extension

    Returns:
        Recommended ChunkStrategy
    """
    qa_docs = ["indian_tax_guide", "indian_capital_gains"]
    section_docs = ["sebi_regulations", "nps_epf_ppf_guide"]

    if any(doc_name.startswith(d) for d in qa_docs):
        return ChunkStrategy.QA_PAIR
    if any(doc_name.startswith(d) for d in section_docs):
        return ChunkStrategy.SECTION
    return ChunkStrategy.PARAGRAPH
