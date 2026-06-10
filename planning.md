# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation - the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

This guide makes **underrated and hidden-gem films** searchable across four genres - sci-fi,
horror, foreign/international, and comedy - answering plain-language questions with grounded,
cited recommendations. This knowledge is hard to find otherwise because no single database
captures it: ratings sites like IMDb and Rotten Tomatoes surface what's *popular*, not what's
*good but forgotten*, so the real "you have to see this" picks stay scattered across dozens of
separate editorial listicles and user-curated lists. Pulling them into one corpus lets a viewer
answer cross-genre questions in one place instead of reading a dozen articles by hand.

---

## Documents

13 sources across four genres and two structural formats (editorial listicles + IMDb user-curated
lists), chosen so they together cover a range of questions rather than repeating one another.

| # | Source | Description | URL or location |
|---|--------|-------------|-----------------|
| 1 | Collider - "15 Most Underrated Sci-Fi Movies of the Last Decade" | Sci-fi, editorial listicle (per-film entries) | https://collider.com/best-underrated-sci-fi-movies-of-the-decade/ |
| 2 | SlashFilm - "20 Underrated Sci-Fi Movies You Need To Watch" | Sci-fi, editorial listicle | https://www.slashfilm.com/711403/underrated-sci-fi-movies-you-need-to-watch/ |
| 3 | IMDb user list - "underrated, unknown and forgotten Sci-Fi movies" | Sci-fi, user-curated list (short blurbs + metadata) | https://www.imdb.com/list/ls063340565/ |
| 4 | Collider - "13 Best Underrated Horror Movies That Time Forgot" | Horror, editorial listicle | https://collider.com/underrated-horror-movies-time-forgot/ |
| 5 | Collider - "9 Greatest Hidden-Gem Horror Masterpieces of the 21st Century" | Horror, editorial listicle | https://collider.com/best-hidden-gem-horror-masterpieces-21st-century-ranked/ |
| 6 | Collider - "8 Most Underrated Folk Horror Movies of All Time" | Horror (folk subgenre), editorial listicle | https://collider.com/most-underrated-folk-horror-movies-of-all-time-ranked/ |
| 7 | ScreenRant - "10 Hidden Gem International Movies Everyone Should Watch" | Foreign/intl, editorial listicle | https://screenrant.com/hidden-gem-international-movies/ |
| 8 | Den of Geek - "25 underappreciated modern foreign language films" | Foreign/intl, editorial listicle | https://www.denofgeek.com/movies/25-underappreciated-modern-foreign-language-films/ |
| 9 | CordCutting - "15 Underrated Foreign Films You Shouldn't Miss" | Foreign/intl, editorial listicle | https://cordcutting.com/what-to-watch/foreign-films/ |
| 10 | GamesRadar - "32 most underrated movie comedies of all time" | Comedy, editorial listicle | https://www.gamesradar.com/entertainment/movies/the-32-most-underrated-movie-comedies-of-all-time/ |
| 11 | Collider - "10 Most Underrated Comedies of the 21st Century (by Rotten Tomatoes)" | Comedy, editorial listicle | https://collider.com/underrated-comedies-21st-century-rotten-tomatoes/ |
| 12 | IMDb user list - "50 Seriously Underrated Comedies" | Comedy, user-curated list | https://www.imdb.com/list/ls020265773/ |
| 13 | Den of Geek - "Top 50 underappreciated comedy films of the past 30 years" | Comedy, editorial listicle | https://www.denofgeek.com/movies/top-50-underappreciated-comedy-films-of-the-past-30-years/ |

---

## Chunking Strategy

**Chunk size:** ~500 characters target, with a per-film-entry primary split (see Implementation note).

**Overlap:** 60 characters (about one sentence), applied only when an over-long entry is window-split.

**Implementation note (updated after Milestone 3):** The pipeline chunks structure-aware rather than by a blind fixed-character split. It first splits each document into its individual film entries (one entry = one chunk), and only if a single entry exceeds 800 characters does it fall back to a sliding window of 500 characters with 60-character overlap. Parameters in code: CHUNK_SIZE=500, CHUNK_OVERLAP=60, MAX_CHARS=800. On the first 4 documents this produced 40 chunks averaging 591 characters, each a self-contained film entry with its title intact.

**Reasoning:**

*Short reviews or long guides?* My corpus is a hybrid, but the meaningful unit is the same in both
formats. The editorial listicles (Collider, SlashFilm, ScreenRant, Den of Geek, GamesRadar) are
long pages, but internally they're a repeating series of per-film entries - a heading with the
**title + year** followed by 1-3 short paragraphs of justification. The IMDb lists are 1-3 sentence
blurbs plus structured metadata. So I'm not chunking "a long guide" or "a single short review" - I'm
chunking a long page *into its individual film entries*. That points to a medium chunk (~500 chars):
big enough to hold one full editorial entry, small enough not to swallow the next film. This is why
I'm not using a tiny review-style chunk (the editorial entries are bigger than a single review) or a
large FAQ-style chunk (that would merge unrelated films).

*Why overlap, and what it buys me.* The hard facts - title, year, country, director, one-line
premise - are concentrated in the heading and first sentence of each entry. The risk overlap guards
against is a split landing right after the heading, orphaning the justification paragraph from the
film it's about. A ~one-sentence overlap means the title/premise gets carried into the start of the
following chunk, so a key fact that lands near a boundary is still retrievable from at least one
whole chunk rather than half-present in two.

*How I'd know the chunks are wrong.* **Too small** would look like retrieved fragments with no
standalone meaning - a chunk like "exams are heavily based on" or a justification paragraph with no
film title in it, producing high distance scores and answers the model can't attribute to any movie.
**Too large** would look like one chunk covering three different films, so a specific query ("a
Korean revenge film") matches a diluted blob and the relevant film's signal is averaged out - vague,
off-target retrieval even when the right film is technically in the chunk. I'll judge this by
printing 5 random chunks (each should be one readable, self-contained film entry with its title
intact) and by watching distance scores during retrieval testing.
_(Confirm/adjust these numbers after inspecting real chunks in Milestone 3.)_

---

## Retrieval Approach

**Embedding model:** `all-MiniLM-L6-v2` via `sentence-transformers` (local, 384-dim, no API key,
no rate limits) - fast and well-matched to short, opinion-based entries.

**Top-k:** Start with **k = 5**. *How many is enough?* Each chunk is one film entry, so k=5 gives
the LLM about five candidate films per query - enough that the right one is very likely in the set
even when the single best match is slightly off, while staying focused. *Too few* (k=1-2) risks the
relevant film simply not being retrieved at all, so the model has nothing to ground on and either
declines or guesses. *Too many* (k=15+) pads the context with loosely related films, which dilutes
the prompt and can pull the answer off-target toward a tangential match. I'll tune after seeing real
results - drop toward 4 if answers get noisy, raise if a known-correct film keeps getting missed.

*Why semantic search works without shared words:* the embedding model maps text to vectors by
meaning, not exact tokens, so a query like "a scary movie that's more creepy than gory" lands near a
chunk that says "slow, atmospheric, overflowing with dread" even though they share almost no words.
That's exactly the behavior this corpus needs, since users describe films by mood/vibe while the
reviews use different vocabulary.

**Production tradeoff reflection:** If deploying for real users with cost no object, I'd weigh:
**(1) Multilingual support** - this corpus references many foreign-language films and could ingest
non-English reviews later, so a multilingual model would beat MiniLM's English focus.
**(2) Domain accuracy** - a larger model (e.g. `bge-large`, OpenAI `text-embedding-3-large`)
captures more nuance for mood/vibe queries ("something weird and unsettling") that don't lexically
match the text. **(3) Context length** - MiniLM truncates ~256 tokens, fine for one-film chunks but
limiting if chunks grow; larger API models allow longer chunks. **(4) Latency / privacy** - API
models add per-query cost and latency and send data off-device, while a local model keeps
everything in-house. For this project local MiniLM is the right call; production would likely favor
a larger and/or multilingual model.

---

## Evaluation Plan

Each expected answer is checkable against what a specific source explicitly says (not a subjective
"best film" judgment).

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | What's an underrated sci-fi film from the last decade that flopped at the box office but gained a cult following? | **Dredd (2012)** - Collider notes it did poorly at the box office despite positive critical/audience reaction and has since gained cult status. (Edge of Tomorrow is an acceptable secondary answer.) |
| 2 | Which underrated horror films are praised more for atmosphere/dread than for jump scares? | Atmospheric, slow-burn titles such as **The Blackcoat's Daughter, Lake Mungo, Session 9** - described as overflowing with atmosphere and dread rather than relying on jump scares. |
| 3 | What Korean revenge film does the guide describe as turning the revenge genre inside out? | **I Saw the Devil (Korea, 2010)**, directed by Kim Jee-woon - Den of Geek says it "turns revenge films inside out." |
| 4 | What hidden-gem folk horror movies does the guide recommend? | **Apostle, Lamb, Incantation, Hagazussa, Sator** - Collider's underrated folk horror list. |
| 5 | What underrated comedy do reviewers call one of the funniest films nobody saw? | **Walk Hard: The Dewey Cox Story** (or another comedy the lists frame as a cult classic / one of the funniest). NOTE: this question exposes a known failure - the comedy source was scraped as a title-only list, so there are no groundable comedy descriptions and the system cannot answer it. |

---

## Anticipated Challenges

1. **Heavy cross-list overlap and near-duplicate chunks.** Popular "underrated" picks (e.g.
   Snowpiercer, I Saw the Devil) appear across multiple source lists. Semantic search may return
   several near-identical chunks for one film, crowding out other relevant results and making the
   answer look more "confirmed" than the corpus actually supports. Mitigation: dedupe by film
   title and/or diversify results; watch for this in the evaluation.

2. **Title/justification split across a chunk boundary.** The film title + year lives in the entry
   heading and the reasoning follows in separate paragraphs. If chunking splits the heading from
   its body, a chunk loses which film it describes - breaking both grounding and source attribution
   (the model can't cite a film it can't identify). Mitigation: chunk per-film, keep the title
   inside every chunk, use small overlap, and store source metadata per chunk.

3. **Noisy scraped HTML and subjective "underrated" framing.** Editorial pages carry nav menus,
   ads, share buttons, and "related article" boilerplate that must be stripped, or it pollutes
   embeddings. Separately, "underrated" is inherently subjective, so evaluation ground-truth must
   be tied to what a source *explicitly states*, not to my own opinion of a film.

---

## Architecture

```mermaid
flowchart LR
    A["Document Ingestion<br/>(13 sources: editorial<br/>listicles + IMDb lists)<br/>load + clean HTML/boilerplate<br/>→ requests / saved .txt"]
      --> B["Chunking<br/>~500 chars, ~50-75 overlap<br/>one film entry per chunk<br/>→ custom chunk_text()"]
    B --> C["Embedding + Vector Store<br/>all-MiniLM-L6-v2<br/>(sentence-transformers)<br/>stored with source metadata<br/>→ ChromaDB"]
    C --> D["Retrieval<br/>semantic similarity<br/>top-k = 5<br/>→ ChromaDB query"]
    D --> E["Generation<br/>grounded answer + citations<br/>context-only prompt<br/>→ Groq llama-3.3-70b-versatile"]
    E --> F["Query Interface<br/>→ Gradio web UI"]
```

Pipeline stages and tools: **Ingestion** (requests / manual `.txt` for JS-blocked sources) →
**Chunking** (custom `chunk_text()`) → **Embedding + Vector Store** (`all-MiniLM-L6-v2` →
**ChromaDB**, with source metadata) → **Retrieval** (semantic top-k=5) → **Generation**
(**Groq llama-3.3-70b-versatile**, context-only) → surfaced through a **Gradio** UI.

---

## AI Tool Plan

**Milestone 3 - Ingestion and chunking:**
Tool: Claude. Input: the **Documents** table (source types and which are HTML vs. saved `.txt`),
the **Chunking Strategy** section (500 chars / ~60 overlap / one-film-per-chunk), and the
architecture diagram. Expected output: a loader that reads each source, a cleaning step that strips
nav/ads/HTML entities, and a `chunk_text()` that produces chunks matching my size/overlap with
source metadata attached. Verify by: printing 5 random chunks and confirming each is one readable,
self-contained film entry with its title intact, and checking the total chunk count lands in the
50-2,000 range.

**Milestone 4 - Embedding and retrieval:**
Tool: Claude. Input: the **Retrieval Approach** section and the diagram. Expected output: code that
embeds chunks with `all-MiniLM-L6-v2`, stores them in **ChromaDB** with source-name + position
metadata, and a `retrieve(query, k=5)` function returning chunks + distances + sources. Verify by:
running 3 of my evaluation questions, printing returned chunks and distance scores, and confirming
top results are on-topic with distances below ~0.5. If a ChromaDB API call is unfamiliar, I'll ask
Claude to explain it rather than copy it blindly.

**Milestone 5 - Generation and interface:**
Tool: Claude. Input: my grounding requirement (answer from retrieved context only; fall back to
"I don't have enough information on that"), the desired output format (answer + source list), and
the Gradio skeleton. Expected output: a prompt template that *enforces* grounding, a generation
function that appends source attribution programmatically from chunk metadata, and a minimal Gradio
app. Verify by: asking an in-corpus question (answer must trace to retrieved chunks + cite sources)
and an out-of-corpus question (system must decline rather than invent an answer).