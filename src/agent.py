"""
GuitarMind — agent.py
The core agent. It loads your API key, sends the user's request plus the
system prompt to Claude, and parses back a structured JSON progression.

Run:  python src/agent.py
Then type a mood/genre/skill request and press Enter. Type 'quit' to exit.
"""

import os
import sys
import json

from dotenv import load_dotenv
import anthropic

import pathlib
_here = pathlib.Path(__file__).resolve().parent
_prompts_code = (_here / "gm_prompts.py").read_text()
exec(_prompts_code)

# Load the API key (same secure pattern as Week 1).
load_dotenv()
api_key = os.getenv("ANTHROPIC_API_KEY")
if not api_key:
    sys.exit("ERROR: ANTHROPIC_API_KEY not found. Check your .env file.")

client = anthropic.Anthropic(api_key=api_key)
# --- Knowledge base retrieval (RAG) ---
import chromadb
from chromadb.utils import embedding_functions

_db_dir = pathlib.Path(__file__).resolve().parent.parent / "chroma_db"
_embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)
_chroma = chromadb.PersistentClient(path=str(_db_dir))
_theory = _chroma.get_collection("music_theory", embedding_function=_embed_fn)


def retrieve_theory(query: str, n: int = 3) -> str:
    """Find the most relevant theory chunks for the user's request."""
    results = _theory.query(query_texts=[query], n_results=n)
    chunks = results["documents"][0]
    return "\n\n".join(chunks)

def get_progression(user_request: str) -> dict:
    """Send one request to GuitarMind and return the parsed JSON result."""
    theory = retrieve_theory(user_request)
    augmented = (
        f"Relevant music theory from my knowledge base:\n{theory}\n\n"
        f"User request: {user_request}"
    )
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=800,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": augmented}],
    )

    raw_text = message.content[0].text.strip()

    # The model sometimes wraps JSON in ```json fences. Strip them if present.
    if raw_text.startswith("```"):
        raw_text = raw_text.strip("`")
        if raw_text.startswith("json"):
            raw_text = raw_text[4:].strip()

    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        # If parsing fails, surface the raw text so we can see what happened.
        return {"_parse_error": True, "raw": raw_text}


def show(result: dict) -> None:
    """Print a structured result in a readable way for the terminal."""
    if result.get("_parse_error"):
        print("\n(Could not parse JSON. Raw response below.)\n")
        print(result["raw"])
        return

    print("\n" + "=" * 50)
    print(f"KEY:        {result.get('key', '?')}")
    print(f"CHORDS:     {' - '.join(result.get('progression', []))}")
    print(f"ANALYSIS:   {' - '.join(result.get('roman_numerals', []))}")
    print(f"\nWHY:        {result.get('reasoning', '')}")
    refs = result.get("song_references", [])
    if refs:
        print(f"\nLIKE:       {', '.join(refs)}")
    note = result.get("skill_note")
    if note:
        print(f"TIP:        {note}")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    print("GuitarMind is ready. Describe a mood, genre, and your skill level.")
    print("Example: 'something melancholic but hopeful, indie folk, intermediate'")
    print("Type 'quit' to exit.\n")

    while True:
        user_request = input("You: ").strip()
        if user_request.lower() in {"quit", "exit", "q"}:
            print("Keep playing. 🎸")
            break
        if not user_request:
            continue
        print("\nThinking...")
        result = get_progression(user_request)
        show(result)
        