"""
app.py - Milestone 5: Gradio query interface for The Unofficial Guide.

A user types a question, the system retrieves relevant chunks, generates a grounded
answer, and shows both the answer and the sources it drew from. Styled with a dark,
cinematic theme.

Run locally:
  pip install gradio
  python app.py
Then open http://localhost:7860
"""

import gradio as gr
from query import ask

# -----------------------------------------------------------------------------
# Theme + custom CSS (cinematic dark look with gold accents)
# -----------------------------------------------------------------------------
theme = gr.themes.Soft(
    primary_hue=gr.themes.colors.amber,
    secondary_hue=gr.themes.colors.yellow,
    neutral_hue=gr.themes.colors.slate,
    font=[gr.themes.GoogleFont("Inter"), "system-ui", "sans-serif"],
)

CSS = """
.gradio-container {
    max-width: 820px !important;
    margin: 0 auto !important;
    background: #0d0d12 !important;
}
#hero {
    text-align: center;
    padding: 26px 18px 10px;
}
#hero h1 {
    font-size: 2.1rem;
    font-weight: 800;
    letter-spacing: -0.5px;
    margin: 0;
    background: linear-gradient(90deg, #f6c453, #e8a13a);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
#hero p {
    color: #9aa0aa;
    font-size: 1rem;
    margin: 8px 0 0;
}
#hero .badges { margin-top: 14px; }
#hero .badges span {
    display: inline-block;
    margin: 0 4px;
    padding: 4px 12px;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 600;
    color: #f6c453;
    background: rgba(246,196,83,0.10);
    border: 1px solid rgba(246,196,83,0.30);
}
#answer-box textarea {
    font-size: 1.05rem !important;
    line-height: 1.6 !important;
    background: #15151c !important;
    border: 1px solid #2a2a35 !important;
    border-radius: 14px !important;
}
#sources-box textarea {
    font-size: 0.9rem !important;
    color: #c9cdd6 !important;
    background: #121218 !important;
    border: 1px solid #23232d !important;
    border-radius: 14px !important;
}
label span { color: #f6c453 !important; font-weight: 600 !important; }
footer { display: none !important; }
#tagline { text-align:center; color:#6b7078; font-size:0.8rem; margin-top:18px; }
"""

HERO = """
<div id="hero">
  <h1>The Unofficial Guide</h1>
  <p>Hidden-gem films the mainstream missed - answered only from real reviews &amp; lists.</p>
  <div class="badges">
    <span>Sci-Fi</span><span>Horror</span><span>Foreign</span><span>Comedy</span>
  </div>
</div>
"""


def handle_query(question):
    if not question or not question.strip():
        return "Type a question above to get started.", ""
    result = ask(question)
    answer = result["answer"]
    if result["sources"]:
        sources = "\n".join(f"🎬  {s}" for s in result["sources"])
    else:
        sources = "(no sources - the system did not have enough information)"
    return answer, sources


with gr.Blocks(title="The Unofficial Guide") as demo:
    gr.HTML(HERO)

    question = gr.Textbox(
        label="Ask about an underrated film",
        placeholder="e.g. What Korean revenge film turns the genre inside out?",
        lines=2,
    )
    with gr.Row():
        ask_btn = gr.Button("🔍  Ask the Guide", variant="primary", scale=3)
        clear_btn = gr.ClearButton(value="Clear", scale=1)

    answer = gr.Textbox(label="Answer", lines=8, elem_id="answer-box")
    sources = gr.Textbox(label="Retrieved from", lines=4, elem_id="sources-box")

    clear_btn.add([question, answer, sources])

    gr.Examples(
        examples=[
            "What underrated sci-fi film flopped at the box office but became a cult favorite?",
            "Which underrated horror films are praised for atmosphere over jump scares?",
            "What hidden-gem folk horror movies does the guide recommend?",
            "Recommend a foreign-language film worth watching despite the subtitles.",
        ],
        inputs=question,
        label="Try one of these",
    )

    gr.HTML('<div id="tagline">Powered by semantic search + grounded generation · '
            'answers cite their sources</div>')

    ask_btn.click(handle_query, inputs=question, outputs=[answer, sources])
    question.submit(handle_query, inputs=question, outputs=[answer, sources])


if __name__ == "__main__":
    # Gradio 6.0 moved theme/css from Blocks() to launch()
    demo.launch(theme=theme, css=CSS)