"""
evaluate.py - Milestone 6: run the 5 evaluation questions end-to-end.

For each test question it prints:
  - the question and the expected answer (your ground truth from planning.md)
  - the chunks that were retrieved, with cosine distances (retrieval quality)
  - the system's grounded answer and its cited sources (response quality)

Copy this output into the Evaluation Report table in README.md, then judge each row
(accurate / partially accurate / inaccurate) and pick one honest failure case.

Run locally:
  python evaluate.py
  # or save the output:  python evaluate.py > eval_output.txt
"""

from retrieve import retrieve
from query import ask

# (question, expected answer) - your 5 ground-truth pairs from planning.md
TEST_SET = [
    ("What underrated sci-fi film flopped at the box office but became a cult favorite?",
     "Dredd (2012) - flopped at the box office but gained cult status (Edge of Tomorrow acceptable)."),
    ("Which underrated horror films are praised for atmosphere and dread rather than jump scares?",
     "Atmospheric slow-burn titles (e.g. The Asphyx, Tourist Trap) valued for dread over jump scares."),
    ("What Korean revenge film turns the revenge genre inside out?",
     "I Saw the Devil (Korea, 2010), dir. Kim Jee-woon - 'turns revenge films inside out.'"),
    ("Name a hidden-gem folk horror movie and what makes it stand out.",
     "A folk horror title from the guide (e.g. Apostle/Lamb/Incantation), atmospheric and rural."),
    ("What underrated comedy do reviewers call one of the funniest films nobody saw?",
     "A comedy the lists call a cult classic / one of the funniest (e.g. Walk Hard, Bowfinger)."),
]


def main():
    for i, (question, expected) in enumerate(TEST_SET, 1):
        print("\n" + "#" * 90)
        print(f"Q{i}: {question}")
        print(f"EXPECTED: {expected}")
        print("#" * 90)

        # --- retrieval quality: show what came back and how close ---
        print("\nRETRIEVED CHUNKS (cosine distance; lower = closer):")
        for j, r in enumerate(retrieve(question, k=5), 1):
            flag = "  <-- weak (>0.5)" if r["distance"] > 0.5 else ""
            print(f"  {j}. dist={r['distance']:<5} [{r['film']}] "
                  f"({r['source_file']}){flag}")

        # --- response quality: the grounded answer + its sources ---
        result = ask(question, k=5)
        print("\nSYSTEM ANSWER:")
        print("  " + result["answer"].replace("\n", "\n  "))
        print("\nCITED SOURCES:")
        if result["sources"]:
            for s in result["sources"]:
                print("  - " + s)
        else:
            print("  (none - system declined to answer)")

        print("\nYOUR JUDGMENT  -> retrieval: [Relevant/Partial/Off-target]  "
              "response: [Accurate/Partial/Inaccurate]")


if __name__ == "__main__":
    main()