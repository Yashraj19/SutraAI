"""
Master script to parse all available scripture PDFs into a unified JSON corpus.
Each text is parsed independently and tagged with its tradition.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from parsers.gita import parse as parse_gita
from parsers.upanishads import parse as parse_upanishads
from parsers.manusmriti import parse as parse_manusmriti
from parsers.arthashastra import parse as parse_arthashastra
from parsers.mahabharata import parse as parse_mahabharata
from parsers.ramayana import parse as parse_ramayana

PDF_DIR = os.path.join(os.path.dirname(__file__), "..")

TEXT_CONFIGS = [
    {
        "name": "Bhagavad Gita",
        "pdf": "Bhagavad-gita-As-It-Is.pdf",
        "parser": parse_gita,
        "output": "corpus_gita.json",
    },
    {
        "name": "Upanishads",
        "pdf": "upanishads_nikhilananda.pdf",
        "parser": parse_upanishads,
        "output": "corpus_upanishads.json",
    },
    {
        "name": "Manusmriti",
        "pdf": "Manu-Smriti.pdf",
        "parser": parse_manusmriti,
        "output": "corpus_manusmriti.json",
    },
    {
        "name": "Arthashastra",
        "pdf": "R. Shamasastry-Kautilya's Arthashastra   (1915).pdf",
        "parser": parse_arthashastra,
        "output": "corpus_arthashastra.json",
    },
    {
        "name": "Mahabharata",
        "pdf": "The Complete Mahabharata .pdf",
        "parser": parse_mahabharata,
        "output": "corpus_mahabharata.json",
    },
    {
        "name": "Ramayana",
        "pdf": "Valmiki-Ramayana-Eng-Translation-Griffith.pdf",
        "parser": parse_ramayana,
        "output": "corpus_ramayana.json",
    },
]


def main():
    all_entries = []
    summary = {}

    for cfg in TEXT_CONFIGS:
        pdf_path = os.path.join(PDF_DIR, cfg["pdf"])
        if not os.path.exists(pdf_path):
            print(f"SKIP: {cfg['name']} — PDF not found at {pdf_path}")
            continue

        print(f"\nParsing {cfg['name']}...")
        entries = cfg["parser"](pdf_path)
        print(f"  -> {len(entries)} entries")

        out_path = os.path.join(os.path.dirname(__file__), cfg["output"])
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(entries, f, ensure_ascii=False, indent=2)
        print(f"  -> Saved to {cfg['output']}")

        if entries:
            e = entries[0]
            print(f"  -> Sample: [{e['text_name']}] {e['section']} Ch {e['chapter']} V {e['verse']}")
            print(f"     {e['translation'][:150]}...")

        all_entries.extend(entries)
        summary[cfg["name"]] = len(entries)

    print(f"\n{'='*50}")
    print(f"TOTAL: {len(all_entries)} entries across {len(summary)} texts")
    for name, count in summary.items():
        print(f"  {name}: {count}")


if __name__ == "__main__":
    main()
