# GuitarMind 🎸

**An AI agent that turns a feeling into a playable guitar chord progression — grounded in real music theory.**

You describe a mood, a genre, and your skill level. GuitarMind returns a complete chord progression, the music theory reasoning behind every choice, real songs that use a similar feel, and a tip tailored to your level.

---

## What it does

Tell GuitarMind something like *"something melancholic but hopeful, indie folk, intermediate"* and it returns:

- **Key & scale** — e.g. E minor
- **Chord progression** — e.g. Em – C – G – D
- **Roman numeral analysis** — e.g. i – VI – III – VII
- **Reasoning** — why those chords create that feeling, in plain English
- **Song references** — real, well-known tracks with a similar vibe
- **A skill-level tip** — practical advice matched to beginner / intermediate / advanced

---

## Why I built it

I'm a product manager and a guitar player. Guitarists often know the *feeling* they want — wistful, triumphant, tense — but lack the theory to translate it into chords. GuitarMind closes that gap. I also built it to demonstrate, end to end, that I can scope, design, and ship a working AI agent: not just talk about AI, but build one from scratch.

---

## How it works (architecture)

GuitarMind is an AI agent with five core parts:

1. **LLM reasoning engine** — Anthropic's Claude model does the actual musical reasoning. The app calls it through the Anthropic API.
2. **System prompt** — a fixed instruction set that defines GuitarMind's personality, rules, and the exact output format. It's sent with every request so behavior stays consistent.
3. **Structured output** — the agent returns a single JSON object (key, chords, reasoning, etc.) rather than free text, so the data is reliable and easy for a UI to render.
4. **RAG knowledge base** — a small, curated set of music-theory notes (scales, chord progressions, modes). Before answering, the agent retrieves the most relevant notes and grounds its response in them, rather than relying purely on the model's memory.
5. **Retrieval pipeline** — the theory notes are converted into embeddings (numerical representations of meaning) and stored in a local ChromaDB vector database. A user's request is matched against these to pull the most relevant chunks.
## Key design decisions

**Right-sized the retrieval layer.** I initially built the knowledge base on ChromaDB, a vector database with semantic embeddings. During deployment I hit repeated dependency conflicts, and stepping back I realized a full vector DB was overkill for a knowledge base of ~31 short, keyword-rich theory chunks. I replaced it with lightweight keyword-based retrieval in plain Python. This kept the same behavior (answers grounded in the curated theory files), removed three heavy dependencies, and made the app deploy reliably. Semantic embedding search is noted as a future enhancement for when the knowledge base grows.

**Honest scoping of the song references.** GuitarMind suggests real songs alongside each progression. I deliberately label these as songs in a *similar emotional space* rather than claiming they use the exact same chords. Verifying exact chord matches would require licensed chord data I couldn't access legally or reliably, and language models can state song chords confidently while being wrong. Rather than risk misleading users, I scoped the feature to mood-matching and surface an "explore" link per song. Progression-verified matching is a documented v2 idea.

**Grounding via retrieval was a deliberate demonstration, not a crutch.** Music theory is well-represented in the base model, so retrieval adds modest accuracy here. I included it primarily to demonstrate the RAG pattern end to end and to let the system cite a curated, controllable knowledge base — an honest framing I can defend in conversation.

## Deployment

Live app: https://guitarmind.streamlit.app

Deployed on Streamlit Community Cloud from this GitHub repo. The API key is supplied through Streamlit's encrypted secrets (never committed to the repo — `.env` is git-ignored). Getting to a clean deploy meant working through a real Python 3.14 dependency incompatibility, which ultimately drove the retrieval-layer simplification above. Note: on the free tier the app sleeps after inactivity and takes ~30 seconds to wake.

### The flow of a single request

```
User request ("dreamy, cinematic, intermediate")
        │
        ▼
Retrieve relevant theory chunks  ◄── ChromaDB vector search
        │
        ▼
Build prompt (theory + request) ──► Claude (with system prompt)
        │
        ▼
Structured JSON response
        │
        ▼
Displayed to the user
```

---

## Tech stack

| Layer | Tool |
|---|---|
| Reasoning engine | Claude (Anthropic API) |
| Language | Python |
| Embeddings | sentence-transformers (`all-MiniLM-L6-v2`, runs locally) |
| Vector database | ChromaDB |
| Secrets | python-dotenv (`.env`) |

---

## Key design decisions

- **Text input only, no audio.** I deliberately scoped out humming/pitch detection. It would have added weeks of audio-ML complexity without strengthening what the project demonstrates: agent design and product thinking.
- **RAG for grounding and demonstration.** Music theory is well-known to large models, so RAG isn't strictly required for accuracy here. I added it to ground answers in named sources and to demonstrate a complete retrieval pipeline — a core, in-demand AI engineering pattern.
- **Structured JSON output.** Chosen over free text so the planned web UI can render results cleanly and so output stays consistent and testable.
- **Local embeddings.** The embedding model runs on-device, so building the knowledge base costs nothing and needs no extra API calls.

---

## What I learned

- How to wire an LLM into an application through an API, and how to keep secrets out of source control.
- How a system prompt shapes an agent's behavior and how to enforce structured output.
- How RAG works end to end: chunking text, creating embeddings, storing them in a vector database, retrieving by semantic similarity, and grounding responses.
- Practical debugging — including a stubborn issue where a file was accidentally created as a directory, which broke every import until traced to the root cause.

---

## Project structure

```
guitarmind/
├── data/                  # curated music-theory notes (the knowledge base)
│   ├── scales.txt
│   ├── progressions.txt
│   └── modes.txt
├── src/
│   ├── gm_prompts.py      # system prompt + output schema
│   ├── agent.py           # the core agent (LLM call + RAG retrieval)
│   ├── build_knowledge.py # builds the vector database from data/
│   └── test_connection.py # Week 1 connection check
├── chroma_db/             # generated vector database (git-ignored)
├── .env                   # API key (git-ignored, never committed)
└── .gitignore
```

---

## Running it locally

```bash
# 1. set up environment
python3 -m venv venv
source venv/bin/activate
pip install anthropic python-dotenv chromadb sentence-transformers

# 2. add your Anthropic API key
cp .env.example .env        # then paste your key into .env

# 3. build the knowledge base (run once)
python src/build_knowledge.py

# 4. run the agent
python src/agent.py
```

---

## Roadmap

- [x] Core agent with structured output
- [x] RAG knowledge base over curated music theory
- [ ] Web UI (Streamlit) for non-technical users
- [ ] Public deployment + demo video
- [ ] Semantic (embedding-based) retrieval once the knowledge base grows beyond keyword matching
- [ ] Progression-verified song matching (songs that genuinely use the displayed chords)
- [ ] Audio playback / MIDI preview of the generated progression

---

*Built as a portfolio project to demonstrate end-to-end AI agent design — from problem definition through a working, retrieval-grounded implementation.*
