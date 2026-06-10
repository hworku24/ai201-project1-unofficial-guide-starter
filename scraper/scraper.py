
# scraper.py - collect the remaining source documents into documents/*.txt.

# Run this LOCALLY (it makes web requests, so it can't run inside the chat sandbox).
# It downloads each editorial listicle, strips the page down to the article body
# (headings + paragraphs), and writes a clean .txt in the same header + entries
# format the pipeline expects.

#   pip install requests beautifulsoup4     # already covered if in requirements.txt
#   python scraper.py

# NOTE: the two IMDb list URLs are JavaScript-rendered, so this generic scraper will
# NOT get their text. For those, open the page in your browser, select the list, and
# paste it into a .txt file by hand (see the bottom of this file). The assignment
# explicitly expects some sources to need manual copying.



import os
import re
import time
import requests
from bs4 import BeautifulSoup

DOCS_DIR = "documents"

# filename -> (TITLE, SOURCE, GENRE, URL)
SOURCES = {
    "scifi_slashfilm_need_to_watch.txt": (
        "20 Underrated Sci-Fi Movies You Need To Watch", "SlashFilm", "Sci-Fi",
        "https://www.slashfilm.com/711403/underrated-sci-fi-movies-you-need-to-watch/"),
    "horror_collider_hidden_gem_21st_century.txt": (
        "9 Greatest Hidden-Gem Horror Masterpieces of the 21st Century", "Collider", "Horror",
        "https://collider.com/best-hidden-gem-horror-masterpieces-21st-century-ranked/"),
    "horror_collider_folk_horror.txt": (
        "8 Most Underrated Folk Horror Movies of All Time", "Collider", "Horror",
        "https://collider.com/most-underrated-folk-horror-movies-of-all-time-ranked/"),
    "foreign_cordcutting_shouldnt_miss.txt": (
        "15 Underrated Foreign Films You Shouldn't Miss", "CordCutting", "Foreign/International",
        "https://cordcutting.com/what-to-watch/foreign-films/"),
    "comedy_gamesradar_most_underrated.txt": (
        "32 Most Underrated Movie Comedies of All Time", "GamesRadar", "Comedy",
        "https://www.gamesradar.com/entertainment/movies/the-32-most-underrated-movie-comedies-of-all-time/"),
    "comedy_collider_21st_century.txt": (
        "10 Most Underrated Comedies of the 21st Century", "Collider", "Comedy",
        "https://collider.com/underrated-comedies-21st-century-rotten-tomatoes/"),
    "comedy_denofgeek_past_30_years.txt": (
        "Top 50 Underappreciated Comedy Films of the Past 30 Years", "Den of Geek", "Comedy",
        "https://www.denofgeek.com/movies/top-50-underappreciated-comedy-films-of-the-past-30-years/"),
}

HEADERS = {"User-Agent": "Mozilla/5.0 (educational RAG project; document collection)"}


def extract_article(html):
    """Pull headings (h2/h3) and paragraphs out of the main article body."""
    soup = BeautifulSoup(html, "html.parser")
    # remove the obvious non-content elements
    for tag in soup(["script", "style", "nav", "aside", "footer", "header",
                     "figure", "form", "button"]):
        tag.decompose()
    article = soup.find("article") or soup.body or soup
    blocks = []
    for el in article.find_all(["h2", "h3", "p"]):
        text = el.get_text(" ", strip=True)
        if not text or len(text) < 25:          # skip empty / tiny boilerplate
            continue
        if el.name in ("h2", "h3"):
            blocks.append("\n" + text)           # blank line before each film heading
        else:
            blocks.append(text)
    return "\n".join(blocks).strip()


def write_doc(path, meta, body):
    title, source, genre, url = meta
    header = f"TITLE: {title}\nSOURCE: {source}\nGENRE: {genre}\nURL: {url}\n\n"
    with open(path, "w", encoding="utf-8") as f:
        f.write(header + body + "\n")


def main():
    os.makedirs(DOCS_DIR, exist_ok=True)
    for filename, meta in SOURCES.items():
        url = meta[3]
        try:
            resp = requests.get(url, headers=HEADERS, timeout=20)
            resp.raise_for_status()
            body = extract_article(resp.text)
            if len(body) < 200:
                print(f"!! {filename}: page returned little text "
                      f"(JS-rendered?) - may need manual copy.")
            write_doc(os.path.join(DOCS_DIR, filename), meta, body)
            print(f"OK {filename} ({len(body)} chars)")
        except Exception as e:
            print(f"!! {filename}: failed ({e}) - collect this one manually.")
        time.sleep(1)                            # be polite between requests

    print("\nDONE. Now open each new file in documents/ and skim it:")
    print(" - delete any leftover 'related article' / newsletter lines the scraper missed")
    print(" - make sure each film entry starts with its 'Title (Year)' line")
    print("\nMANUAL (JavaScript-rendered, scraper can't read them):")
    print("  imdb_scifi_forgotten.txt   <- https://www.imdb.com/list/ls063340565/")
    print("  imdb_comedy_seriously.txt  <- https://www.imdb.com/list/ls020265773/")
    print("  Open in browser, copy the list text, paste into a .txt using the same")
    print("  header format (TITLE/SOURCE/GENRE/URL, blank line, then one film per block).")


if __name__ == "__main__":
    main()