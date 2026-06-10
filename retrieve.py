"""
retrieve.py - Milestone 4 (part 2): semantic search over the vector store.

Provides retrieve(query, k=5), which embeds the query with the same model used in
embed.py and returns the top-k most similar chunks with their source info and cosine
distance. Run this file directly to test retrieval on 3 of your evaluation questions
BEFORE wiring in any LLM (most RAG failures are retrieval failures).

  python retrieve.py
"""

import chromadb
from sentence_transformers import SentenceTransformer

MODEL_NAME = "all-MiniLM-L6-v2"
DB_DIR = "chroma_db"
COLLECTION = "unofficial_guide"

# loaded once and reused (so we don't reload the model on every query)
_model = None
_collection = None


def _load():
    global _model, _collection
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
        _collection = chromadb.PersistentClient(path=DB_DIR).get_collection(COLLECTION)
    return _model, _collection


def retrieve(query, k=5):
    """Return the top-k chunks for a query as a list of dicts."""
    model, collection = _load()
    query_embedding = model.encode([query]).tolist()
    res = collection.query(query_embeddings=query_embedding, n_results=k)
    results = []
    for doc, meta, dist in zip(
        res["documents"][0], res["metadatas"][0], res["distances"][0]
    ):
        results.append({
            "text": doc,
            "film": meta.get("film", ""),
            "source": meta.get("source", ""),        # publisher, e.g. "Collider"
            "title": meta.get("title", ""),          # list title
            "source_file": meta.get("source_file", ""),
            "genre": meta.get("genre", ""),
            "url": meta.get("url", ""),
            "distance": round(dist, 3),
        })
    return results


# 3 of the 5 evaluation questions from planning.md, used to sanity-check retrieval
TEST_QUERIES = [
    "An underrated sci-fi film that flopped at the box office but became a cult favorite",
    "A Korean revenge film that turns the revenge genre inside out",
    "An underrated horror film praised for atmosphere and dread rather than jump scares",
]


def _test():
    for q in TEST_QUERIES:
        print("\n" + "=" * 80)
        print("QUERY:", q)
        print("=" * 80)
        for i, r in enumerate(retrieve(q, k=5), 1):
            flag = "  <-- weak match (>0.5)" if r["distance"] > 0.5 else ""
            print(f"\n{i}. [{r['film']}]  distance={r['distance']}  "
                  f"({r['source_file']}, {r['genre']}){flag}")
            print("   " + r["text"][:200].replace("\n", " ") + "...")


if __name__ == "__main__":
    _test()