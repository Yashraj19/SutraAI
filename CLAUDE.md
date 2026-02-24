# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Scripture Wisdom** is a RAG (Retrieval-Augmented Generation) application for querying Indian scriptures (Bhagavad Gita, Upanishads, Manusmriti, Arthashastra, Mahabharata, Ramayana). It returns answers grounded strictly in primary source texts with verse citations.

## Development Commands

### Backend (FastAPI)
```bash
# Activate virtual environment (from project root)
source venv/bin/activate

# Run backend server (from project root)
cd backend && source ../venv/bin/activate && uvicorn main:app --port 8000 --reload

# Rebuild vector store (after modifying parsers or corpus)
cd backend && python vector_store.py

# Re-parse all PDFs to JSON corpus files
cd backend && python parse_all.py
```

### Frontend (React + Vite)
```bash
cd frontend

npm run dev       # Start dev server (localhost:5173)
npm run build     # Production build
npm run lint      # ESLint
npm run preview   # Preview production build
```

### Environment Setup
Backend requires `backend/.env` with:
```
GOOGLE_API_KEY=your-google-api-key-here
```

## Architecture

### Data Flow
```
PDF Sources → Parsers (parsers/*.py) → JSON Corpus files (corpus_*.json)
    → MultiCorpusVectorStore (vector_store_multi.pkl, ~238MB)
    → ScriptureRAG.query() → Google Gemini 2.5 Flash
    → FastAPI /api/ask → React frontend
```

### Backend (`backend/`)

**`main.py`** — FastAPI app with three endpoints:
- `POST /api/ask` — accepts `{question, text_filter?, compare_texts?}`, returns `AnswerResponse`
- `GET /api/texts` — lists available scriptures with entry counts
- `GET /api/health` — health check with corpus stats

**`rag.py`** — `ScriptureRAG` class: guardrail checking → vector search → Gemini API call → structured response. Uses two system prompts: `SINGLE_TEXT_PROMPT` and `COMPARE_PROMPT`. Rejects questions matching prescription keywords (should i, what should, is it right, etc.).

**`vector_store.py`** — `MultiCorpusVectorStore`: manages 6 scripture corpora as separate embedding spaces. Embedding model: `gemini-embedding-001`. Similarity: cosine. Default relevance threshold: 0.3. The precomputed pickle file must be regenerated if corpora change.

**`parsers/`** — One parser per scripture. Each implements the base interface from `base.py` and outputs `ScriptureEntry` dataclasses with fields: `text_name`, `section`, `chapter`, `verse`, `translation`, `translation_source`, `tradition`.

### Frontend (`frontend/src/`)

**`App.jsx`** — All state management and API calls. Two modes: single-text query and compare mode (2+ texts). Hardcoded sample questions per scripture.

Key UI components inline in App.jsx:
- `AnswerDisplay` — renders markdown LLM response + tradition badges
- `VerseCard` — collapsible verse detail with relevance score
- `TraditionBadge` / `TextBadge` — color-coded by tradition (Vedic=gold, Epic=blue, Dharmashastra=green, Arthashastra=red)

### Corpus & Embeddings
- 6 precomputed JSON corpus files: `corpus_gita.json`, `corpus_upanishads.json`, etc.
- Precomputed vector store: `vector_store_multi.pkl` (~238MB, not committed to git likely)
- Rebuild order: parsers → `parse_all.py` → `vector_store.py`

## Key Design Decisions

- **Guardrails-first**: Questions asking for life advice or personal prescriptions are rejected before any LLM call. This is enforced in `rag.py` via keyword matching.
- **No outside knowledge**: System prompts explicitly forbid the LLM from using knowledge beyond the retrieved passages. If similarity score < 0.3 for all retrieved verses, returns a "text does not address this" response.
- **Pickle persistence**: The vector store is serialized as a pickle file to avoid re-embedding on every startup (embedding 6 full scriptures is slow/expensive).
- **Python 3.14 + venv**: Virtual environment is at project root (`/venv`), not inside `backend/`.
