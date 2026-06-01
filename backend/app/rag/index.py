"""
index.py — CLI entrypoint to index knowledge docs into ChromaDB.

Run from the backend directory:
    python -m app.rag.index

Safe to run repeatedly — clears and re-indexes every time.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.rag.embedder import index_knowledge_docs

if __name__ == "__main__":
    print("Indexing knowledge docs into ChromaDB...")
    total = index_knowledge_docs()
    print(f"Done. {total} chunks indexed.")
