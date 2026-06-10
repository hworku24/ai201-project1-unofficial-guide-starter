"""
embed.py - Milestone 4 (part 1): embed chunks and load them into ChromaDB.

Reads chunks.json (produced by pipeline.py), embeds each chunk's text with the
all-MiniLM-L6-v2 sentence-transformer, and stores the vectors in a local ChromaDB
collection along with the source metadata you'll need for citations later.

Run locally (downloads the model the first time, ~80MB):
  pip install sentence-transformers chromadb
  python embed.py

The vector store is written to ./chroma_db so retrieve.py can reuse it.
"""

import json
import chromadb
from sentence_transformers import SentenceTransformer

MODEL_NAME = "all-MiniLM-L6-v2"   # local, free, 384-dim (matches planning.md)
CHUNKS_JSON = "chunks.json"
DB_DIR = "chroma_db"              # ChromaDB persists here
COLLECTION = "unofficial_guide"

# metadata fields we copy from each chunk into the vector store
META_FIELDS = ("source_file", "title", "source", "genre", "url", "film", "part")


def main():
    with open(CHUNKS_JSON, encoding="utf-8") as f:
        chunks = json.load(f)
    print(f"Loaded {len(chunks)} chunks from {CHUNKS_JSON}")

    # 1. embed every chunk's text
    model = SentenceTransformer(MODEL_NAME)
    texts = [c["text"] for c in chunks]
    embeddings = model.encode(texts, show_progress_bar=True).tolist()

    # 2. (re)create the ChromaDB collection.
    #    hnsw:space = cosine so distances run 0 (identical) .. 2 (opposite),
    #    which is what the "distance below 0.5" guidance in the brief assumes.
    client = chromadb.PersistentClient(path=DB_DIR)
    try:
        client.delete_collection(COLLECTION)   # start clean on every run
    except Exception:
        pass
    collection = client.create_collection(
        name=COLLECTION, metadata={"hnsw:space": "cosine"}
    )

    # 3. add vectors + documents + metadata, keyed by each chunk's unique id
    collection.add(
        ids=[c["id"] for c in chunks],
        documents=texts,
        embeddings=embeddings,
        metadatas=[{k: c.get(k, "") for k in META_FIELDS} for c in chunks],
    )

    print(f"Embedded {len(chunks)} chunks into collection "
          f"'{COLLECTION}' at ./{DB_DIR}/")


if __name__ == "__main__":
    main()