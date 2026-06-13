"""
GuitarMind — build_knowledge.py
Reads the .txt files in data/, splits them into chunks, creates embeddings,
and stores everything in a local ChromaDB vector database.

Run ONCE (and again whenever you add/change data files):
    python src/build_knowledge.py
"""

import pathlib
import chromadb
from chromadb.utils import embedding_functions

# --- Locate folders relative to this file, so it works from anywhere ---
SRC_DIR = pathlib.Path(__file__).resolve().parent
PROJECT_DIR = SRC_DIR.parent
DATA_DIR = PROJECT_DIR / "data"
DB_DIR = PROJECT_DIR / "chroma_db"


def chunk_text(text: str, max_chars: int = 500) -> list[str]:
    """Split text into chunks, breaking on blank lines (paragraphs).
    Paragraphs longer than max_chars are split further."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks = []
    for para in paragraphs:
        if len(para) <= max_chars:
            chunks.append(para)
        else:
            # split a long paragraph into sentence-ish pieces
            words = para.split()
            current = ""
            for word in words:
                if len(current) + len(word) + 1 > max_chars:
                    chunks.append(current.strip())
                    current = word
                else:
                    current += " " + word
            if current.strip():
                chunks.append(current.strip())
    return chunks


def main():
    if not DATA_DIR.exists():
        raise SystemExit(f"ERROR: data folder not found at {DATA_DIR}")

    txt_files = sorted(DATA_DIR.glob("*.txt"))
    if not txt_files:
        raise SystemExit(f"ERROR: no .txt files found in {DATA_DIR}")

    print(f"Found {len(txt_files)} data file(s): {[f.name for f in txt_files]}")

    # Build all chunks with metadata about which file they came from.
    all_chunks = []
    all_ids = []
    all_metadata = []
    for txt_file in txt_files:
        text = txt_file.read_text(encoding="utf-8")
        chunks = chunk_text(text)
        for i, chunk in enumerate(chunks):
            all_chunks.append(chunk)
            all_ids.append(f"{txt_file.stem}_{i}")
            all_metadata.append({"source": txt_file.name})
        print(f"  {txt_file.name}: {len(chunks)} chunk(s)")

    print(f"\nTotal chunks: {len(all_chunks)}")
    print("Creating embeddings (first run downloads a small model, please wait)...")

    # Local embedding model (free, runs on your machine, no API calls).
    embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )

    # Create / reset the database.
    client = chromadb.PersistentClient(path=str(DB_DIR))
    # Delete old collection if it exists, so re-running is clean.
    try:
        client.delete_collection("music_theory")
    except Exception:
        pass
    collection = client.create_collection(
        name="music_theory", embedding_function=embed_fn
    )

    collection.add(documents=all_chunks, ids=all_ids, metadatas=all_metadata)

    print(f"\nDone. Knowledge base built at: {DB_DIR}")
    print(f"Stored {collection.count()} chunks. GuitarMind can now retrieve theory.")


if __name__ == "__main__":
    main()
    