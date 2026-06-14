"""
GuitarMind — agent.py
The core agent. Loads the API key, retrieves relevant music theory from the
local data files (simple keyword retrieval — no heavy vector DB needed for a
small knowledge base), sends the request + system prompt to Claude, and parses
back a structured JSON progression.
"""

import os
import sys
import json
import pathlib
import re

from dotenv import load_dotenv
import anthropic

# Make sure we can import gm_prompts whether run directly or imported by app.py
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gm_prompts import SYSTEM_PROMPT

# Load the API key. Works both locally (.env) and on Streamlit (env var / secrets).
load_dotenv()
api_key = os.getenv("ANTHROPIC_API_KEY")
if not api_key:
    sys.exit("ERROR: ANTHROPIC_API_KEY not found. Check your .env file or secrets.")

client = anthropic.Anthropic(api_key=api_key)

# --- Knowledge base retrieval (simple keyword scoring over data/*.txt) ---
_DATA_DIR = pathlib.Path(__file__).resolve().parent.parent / "data"


def _load_chunks() -> list[str]:
    """Read every .txt file in data/ and split into paragraph-sized chunks."""
    chunks = []
    if not _DATA_DIR.exists():
        return chunks
    for txt_file in sorted(_DATA_DIR.glob("*.txt")):
        text = txt_file.read_text(encoding="utf-8")
        for para in text.split("\n\n"):
            para = para.strip()
            if para:
                chunks.append(para)
    return chunks


_CHUNKS = _load_chunks()


def retrieve_theory(query: str, n: int = 3) -> str:
    """Return the n chunks that share the most words with the query."""
    if not _CHUNKS:
        return ""
    query_words = set(re.findall(r"[a-z]+", query.lower()))
    scored = []
    for chunk in _CHUNKS:
        chunk_words = set(re.findall(r"[a-z]+", chunk.lower()))
        overlap = len(query_words & chunk_words)
        scored.append((overlap, chunk))
    scored.sort(key=lambda pair: pair[0], reverse=True)
    top = [chunk for score, chunk in scored[:n] if score > 0]
    return "\n\n".join(top)


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
            print("Keep playing.")
            break
        if not user_request:
            continue
        print("\nThinking...")
        result = get_progression(user_request)
        show(result)
