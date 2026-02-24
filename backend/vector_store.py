"""
Multi-corpus vector store using Google's embedding API and numpy.
Each scripture text is stored as an independent corpus with tradition tags.
Supports single-text retrieval and cross-text comparison.
"""

import json
import os
import pickle

import numpy as np
from google import genai

STORE_PATH = "vector_store_multi.pkl"
EMBEDDING_MODEL = "gemini-embedding-001"

AVAILABLE_TEXTS = {
    "Bhagavad Gita": {"tradition": "Vedic", "corpus_file": "corpus_gita.json"},
    "Upanishads": {"tradition": "Vedic", "corpus_file": "corpus_upanishads.json"},
    "Manusmriti": {"tradition": "Dharmashastra", "corpus_file": "corpus_manusmriti.json"},
    "Arthashastra": {"tradition": "Arthashastra", "corpus_file": "corpus_arthashastra.json"},
    "Mahabharata": {"tradition": "Epic", "corpus_file": "corpus_mahabharata.json"},
    "Ramayana": {"tradition": "Epic", "corpus_file": "corpus_ramayana.json"},
}


class MultiCorpusVectorStore:
    def __init__(self, api_key: str | None = None):
        key = api_key or os.getenv("GOOGLE_API_KEY")
        if not key:
            raise ValueError("GOOGLE_API_KEY is required")
        self.client = genai.Client(api_key=key)
        self.documents: list[dict] = []
        self.embeddings: np.ndarray | None = None
        self.text_indices: dict[str, list[int]] = {}

    def _embed(self, texts: list[str]) -> np.ndarray:
        import time
        batch_size = 50
        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            for attempt in range(5):
                try:
                    result = self.client.models.embed_content(
                        model=EMBEDDING_MODEL,
                        contents=batch,
                    )
                    for emb in result.embeddings:
                        all_embeddings.append(emb.values)
                    break
                except Exception as e:
                    if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                        wait = 2 ** attempt * 5
                        print(f"    Rate limited, waiting {wait}s...")
                        time.sleep(wait)
                    else:
                        raise
            if (i // batch_size) % 20 == 0 and i > 0:
                print(f"    Embedded {i + len(batch)}/{len(texts)}...")
            time.sleep(0.5)
        return np.array(all_embeddings, dtype=np.float32)

    def _build_doc_text(self, entry: dict) -> str:
        parts = [
            f"{entry['text_name']}",
        ]
        if entry.get("section"):
            parts.append(f"Section: {entry['section']}")
        parts.append(f"Chapter {entry['chapter']}, Verse {entry['verse']}")
        parts.append(f"Translation: {entry['translation']}")
        return ". ".join(parts)

    def build_from_corpus_files(self, corpus_dir: str = "."):
        """Load all corpus JSON files and compute embeddings."""
        self.documents = []
        self.text_indices = {}
        texts_to_embed = []

        for text_name, info in AVAILABLE_TEXTS.items():
            path = os.path.join(corpus_dir, info["corpus_file"])
            if not os.path.exists(path):
                print(f"  SKIP: {text_name} — {info['corpus_file']} not found")
                continue

            with open(path, "r", encoding="utf-8") as f:
                entries = json.load(f)

            start_idx = len(self.documents)
            indices = []
            for entry in entries:
                doc_text = self._build_doc_text(entry)
                idx = len(self.documents)
                self.documents.append({
                    "id": f"{text_name.lower().replace(' ', '_')}_{entry['chapter']}_{entry['verse']}",
                    "text_name": entry["text_name"],
                    "section": entry.get("section", ""),
                    "chapter": entry["chapter"],
                    "verse": entry["verse"],
                    "translation": entry["translation"],
                    "translation_source": entry["translation_source"],
                    "tradition": entry["tradition"],
                    "doc_text": doc_text,
                })
                texts_to_embed.append(doc_text)
                indices.append(idx)

            self.text_indices[text_name] = indices
            print(f"  Loaded {len(entries)} entries for {text_name}")

        print(f"\nTotal documents: {len(self.documents)}")
        print(f"Computing embeddings for {len(texts_to_embed)} documents...")
        self.embeddings = self._embed(texts_to_embed)
        print(f"Embeddings shape: {self.embeddings.shape}")

    def save(self, path: str = STORE_PATH):
        data = {
            "documents": self.documents,
            "embeddings": self.embeddings,
            "text_indices": self.text_indices,
        }
        with open(path, "wb") as f:
            pickle.dump(data, f)
        size_mb = os.path.getsize(path) / (1024 * 1024)
        print(f"Saved vector store to {path} ({size_mb:.1f} MB)")

    def load(self, path: str = STORE_PATH):
        with open(path, "rb") as f:
            data = pickle.load(f)
        self.documents = data["documents"]
        self.embeddings = data["embeddings"]
        self.text_indices = data["text_indices"]
        print(f"Loaded {len(self.documents)} documents from {path}")
        for name, indices in self.text_indices.items():
            print(f"  {name}: {len(indices)} entries")

    def get_available_texts(self) -> list[dict]:
        """Return list of available texts with their metadata."""
        result = []
        for name, indices in self.text_indices.items():
            info = AVAILABLE_TEXTS.get(name, {})
            result.append({
                "name": name,
                "tradition": info.get("tradition", "Unknown"),
                "entry_count": len(indices),
            })
        return result

    def search(
        self,
        query: str,
        top_k: int = 8,
        text_filter: str | None = None,
        text_filters: list[str] | None = None,
    ) -> list[dict]:
        """
        Search for relevant entries.
        text_filter: single text name to restrict search (default retrieval)
        text_filters: list of text names for comparison mode
        """
        if self.embeddings is None or len(self.documents) == 0:
            return []

        query_emb = self._embed([query])

        if text_filter:
            allowed_indices = set(self.text_indices.get(text_filter, []))
        elif text_filters:
            allowed_indices = set()
            for tf in text_filters:
                allowed_indices.update(self.text_indices.get(tf, []))
        else:
            allowed_indices = None

        if allowed_indices is not None and len(allowed_indices) == 0:
            return []

        if allowed_indices is not None:
            idx_list = sorted(allowed_indices)
            subset_embs = self.embeddings[idx_list]
        else:
            idx_list = list(range(len(self.documents)))
            subset_embs = self.embeddings

        norms_docs = np.linalg.norm(subset_embs, axis=1, keepdims=True)
        norms_query = np.linalg.norm(query_emb, axis=1, keepdims=True)
        similarities = (subset_embs @ query_emb.T) / (norms_docs * norms_query.T + 1e-10)
        similarities = similarities.flatten()

        top_local = np.argsort(similarities)[::-1][:top_k]
        results = []
        for local_idx in top_local:
            global_idx = idx_list[local_idx]
            doc = self.documents[global_idx].copy()
            doc["score"] = float(similarities[local_idx])
            results.append(doc)
        return results


def main():
    from dotenv import load_dotenv
    load_dotenv()

    store = MultiCorpusVectorStore()
    store.build_from_corpus_files(".")
    store.save()

    print("\n--- Test: 'What is the soul?' (Bhagavad Gita only) ---")
    for r in store.search("What is the soul?", top_k=3, text_filter="Bhagavad Gita"):
        print(f"  [{r['score']:.3f}] [{r['text_name']}] Ch {r['chapter']} V {r['verse']}: {r['translation'][:100]}...")

    print("\n--- Test: 'What is dharma?' (Cross-text) ---")
    for r in store.search("What is dharma?", top_k=5):
        print(f"  [{r['score']:.3f}] [{r['text_name']}] Ch {r['chapter']} V {r['verse']}: {r['translation'][:100]}...")

    print("\n--- Test: 'duties of a king' (Arthashastra only) ---")
    for r in store.search("duties of a king", top_k=3, text_filter="Arthashastra"):
        print(f"  [{r['score']:.3f}] [{r['text_name']}] Ch {r['chapter']} V {r['verse']}: {r['translation'][:100]}...")


if __name__ == "__main__":
    main()
