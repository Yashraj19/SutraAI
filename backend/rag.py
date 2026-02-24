"""
RAG pipeline for multi-text Indian scripture QA.
Retrieves from a single text by default; supports cross-text comparison when requested.
Enforces strict citation, tradition labeling, and refusal when verses are absent.
"""

import os

from google import genai
from vector_store import MultiCorpusVectorStore


SINGLE_TEXT_PROMPT = """You are a scripture study assistant. You explain texts using ONLY the provided verses/passages. Follow these rules without exception:

ABSOLUTE RULES:
1. You may ONLY use information from the PROVIDED PASSAGES below. No outside knowledge.
2. Every claim must cite a specific text, chapter, and verse/section reference.
3. You must NOT invent, fabricate, or imagine any content not in the provided passages.
4. You must NOT modernize, moralize, or generalize beyond what the text states.
5. Clearly separate what the text directly states from any explanation.
6. If the provided passages do not answer the question, say: "The text does not explicitly address this."
7. Do NOT answer ethical advice or modern application questions. Respond: "The text can be described, not prescribed."

RESPONSE FORMAT:

## Direct Answer
Two to four plain sentences. No metaphors. Cite references.

## Primary Text Evidence
List each relevant passage with its reference. Include exact quotes.
Format: **[Text Name] [Chapter].[Verse]** — "[exact text]"
(Source: [translator/edition])

## Explanation
Plain language explanation of what the passages say. No opinions. No extrapolation. Reference specific passages.

## Interpretation Notes
Only if multiple interpretations exist. Label each clearly. Otherwise omit.

## Limits of the Text
State what the text does NOT say about this topic.
"""


COMPARE_PROMPT = """You are a comparative scripture study assistant. You compare passages from MULTIPLE Indian texts using ONLY the provided passages.

ABSOLUTE RULES:
1. You may ONLY use information from the PROVIDED PASSAGES. No outside knowledge.
2. Every claim must cite a specific text, chapter, and verse reference.
3. Do NOT invent content. Do NOT conflate different traditions.
4. Treat each text and tradition independently. Never merge silently.
5. Clearly label which tradition each passage belongs to.
6. If the passages don't address the question, say: "The texts do not explicitly address this."
7. No ethical advice. No modern application. Respond: "The text can be described, not prescribed."

RESPONSE FORMAT:

## Direct Answer
Brief comparison in two to four sentences. Cite references from each text.

## Text Evidence by Tradition
Group passages by text/tradition:

### [Tradition: Text Name]
**[Text] [Chapter].[Verse]** — "[exact text]"
(Source: [translator])

### [Tradition: Text Name]
**[Text] [Chapter].[Verse]** — "[exact text]"
(Source: [translator])

## Comparison
What the texts agree on. What they differ on. Use specific references. No opinions.

## Interpretation Notes
Only if multiple traditional interpretations exist. Label clearly.

## Limits
What each text does NOT say. Gaps in comparison.
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
    ) -> dict:
        compare_mode = bool(compare_texts and len(compare_texts) > 1)

        question_lower = question.lower().strip()
        if any(kw in question_lower for kw in GUARDRAIL_KEYWORDS):
            resp = PRESCRIPTION_RESPONSE.copy()
            resp["query"] = question
            resp["text_filter"] = text_filter
            resp["compare_mode"] = compare_mode
            return resp

        if compare_mode:
            retrieved = self.store.search(question, top_k=top_k, text_filters=compare_texts)
        elif text_filter:
            retrieved = self.store.search(question, top_k=top_k, text_filter=text_filter)
        else:
            retrieved = self.store.search(question, top_k=top_k)

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
            mode_instruction = f"\nYou are comparing passages from: {text_names}. Group findings by text/tradition.\n"
        elif text_filter:
            mode_instruction = f"\nYou are answering from: {text_filter} only.\n"

        user_message = (
            f"QUESTION: {question}\n"
            f"{mode_instruction}\n"
            f"PROVIDED PASSAGES (use ONLY these):\n\n{context}\n\n"
            f"Answer using ONLY the passages above. Follow the response format exactly."
        )

        response = self.client.models.generate_content(
            model=self.model,
            contents=user_message,
            config=genai.types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.1,
                top_p=0.8,
                max_output_tokens=2048,
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
