"""
pipeline.py - Milestone 3: document ingestion + chunking for The Unofficial Guide.

What it does (the three jobs from the assignment):
  1. LOAD   every .txt file in the documents/ folder.
  2. CLEAN  each one (strip any leftover HTML, entities, boilerplate; normalize whitespace).
  3. CHUNK  the cleaned text into per-film chunks (~500 chars target, ~60 overlap),
            attaching source metadata to every chunk.

It then prints the total chunk count and 5 random sample chunks so you can eyeball them,
and writes the chunks to chunks.json for Milestone 4 (embedding + vector store).

Chunking strategy (from planning.md, refined to be structure-aware):
  Each .txt is a header block followed by film entries separated by blank lines, where each
  entry starts with a "Title (Year)" line. The natural unit of meaning is ONE FILM, so we
  chunk per film entry. If an entry is longer than MAX_CHARS we fall back to a sliding
  window of CHUNK_SIZE chars with CHUNK_OVERLAP, so no single chunk gets too big.

Runs on the standard library only - no pip installs needed.
"""

import os
import re
import csv
import glob
import json
import random

# ---- chunking parameters (keep in sync with planning.md) --------------------
CHUNK_SIZE = 500      # target characters per chunk
CHUNK_OVERLAP = 60    # characters carried over between sliding-window chunks
MAX_CHARS = 800       # if a single film entry is longer than this, window-split it

DOCS_DIR = "documents"
OUTPUT_JSON = "chunks.json"


# ---- 1. LOAD ----------------------------------------------------------------
def load_documents(docs_dir=DOCS_DIR):
    """Read every .txt file in docs_dir. Returns list of {filename, raw_text}."""
    paths = sorted(glob.glob(os.path.join(docs_dir, "*.txt")))
    docs = []
    for path in paths:
        with open(path, encoding="utf-8") as f:
            docs.append({"filename": os.path.basename(path), "raw_text": f.read()})
    print(f"Loaded {len(docs)} documents from '{docs_dir}/'")
    return docs


# ---- 2. CLEAN ---------------------------------------------------------------
HTML_TAG = re.compile(r"<[^>]+>")
ENTITIES = {"&amp;": "&", "&nbsp;": " ", "&#39;": "'", "&quot;": '"',
            "&rsquo;": "'", "&lsquo;": "'", "&ldquo;": '"', "&rdquo;": '"',
            "&mdash;": "-", "&ndash;": "-"}
# lines that are pure boilerplate (nav, share buttons, ads) get dropped entirely
BOILERPLATE = re.compile(
    r"^(menu|sign in.*|follow(ed)?|like|share|close|log in|newsletter|"
    r"advertisement|ad ?- ?content continues below|ad|related|trending now|"
    r"recommended|image via.*|by .{0,40}|popular|read the latest issue|"
    r"join our mailing list|latest .*reviews?|tags:.*|more action|"
    r"get the best of .*|sign in to your .* account|share:|comment.*|"
    r"\d+ (min|minutes) read|est\. reading time.*|written by.*)$",
    re.IGNORECASE,
)

# whole chunks that are clearly not film content get dropped after chunking
JUNK_CHUNK = re.compile(
    r"(review:|mailing list|latest movie|^popular$|advertisement|"
    r"newsletter|read the latest|click here|continues below)",
    re.IGNORECASE,
)

def clean_text(text):
    """Strip HTML, decode entities, drop boilerplate lines, normalize whitespace."""
    text = HTML_TAG.sub("", text)              # remove any <tags>
    for ent, char in ENTITIES.items():         # decode common HTML entities
        text = text.replace(ent, char)
    kept = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            kept.append("")                     # keep blank lines (entry separators)
        elif BOILERPLATE.match(line):
            continue                            # drop nav/share/ad lines
        else:
            kept.append(re.sub(r"[ \t]+", " ", line))
    # collapse 3+ blank lines down to a single blank line
    return re.sub(r"\n{3,}", "\n\n", "\n".join(kept)).strip()


# ---- helpers: parse header + split into film entries ------------------------
HEADER_KEYS = ("TITLE:", "SOURCE:", "GENRE:", "URL:")

def parse_header(clean):
    """Pull TITLE/SOURCE/GENRE/URL metadata off the top of a document."""
    meta = {"title": "", "source": "", "genre": "", "url": ""}
    body_lines = []
    in_header = True
    for line in clean.splitlines():
        if in_header and line.startswith(HEADER_KEYS):
            key, _, val = line.partition(":")
            meta[key.strip().lower()] = val.strip()
        else:
            in_header = False
            body_lines.append(line)
    return meta, "\n".join(body_lines).strip()

FILM_TITLE_LINE = re.compile(r"^.{1,80}\(\d{4}.*\)\s*$")  # e.g. "Dredd (2012)"

def split_into_entries(body):
    """Split the body into film entries on blank lines."""
    return [e.strip() for e in re.split(r"\n\s*\n", body) if e.strip()]

def film_title_of(entry):
    """First line of an entry is the film title (with year)."""
    return entry.splitlines()[0].strip()


# ---- 3. CHUNK ---------------------------------------------------------------
def window_split(text, size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """Sliding-window splitter used only for over-long entries."""
    chunks, start = [], 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end].strip())
        if end >= len(text):
            break
        start = end - overlap
    return [c for c in chunks if c]

def chunk_documents(docs):
    """Turn loaded docs into chunks with metadata. One film entry = one chunk
    (over-long entries are window-split)."""
    chunks = []
    for doc in docs:
        clean = clean_text(doc["raw_text"])
        meta, body = parse_header(clean)
        for entry in split_into_entries(body):
            film = film_title_of(entry)
            # An entry's first line should be a short film title (e.g. "Dredd (2012)"
            # or "13. What We Do in the Shadows"). If it's long prose, this block is an
            # intro/methodology paragraph, not a film entry - skip it so it can't
            # outrank real film descriptions in retrieval.
            if len(film) > 80:
                continue
            # A real film entry has a description after the title line. If the body
            # is essentially empty, this is a title-only fragment (the scraper got the
            # heading but not the review text) - useless for grounding, so drop it.
            body_text = entry[len(entry.splitlines()[0]):].strip()
            if len(body_text) < 60:
                continue
            pieces = [entry] if len(entry) <= MAX_CHARS else window_split(entry)
            for i, piece in enumerate(pieces):
                if len(piece) < 80:             # drop tiny fragments
                    continue
                if JUNK_CHUNK.search(piece):    # drop boilerplate (reviews, ads, nav)
                    continue
                chunks.append({
                    "id": f"{doc['filename']}::{len(chunks)}",
                    "text": piece,
                    "source_file": doc["filename"],
                    "title": meta["title"],
                    "source": meta["source"],
                    "genre": meta["genre"],
                    "url": meta["url"],
                    "film": film,
                    "part": i,                  # 0 unless the entry was window-split
                })
    return chunks


# ---- run --------------------------------------------------------------------
def main():
    docs = load_documents()
    chunks = chunk_documents(docs)

    print(f"\nProduced {len(chunks)} chunks across {len(docs)} documents.")
    lengths = [len(c["text"]) for c in chunks]
    if lengths:
        print(f"Chunk length: min={min(lengths)}  max={max(lengths)}  "
              f"avg={sum(lengths)//len(lengths)} chars")

    print("\n--- 5 random sample chunks ---")
    for c in random.sample(chunks, min(5, len(chunks))):
        print(f"\n[{c['film']}]  (source: {c['source_file']}, genre: {c['genre']})")
        print(c["text"])

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)
    print(f"\nWrote {len(chunks)} chunks to {OUTPUT_JSON}")


if __name__ == "__main__":
    main()