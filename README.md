# The Unofficial Guide — Project 1

> **How to use this template:**
> Complete each section *after* you've built and tested the corresponding part of your system.
> Do not write placeholder text — if a section isn't done yet, leave it blank and come back.
> Every section below is required for submission. One-liners will not receive full credit.

--- 

## Domain

<!-- What topic or category of knowledge does your system cover?
     Why is this knowledge valuable, and why is it hard to find through official channels?
     Example: "Student reviews of CS professors at [university] — useful because official
     course descriptions don't reflect teaching style, exam difficulty, or workload." -->

This system covers underrated and hidden-gem films across four genres: science fiction, horror, foreign/international cinema, and comedy. A user asks a plain-language question (e.g. "what's a great sci-fi film almost nobody saw?") and gets a grounded, cited answer drawn from real recommendation articles and user-curated lists.

This knowledge is valuable and hard to find through official channels because no single database captures it. Ratings sites like IMDb and Rotten Tomatoes tell you what's popular, not what's good but forgotten - their default sorting buries low-vote-count gems. The actual "you have to see this" recommendations live scattered across dozens of separate editorial listicles and user-built lists, each covering only one genre or one decade. Pulling them into one searchable corpus lets a viewer answer cross-cutting questions ("which foreign films are worth the subtitles?", "what underrated horror is praised for atmosphere over jump scares?") that would otherwise require reading a dozen articles by hand.

--- 

## Document Sources

<!-- List every source you collected documents from.
     Be specific: include URLs, subreddit names, forum thread titles, or file names.
     Aim for variety — sources that together cover different subtopics or perspectives. -->

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | Collider - 15 Most Underrated Sci-Fi Movies of the Last Decade | Sci-fi, clean | https://collider.com/best-underrated-sci-fi-movies-of-the-decade/ |
| 2 | SlashFilm - 20 Underrated Sci-Fi Movies You Need To Watch | Sci-fi, scraped | https://www.slashfilm.com/711403/underrated-sci-fi-movies-you-need-to-watch/ |
| 3 | Collider - 13 Best Underrated Horror Movies That Time Forgot | Horror, clean | https://collider.com/underrated-horror-movies-time-forgot/ |
| 4 | Collider - 9 Greatest Hidden-Gem Horror Masterpieces of the 21st Century | Horror, scraped | https://collider.com/best-hidden-gem-horror-masterpieces-21st-century-ranked/ |
| 5 | Collider - 8 Most Underrated Folk Horror Movies of All Time | Horror, scraped | https://collider.com/most-underrated-folk-horror-movies-of-all-time-ranked/ |
| 6 | ScreenRant - 10 Hidden Gem International Movies Everyone Should Watch | Foreign, clean | https://screenrant.com/hidden-gem-international-movies/ |
| 7 | Den of Geek - 25 Underappreciated Modern Foreign Language Films | Foreign, clean | https://www.denofgeek.com/movies/25-underappreciated-modern-foreign-language-films/ |
| 8 | CordCutting - 15 Underrated Foreign Films You Shouldn't Miss | Foreign, scraped | https://cordcutting.com/what-to-watch/foreign-films/ |
| 9 | GamesRadar - 32 Most Underrated Movie Comedies of All Time | Comedy, scraped | https://www.gamesradar.com/entertainment/movies/the-32-most-underrated-movie-comedies-of-all-time/ |
| 10 | Collider - 10 Most Underrated Comedies of the 21st Century | Comedy, scraped | https://collider.com/underrated-comedies-21st-century-rotten-tomatoes/ |
| 11 | Den of Geek - Top 50 Underappreciated Comedy Films of the Past 30 Years | Comedy, scraped | https://www.denofgeek.com/movies/top-50-underappreciated-comedy-films-of-the-past-30-years/ |

---

## Chunking Strategy

<!-- Describe your chunking approach with enough specificity that someone else could reproduce it.
     Include:
     - Chunk size (characters or tokens) and why that size fits your documents
     - Overlap size and why (or why not) you used overlap
     - Any preprocessing you did before chunking (e.g., stripping HTML, removing headers)
     - What your final chunk count was across all documents -->

**Chunk size:** ~500 characters target. The chunker is structure-aware: it first splits each document into its individual film entries (one entry = one chunk), and only window-splits an entry into 500-character pieces if that entry exceeds 800 characters (CHUNK_SIZE=500, MAX_CHARS=800). 500 characters fits the documents because each film entry (a title plus a short review paragraph) is roughly that size, so one chunk = one self-contained recommendation.

**Overlap:** 60 characters, applied only when an over-long entry is window-split. Overlap carries the film title and opening sentence into the next piece so a key fact landing near a boundary stays retrievable in at least one whole chunk.

**Why these choices fit your documents:** The natural unit of meaning in these sources is a single film with its title and review, so chunking per entry keeps each recommendation intact and labeled. Preprocessing before chunking strips HTML tags and entities, removes boilerplate lines (nav, ads, share buttons, newsletter prompts), and then drops low-value chunks with three filters: under 80 characters (fragments), boilerplate matches (reviews/ads/nav), and "title-only" entries whose body after the title line is under 60 characters (scraped headings with no description). These filters cut the corpus from 344 raw chunks to 213 substantive ones.

**Final chunk count:** 213 chunks across 11 documents.

---

## Embedding Model

<!-- Name the embedding model you used and explain your choice.
     Then answer: if you were deploying this system for real users and cost wasn't a constraint,
     what tradeoffs would you weigh in choosing a different model?
     Consider: context length limits, multilingual support, accuracy on domain-specific text,
     latency, and local vs. API-hosted. -->

**Model used:** all-MiniLM-L6-v2 via sentence-transformers (local, 384-dimensional, no API key, no rate limits), stored in ChromaDB with hnsw:space=cosine so distances run 0 (identical) to 2. It is fast and well-matched to the short, opinion-based film entries in this corpus, and semantic search lets a query like "a scary movie that's more creepy than gory" match a chunk that says "slow, atmospheric, overflowing with dread" even with no shared words.

**Production tradeoff reflection:** If deploying for real users with cost no constraint, I would weigh four factors. (1) Multilingual support: this corpus references many foreign-language films and could ingest non-English reviews, so a multilingual model would beat MiniLM's English focus. (2) Domain accuracy: a larger model (e.g. bge-large or OpenAI text-embedding-3-large) captures more nuance for mood/vibe queries like "something weird and unsettling." (3) Context length: MiniLM truncates around 256 tokens, which is fine for one-film chunks but limiting if chunks grow. (4) Latency and privacy: API-hosted models add per-query cost and latency and send data off-device, while a local model keeps everything in-house. For this project local MiniLM is the right call; a production deployment would likely favor a larger and/or multilingual model.

---

## Grounded Generation

<!-- Explain how your system enforces grounding — how does it prevent the LLM from answering
     beyond the retrieved documents?
     Describe both your system prompt (what instruction you gave the model) and any structural
     choices (e.g., how you formatted the context, whether you filtered low-relevance chunks).
     Do not just say "I told it to use the documents" — show the actual instruction or explain
     the mechanism. -->

**System prompt grounding instruction:** The model (Groq llama-3.3-70b-versatile, temperature 0) is told: "Answer the user's question USING ONLY the numbered context passages provided. Use only the information in the context passages. Do NOT use any outside knowledge about films, even if you are confident. Do NOT add any details (plot, box office, budget, reception, awards, director) unless those exact details are written in the passages. A passage that is only a film title with no description does NOT count as enough information. If the passages do not contain enough information to answer, reply exactly: 'I don't have enough information on that.'" Structurally, the retrieved chunks are formatted into a numbered context block and the model never receives the question without that context, so it has nothing to fall back on except the passages.

**How source attribution is surfaced in the response:** Sources are appended programmatically in query.py, built from the metadata (film, source, source_file) of the retrieved chunks rather than asked of the LLM. If the model returns the refusal line, no sources are listed.

---

## Evaluation Report

<!-- Run your 5 test questions from planning.md through your system and record the results.
     Be honest — a partially accurate or inaccurate result that you explain well is more
     valuable than a suspiciously perfect result. -->

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | Underrated sci-fi film that flopped but became a cult favorite? | Dredd (2012) | "Mars Attacks..." - a film not present in any retrieved chunk (hallucination) | Off-target | Inaccurate |
| 2 | Underrated horror praised for atmosphere over jump scares? | Atmospheric titles (e.g. The Asphyx) | Named The Dark and the Wicked and Hagazussa as atmospheric/dread-driven | Partially relevant | Partially accurate |
| 3 | Korean revenge film that turns the genre inside out? | I Saw the Devil (2010) | "I Saw the Devil (Korea, 2010)" - correct, grounded in passage 3 | Relevant | Accurate |
| 4 | Name a hidden-gem folk horror movie and what makes it stand out. | A folk-horror title (e.g. Hagazussa) | Named Hagazussa, but the "stand out" detail was weakly grounded (retrieved chunk was title-only) | Partially relevant | Partially accurate |
| 5 | Underrated comedy reviewers call one of the funniest nobody saw? | A cult-classic comedy (e.g. Walk Hard) | "I don't have enough information on that." (no groundable comedy descriptions) | Off-target | Refused (appropriate) |

**Retrieval quality:** Relevant / Partially relevant / Off-target  
**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

<!-- Identify at least one question where retrieval or generation did not work as expected.
     Write a specific explanation of *why* it failed, tied to a part of the pipeline.

     "The answer was wrong" is not an explanation.

     "The relevant information was split across a chunk boundary, so retrieval returned
     only half the context — the model didn't have enough to answer correctly" is an explanation.

     "The embedding model treated the professor's nickname as out-of-vocabulary and returned
     results from an unrelated review" is an explanation. -->

**Question that failed:** Q1 - "What underrated sci-fi film flopped at the box office but became a cult favorite?" (Expected: Dredd.)

**What the system returned:** "Mars Attacks, as mentioned in passage 1, is an underrated sci-fi film that flopped at the box office..." - but Mars Attacks appears in none of the retrieved chunks (passage 1 was the title "13. What We Do in the Shadows"). The model hallucinated a plausible answer from its own training knowledge.

**Root cause (tied to a specific pipeline stage):** This is an ingestion-stage failure, not a generation one. The scraper (scraper.py) extracted film titles (page headings) from several sources but not the description paragraphs, producing "title-only" documents, especially for the sci-fi and comedy scraped sources. After chunking and filtering, there were no substantive sci-fi description chunks for this query to match, so retrieval returned off-topic title fragments (distances 0.478-0.544, all weak). Given near-empty context, the LLM filled the gap from training data. In short: bad documents -> bad chunks -> bad retrieval -> the model had nothing to ground on.

**What you would change to fix it:** Two fixes. (1) Tighten the grounding prompt so title-only context is treated as insufficient and the model refuses instead of hallucinating (added to query.py; this converts the hallucination into an honest "I don't have enough information"). (2) Fix ingestion by rebuilding the scraped documents in the same clean one-film-per-entry structure as the manually-formatted sources; the cleanly-structured source behind the correct Q3 answer retrieves and grounds correctly, confirming document quality is the real lever.

---

## Spec Reflection

<!-- Reflect on how planning.md shaped your implementation.
     Answer both questions with at least 2–3 sentences each. -->

**One way the spec helped you during implementation:** Writing the Chunking Strategy in planning.md before coding forced the decision that the meaningful unit is one film entry, not a fixed character block. That single decision shaped the entire pipeline - the loader, the per-entry splitter, and the metadata schema all followed from it. It is the reason the cleanly-structured documents chunk and retrieve so reliably, and it gave me a clear target to test each chunk against ("is this one self-contained film?").

**One way your implementation diverged from the spec, and why:** The spec described a mostly fixed ~500-character split. In practice I moved to structure-aware chunking (split on film entries first, window-split only over-long ones) and added three junk filters - minimum length, boilerplate, and title-only - that the spec never anticipated. These weren't planned; they were forced by inspecting real chunks and real retrieval output, where the scraped pages turned out far messier than the spec assumed. planning.md was updated to record the change.

---

## AI Usage

<!-- Describe at least 2 specific instances where you used an AI tool during this project.
     For each: what did you give the AI as input, what did it produce, and what did you
     change, override, or direct differently?

     "I used Claude to help me code" is not sufficient.
     "I gave Claude my Chunking Strategy section from planning.md and asked it to implement
     chunk_text(). It returned a function using a fixed character split. I overrode the
     chunk size from 500 to 200 because my documents are short reviews, not long guides." -->

**Instance 1**

- *What I gave the AI:* my planning.md Documents and Chunking Strategy sections, plus the architecture diagram.
- *What it produced:* pipeline.py with a structure-aware chunk_text() that splits on film entries and attaches source metadata.
- *What I changed or overrode:* after running it and inspecting chunks, I directed it to add filters it hadn't included - dropping sub-80-character fragments, boilerplate (reviews/ads), and title-only entries - because the scraped documents produced large amounts of junk. This cut the corpus from 344 to 213 chunks.

**Instance 2**

- *What I gave the AI:* my grounding requirement (answer from retrieved context only; refuse otherwise) and the desired output format (answer plus programmatic sources).
- *What it produced:* query.py with a system prompt and an ask() function that appends sources from chunk metadata.
- *What I changed or overrode:* after evaluation revealed a hallucination (the "Mars Attacks" answer to Q1), I had it tighten the prompt to forbid any detail not present in the passages and to treat title-only passages as insufficient, so the system refuses instead of inventing an answer.