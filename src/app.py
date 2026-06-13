"""
GuitarMind — app.py (styled version)
A polished web interface with a warm, musician-friendly look.
Reuses the same logic from agent.py: retrieve theory, call Claude, show result.

Run from the guitarmind folder:
    streamlit run src/app.py
"""

import pathlib
import sys

import streamlit as st

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from agent import get_progression


st.set_page_config(page_title="GuitarMind", page_icon="🎸", layout="centered")

# --- Styling: a warm, songwriter's-notebook aesthetic ---
st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(180deg, #FBF6EE 0%, #F4EADB 100%);
    }
    .block-container {
        max-width: 720px;
        padding-top: 3rem;
    }
    h1, h2, h3 {
        color: #3D2B1F !important;
        font-family: Georgia, 'Times New Roman', serif !important;
    }
    .stApp, p, label, .stMarkdown {
        color: #4A3B2E;
    }
    .stButton > button {
        background-color: #C2410C;
        color: #FFF8F0;
        border: none;
        border-radius: 10px;
        padding: 0.55rem 1.4rem;
        font-weight: 600;
        font-size: 1rem;
    }
    .stButton > button:hover {
        background-color: #9A3412;
        color: #FFF8F0;
    }
    .stTextInput input, .stSelectbox div[data-baseweb="select"] > div {
        background-color: #FFFDF8 !important;
        border: 1px solid #DDCBB0 !important;
        border-radius: 8px !important;
        color: #3D2B1F !important;
    }
    .result-card {
        background: #FFFDF8;
        border: 1px solid #E5D5BC;
        border-radius: 16px;
        padding: 1.6rem 1.8rem;
        margin-top: 0.5rem;
        box-shadow: 0 2px 10px rgba(120, 80, 40, 0.06);
    }
    .chords {
        font-family: Georgia, serif;
        font-size: 1.8rem;
        color: #C2410C;
        letter-spacing: 0.04em;
        margin: 0.2rem 0;
    }
    .romans {
        font-size: 0.95rem;
        color: #8A7A66;
        letter-spacing: 0.08em;
        margin-bottom: 1rem;
    }
    .keyline {
        font-size: 1.05rem;
        color: #6B5A45;
        font-style: italic;
        margin-bottom: 0.3rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown("# GuitarMind 🎸")
st.markdown(
    "<p style='font-size:1.05rem; color:#6B5A45; margin-top:-0.6rem;'>"
    "Turn a feeling into a playable chord progression — grounded in real music theory."
    "</p>",
    unsafe_allow_html=True,
)
st.write("")

mood = st.text_input(
    "What feeling or mood are you going for?",
    placeholder="e.g. melancholic but hopeful, like driving at night",
)

col1, col2 = st.columns(2)
with col1:
    genre = st.text_input("Genre", placeholder="indie folk, blues, pop...")
with col2:
    skill = st.selectbox("Your skill level", ["beginner", "intermediate", "advanced"])

st.write("")
generate = st.button("Generate progression", type="primary")

if generate:
    if not mood.strip():
        st.warning("Please describe a mood or feeling first.")
    else:
        request = f"{mood}; genre: {genre}; skill level: {skill}"
        with st.spinner("GuitarMind is thinking..."):
            result = get_progression(request)

        if result.get("_parse_error"):
            st.error("Something went wrong parsing the response. Raw output:")
            st.code(result.get("raw", ""))
        else:
            key = result.get("key", "")
            chords = "  &middot;  ".join(result.get("progression", []))
            romans = " &ndash; ".join(result.get("roman_numerals", []))
            reasoning = result.get("reasoning", "")

            card_html = f"""
            <div class="result-card">
                <div class="keyline">{key}</div>
                <div class="chords">{chords}</div>
                <div class="romans">{romans}</div>
                <p>{reasoning}</p>
            </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)

            refs = result.get("song_references", [])
            if refs:
                st.markdown("**Songs with a similar feel:**")
                st.caption("Songs in a similar emotional space — tap to explore them.")
                import urllib.parse
                for r in refs:
                    query = urllib.parse.quote(f"{r} song")
                    url = f"https://www.google.com/search?q={query}"
                    st.markdown(f"- {r} &nbsp; [🔗 listen / explore]({url})")
            tip = result.get("skill_note", "")
            if tip:
                st.info(f"💡 {tip}")

st.write("")
st.markdown(
    "<p style='font-size:0.85rem; color:#A0917C;'>"
    "Built with Claude + RAG over a curated music-theory knowledge base."
    "</p>",
    unsafe_allow_html=True,
)