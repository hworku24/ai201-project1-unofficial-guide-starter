"""
query.py - Milestone 5: grounded answer generation with source attribution.

ask(question) ties the whole RAG system together:
  1. retrieve the top-k chunks for the question (retrieve.py / ChromaDB)
  2. build a numbered context block from those chunks
  3. ask Groq's llama-3.3-70b-versatile to answer USING ONLY that context
  4. attach source attribution programmatically from the retrieved chunks

Grounding is enforced two ways: (a) a system prompt that tells the model to use only the
provided passages and to refuse when they're insufficient, and (b) the context is the only
material the model is given - it never sees the question without the retrieved passages.

Run locally:
  pip install groq python-dotenv
  # put GROQ_API_KEY=... in your .env  (copy .env.example to .env)
  python query.py
"""

import os
from dotenv import load_dotenv
from groq import Groq
from retrieve import retrieve

load_dotenv()
client = Groq(api_key=os.environ["GROQ_API_KEY"])
MODEL = "llama-3.3-70b-versatile"

REFUSAL = "I don't have enough information on that."

SYSTEM_PROMPT = (
    "You are The Unofficial Guide to underrated and hidden-gem films. "
    "Answer the user's question USING ONLY the numbered context passages provided. "
    "Follow these rules strictly:\n"
    "- Use only the information in the context passages. Do NOT use any outside knowledge "
    "about films, even if you are confident.\n"
    "- Do NOT add any details (plot, box office, budget, reception, awards, director) "
    "unless those exact details are written in the passages.\n"
    "- A passage that is only a film title with no description does NOT count as enough "
    "information. If all passages are just titles, use the refusal line.\n"
    f'- If the passages do not contain enough information to answer, reply exactly: "{REFUSAL}"\n'
    "- When you state a fact or recommend a film, name the film it comes from.\n"
    "- Be concise (a few sentences). Do not invent films, directors, or details."
)


def build_context(chunks):
    """Render retrieved chunks as a numbered, labeled context block."""
    blocks = []
    for i, c in enumerate(chunks, 1):
        blocks.append(
            f"[{i}] (film: {c['film']}; source: {c['source_file']})\n{c['text']}"
        )
    return "\n\n".join(blocks)


def ask(question, k=5):
    """Retrieve, generate a grounded answer, and return answer + sources + chunks."""
    chunks = retrieve(question, k=k)
    context = build_context(chunks)
    user_message = (
        f"Context passages:\n\n{context}\n\n"
        f"Question: {question}"
    )

    response = client.chat.completions.create(
        model=MODEL,
        temperature=0,                      # deterministic, less prone to embellishing
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
    )
    answer = response.choices[0].message.content.strip()

    # Source attribution, appended programmatically (not left to the LLM).
    # If the model refused, we don't claim any sources.
    sources = []
    if REFUSAL.lower() not in answer.lower():
        seen = set()
        for c in chunks:
            label = f"{c.get('film','')} ({c.get('source','')}) - {c.get('source_file','')}"
            if label not in seen:
                seen.add(label)
                sources.append(label)

    return {"answer": answer, "sources": sources, "chunks": chunks}


def _demo():
    """Quick end-to-end test: one in-corpus question, one out-of-corpus question."""
    for q in [
        "What Korean revenge film turns the revenge genre inside out?",   # in corpus
        "What does the guide say about the best pizza in Chicago?",       # out of corpus
    ]:
        print("\n" + "=" * 80)
        print("Q:", q)
        result = ask(q)
        print("\nANSWER:\n", result["answer"])
        print("\nSOURCES:")
        for s in result["sources"]:
            print("  -", s)
        if not result["sources"]:
            print("  (none - system declined to answer)")


if __name__ == "__main__":
    _demo()