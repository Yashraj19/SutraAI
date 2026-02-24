"""
RAG pipeline for multi-text Indian scripture QA.
Retrieves from a single text by default; supports cross-text comparison when requested.
Enforces strict citation and refusal when verses are absent.
Supports multi-turn chat via chat_history parameter.
"""

import os

from google import genai
from vector_store import MultiCorpusVectorStore


SINGLE_TEXT_PROMPT = """You are a knowledgeable and enthusiastic guide to Indian scriptures — a scholar who genuinely loves this material and wants to share it with depth and clarity.

CORE RULES (never break these):
1. Base your answer ONLY on the PROVIDED PASSAGES below. Do not use outside knowledge, even if you know it.
2. Every factual claim must be cited. Format: [Text Name] [Chapter].[Verse]
3. Never invent, fabricate, or paraphrase beyond what the passages actually say.
4. Do not give personal life advice or prescribe what the user should do.
5. If the passages don't address the question, say so honestly: "The text does not explicitly address this."

TONE & STYLE:
- Be warm, intellectually engaged, and thorough — like a scholar in conversation
- Write in flowing prose, not just bullet lists
- Use vivid, clear language to illuminate the text's meaning
- Highlight surprising, counterintuitive, or especially striking passages
- Responses should be complete — never cut off mid-thought
- Connect related ideas across the cited passages when relevant

RESPONSE FORMAT:

## Direct Answer
Answer the question clearly and directly (2–5 sentences), with citations.

## From the Text
Quote and explain the most relevant passages. Build understanding progressively.
For each key passage: cite it → quote it → explain what it means in context.

## What Else the Text Reveals
Any additional nuances, related ideas, or important context from the remaining passages.

## Notes
Only if needed: clarify interpretive debates, translation nuances, or what the text doesn't cover here.
"""


COMPARE_PROMPT = """You are a comparative scripture scholar — knowledgeable, enthusiastic, and precise. You illuminate how different Indian traditions approach the same questions.

CORE RULES (never break these):
1. Base your answer ONLY on the PROVIDED PASSAGES. No outside knowledge.
2. Every claim must cite the text name, chapter, and verse.
3. Never invent content or conflate different traditions.
4. Treat each text and tradition independently. Never merge their voices.
5. If passages don't address the question, say so honestly.
6. Do not give personal life advice.

TONE & STYLE:
- Be intellectually engaged and thorough
- Highlight genuine agreements AND genuine differences with specificity
- Note when traditions use the same concept but mean different things
- Responses should be complete — never cut off mid-thought
- Write in flowing prose, building a narrative of comparison

RESPONSE FORMAT:

## Overview
A 3–5 sentence overview of the comparison. What's the essential similarity or core tension?

## [Text Name] — What It Says
For each text: quote and explain its most relevant passages, with citations.
(Repeat this section for each text in the comparison.)

## Side by Side
Where do the texts genuinely agree? Where do they diverge? What might explain the differences — different traditions, purposes, or audiences?

## What the Texts Leave Unsaid
Important gaps or limits in what these passages reveal about the question.
"""


def format_context(entries: list[dict]) -> str:
    parts = []
    for e in entries:
        header = f"--- {e['text_name']}"
        if e.get("section"):
            header += f" | {e['section']}"
        header += f" | Chapter {e['chapter']}, Verse {e['verse']} ---"

        entry_text = (
            f"{header}\n"
            f"Tradition: {e['tradition']}\n"
            f"Translator: {e['translation_source']}\n"
            f"Text: {e['translation']}\n"
        )
        parts.append(entry_text)
    return "\n".join(parts)


def format_history_context(chat_history: list[dict]) -> str:
    """Format last 3 exchange pairs as context for the current question."""
    recent = chat_history[-6:]  # max 3 user + 3 assistant messages
    lines = []
    for msg in recent:
        role = "User" if msg["role"] == "user" else "Assistant"
        content = msg["content"]
        # Truncate long assistant messages to keep the prompt manageable
        if len(content) > 800:
            content = content[:800] + "...[summary truncated]"
        lines.append(f"{role}: {content}")
    return "CONVERSATION SO FAR:\n" + "\n\n".join(lines) + "\n\n"


REFUSAL_RESPONSE = {
    "answer": "The text does not explicitly address this. No relevant passages were found for this question.",
    "verses": [],
    "raw_response": "",
    "query": "",
    "text_filter": None,
    "compare_mode": False,
}

GUARDRAIL_KEYWORDS = [
    "should i", "what should", "is it right", "is it wrong",
    "advice for", "how to deal with", "in modern", "in today",
    "apply to", "real life", "practical advice", "life advice",
]

PRESCRIPTION_RESPONSE = {
    "answer": "The text can be described, not prescribed. This assistant describes what the scriptures say but does not offer personal, ethical, or practical life advice.",
    "verses": [],
    "raw_response": "",
    "query": "",
    "text_filter": None,
    "compare_mode": False,
}


class ScriptureRAG:
    def __init__(self, store: MultiCorpusVectorStore, api_key: str | None = None):
        self.store = store
        key = api_key or os.getenv("GOOGLE_API_KEY")
        self.client = genai.Client(api_key=key)
        self.model = "gemini-2.5-flash"

    def query(
        self,
        question: str,
        text_filter: str | None = None,
        compare_texts: list[str] | None = None,
        top_k: int = 8,
        score_threshold: float = 0.3,
        chat_history: list[dict] | None = None,
    ) -> dict:
        compare_mode = bool(compare_texts and len(compare_texts) > 1)

        question_lower = question.lower().strip()
        if any(kw in question_lower for kw in GUARDRAIL_KEYWORDS):
            resp = PRESCRIPTION_RESPONSE.copy()
            resp["query"] = question
            resp["text_filter"] = text_filter
            resp["compare_mode"] = compare_mode
            return resp

        # Use higher top_k when searching all scriptures for better coverage
        effective_top_k = top_k
        if text_filter is None and not compare_mode:
            effective_top_k = max(top_k, 12)

        if compare_mode:
            retrieved = self.store.search(question, top_k=effective_top_k, text_filters=compare_texts)
        elif text_filter:
            retrieved = self.store.search(question, top_k=effective_top_k, text_filter=text_filter)
        else:
            retrieved = self.store.search(question, top_k=effective_top_k)

        relevant = [v for v in retrieved if v["score"] >= score_threshold]

        if not relevant:
            resp = REFUSAL_RESPONSE.copy()
            resp["query"] = question
            resp["text_filter"] = text_filter
            resp["compare_mode"] = compare_mode
            return resp

        context = format_context(relevant)
        system_prompt = COMPARE_PROMPT if compare_mode else SINGLE_TEXT_PROMPT

        mode_instruction = ""
        if compare_mode:
            text_names = ", ".join(compare_texts)
            mode_instruction = f"\nYou are comparing passages from: {text_names}. Address each text separately.\n"
        elif text_filter:
            mode_instruction = f"\nYou are answering from: {text_filter} only.\n"
        else:
            mode_instruction = "\nYou are searching across all available scriptures.\n"

        # Build base message with context and question
        base_message = (
            f"QUESTION: {question}\n"
            f"{mode_instruction}\n"
            f"PROVIDED PASSAGES (use ONLY these):\n\n{context}\n\n"
            f"Answer using ONLY the passages above. Follow the response format exactly."
        )

        # Prepend conversation history if this is a follow-up in a chat
        if chat_history:
            user_message = format_history_context(chat_history) + base_message
        else:
            user_message = base_message

        response = self.client.models.generate_content(
            model=self.model,
            contents=user_message,
            config=genai.types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.3,
                top_p=0.9,
                max_output_tokens=8192,
            ),
        )

        verses_data = []
        for v in relevant:
            verses_data.append({
                "text_name": v["text_name"],
                "section": v.get("section", ""),
                "chapter": v["chapter"],
                "verse": v["verse"],
                "translation": v["translation"],
                "translation_source": v["translation_source"],
                "tradition": v["tradition"],
                "relevance_score": round(v["score"], 3),
            })

        return {
            "query": question,
            "answer": response.text,
            "verses": verses_data,
            "raw_response": response.text,
            "text_filter": text_filter,
            "compare_mode": compare_mode,
        }
