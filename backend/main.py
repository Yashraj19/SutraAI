"""
FastAPI server for the multi-text Indian scripture RAG platform.
Supports single-text queries and cross-text comparison.
"""

import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

load_dotenv()

from rag import ScriptureRAG
from vector_store import MultiCorpusVectorStore

app = FastAPI(
    title="Scripture Wisdom API",
    description="Ask questions about Indian scriptures. Answers grounded strictly in verse text.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

store = MultiCorpusVectorStore()
store.load("vector_store_multi.pkl")
rag = ScriptureRAG(store)


class QuestionRequest(BaseModel):
    question: str
    text_filter: str | None = None
    compare_texts: list[str] | None = None


class VerseDetail(BaseModel):
    text_name: str
    section: str
    chapter: str
    verse: str
    translation: str
    translation_source: str
    tradition: str
    relevance_score: float


class AnswerResponse(BaseModel):
    query: str
    answer: str
    verses: list[VerseDetail]
    text_filter: str | None
    compare_mode: bool


class TextInfo(BaseModel):
    name: str
    tradition: str
    entry_count: int


@app.post("/api/ask", response_model=AnswerResponse)
async def ask_question(req: QuestionRequest):
    question = req.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    if len(question) > 500:
        raise HTTPException(status_code=400, detail="Question too long (max 500 characters)")

    if req.text_filter and req.compare_texts:
        raise HTTPException(
            status_code=400,
            detail="Cannot use text_filter and compare_texts together. Use one or the other.",
        )

    try:
        result = rag.query(
            question=question,
            text_filter=req.text_filter,
            compare_texts=req.compare_texts,
        )
        return AnswerResponse(
            query=result["query"],
            answer=result["answer"],
            verses=[VerseDetail(**v) for v in result["verses"]],
            text_filter=result.get("text_filter"),
            compare_mode=result.get("compare_mode", False),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")


@app.get("/api/texts", response_model=list[TextInfo])
async def list_texts():
    return [TextInfo(**t) for t in store.get_available_texts()]


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "total_entries": len(store.documents),
        "texts": {name: len(idx) for name, idx in store.text_indices.items()},
    }
