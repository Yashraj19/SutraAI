"""
Parse the Bhagavad Gita As It Is PDF into structured verse data.
Extracts chapter number, verse number, translation text, and purport for each verse.
"""

import re
import json
import fitz


def extract_text_from_pdf(pdf_path: str) -> str:
    doc = fitz.open(pdf_path)
    full_text = ""
    for page in doc:
        full_text += page.get_text() + "\n"
    doc.close()
    return full_text


def parse_verses(full_text: str) -> list[dict]:
    """Parse the full PDF text into individual verses with metadata."""
    verses = []
    current_chapter = 0

    chapter_pattern = re.compile(r"^CHAPTER\s+(ONE|TWO|THREE|FOUR|FIVE|SIX|SEVEN|EIGHT|NINE|TEN|ELEVEN|TWELVE|THIRTEEN|FOURTEEN|FIFTEEN|SIXTEEN|SEVENTEEN|EIGHTEEN)\b", re.MULTILINE)
    chapter_map = {
        "ONE": 1, "TWO": 2, "THREE": 3, "FOUR": 4, "FIVE": 5, "SIX": 6,
        "SEVEN": 7, "EIGHT": 8, "NINE": 9, "TEN": 10, "ELEVEN": 11,
        "TWELVE": 12, "THIRTEEN": 13, "FOURTEEN": 14, "FIFTEEN": 15,
        "SIXTEEN": 16, "SEVENTEEN": 17, "EIGHTEEN": 18,
    }

    text_pattern = re.compile(r"^TEXTS?\s+(\d+(?:[–\-−]+\d+)?)\s*$", re.MULTILINE)
    translation_pattern = re.compile(r"^TRANSLATION\s*$", re.MULTILINE)
    purport_pattern = re.compile(r"^PURPORT\s*$", re.MULTILINE)

    lines = full_text.split("\n")
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        chap_match = chapter_pattern.match(line)
        if chap_match:
            current_chapter = chapter_map[chap_match.group(1)]
            i += 1
            continue

        text_match = text_pattern.match(line)
        if text_match and current_chapter > 0:
            verse_ref = text_match.group(1)
            verse_ref = verse_ref.replace("–", "-").replace("−", "-")
            i += 1

            translation_text = ""
            purport_text = ""

            search_limit = min(i + 150, len(lines))
            j = i
            found_translation = False
            found_purport = False

            while j < search_limit:
                stripped = lines[j].strip()

                if text_pattern.match(stripped):
                    break

                if chapter_pattern.match(stripped):
                    break

                if translation_pattern.match(stripped):
                    found_translation = True
                    j += 1
                    trans_lines = []
                    while j < search_limit:
                        s = lines[j].strip()
                        if purport_pattern.match(s) or text_pattern.match(s) or chapter_pattern.match(s):
                            break
                        trans_lines.append(s)
                        j += 1
                    translation_text = " ".join(trans_lines).strip()
                    translation_text = re.sub(r"\s+", " ", translation_text)
                    continue

                if purport_pattern.match(stripped):
                    found_purport = True
                    j += 1
                    purp_lines = []
                    while j < search_limit:
                        s = lines[j].strip()
                        if text_pattern.match(s) or chapter_pattern.match(s):
                            break
                        purp_lines.append(s)
                        j += 1
                    purport_text = " ".join(purp_lines).strip()
                    purport_text = re.sub(r"\s+", " ", purport_text)
                    continue

                j += 1

            if translation_text:
                verse_entry = {
                    "book": "Bhagavad Gita",
                    "chapter": current_chapter,
                    "verse": verse_ref,
                    "translation_source": "A.C. Bhaktivedanta Swami Prabhupada",
                    "translation": translation_text,
                    "purport": purport_text[:2000] if purport_text else "",
                }
                verses.append(verse_entry)

            i = j
            continue

        i += 1

    return verses


def deduplicate_verses(verses: list[dict]) -> list[dict]:
    """Remove duplicates keeping the entry with the longest translation."""
    seen = {}
    for v in verses:
        key = f"{v['chapter']}:{v['verse']}"
        if key not in seen or len(v["translation"]) > len(seen[key]["translation"]):
            seen[key] = v
    result = sorted(seen.values(), key=lambda x: (x["chapter"], _verse_sort_key(x["verse"])))
    return result


def _verse_sort_key(verse_ref: str) -> tuple:
    parts = verse_ref.split("-")
    try:
        return (int(parts[0]),)
    except ValueError:
        return (0,)


def main():
    import sys
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else "../Bhagavad-gita-As-It-Is.pdf"
    print(f"Parsing PDF: {pdf_path}")

    full_text = extract_text_from_pdf(pdf_path)
    print(f"Extracted {len(full_text)} characters of text")

    verses = parse_verses(full_text)
    print(f"Found {len(verses)} raw verse entries")

    verses = deduplicate_verses(verses)
    print(f"After deduplication: {len(verses)} verses")

    chapters = {}
    for v in verses:
        ch = v["chapter"]
        chapters[ch] = chapters.get(ch, 0) + 1
    for ch in sorted(chapters.keys()):
        print(f"  Chapter {ch}: {chapters[ch]} verses")

    output_path = "gita_verses.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(verses, f, ensure_ascii=False, indent=2)
    print(f"Saved to {output_path}")

    if verses:
        print(f"\nSample verse (Ch {verses[0]['chapter']}, V {verses[0]['verse']}):")
        print(f"  Translation: {verses[0]['translation'][:200]}")


if __name__ == "__main__":
    main()
