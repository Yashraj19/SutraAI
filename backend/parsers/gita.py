"""Parser for Bhagavad Gita As It Is (Prabhupada) PDF."""

import re
from .base import ScriptureEntry, extract_pdf_text


CHAPTER_MAP = {
    "ONE": 1, "TWO": 2, "THREE": 3, "FOUR": 4, "FIVE": 5, "SIX": 6,
    "SEVEN": 7, "EIGHT": 8, "NINE": 9, "TEN": 10, "ELEVEN": 11,
    "TWELVE": 12, "THIRTEEN": 13, "FOURTEEN": 14, "FIFTEEN": 15,
    "SIXTEEN": 16, "SEVENTEEN": 17, "EIGHTEEN": 18,
}


def parse(pdf_path: str) -> list[dict]:
    full_text = extract_pdf_text(pdf_path)
    lines = full_text.split("\n")
    entries = []
    current_chapter = 0

    chapter_pat = re.compile(
        r"^CHAPTER\s+(ONE|TWO|THREE|FOUR|FIVE|SIX|SEVEN|EIGHT|NINE|TEN|"
        r"ELEVEN|TWELVE|THIRTEEN|FOURTEEN|FIFTEEN|SIXTEEN|SEVENTEEN|EIGHTEEN)\b",
        re.MULTILINE,
    )
    text_pat = re.compile(r"^TEXTS?\s+(\d+(?:[–\-−]+\d+)?)\s*$", re.MULTILINE)
    trans_pat = re.compile(r"^TRANSLATION\s*$", re.MULTILINE)
    purp_pat = re.compile(r"^PURPORT\s*$", re.MULTILINE)

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        chap_match = chapter_pat.match(line)
        if chap_match:
            current_chapter = CHAPTER_MAP[chap_match.group(1)]
            i += 1
            continue

        text_match = text_pat.match(line)
        if text_match and current_chapter > 0:
            verse_ref = text_match.group(1).replace("–", "-").replace("−", "-")
            i += 1
            translation_text = ""
            purport_text = ""

            search_limit = min(i + 150, len(lines))
            j = i
            while j < search_limit:
                s = lines[j].strip()
                if text_pat.match(s) or chapter_pat.match(s):
                    break

                if trans_pat.match(s):
                    j += 1
                    buf = []
                    while j < search_limit:
                        s2 = lines[j].strip()
                        if purp_pat.match(s2) or text_pat.match(s2) or chapter_pat.match(s2):
                            break
                        buf.append(s2)
                        j += 1
                    translation_text = re.sub(r"\s+", " ", " ".join(buf)).strip()
                    continue

                if purp_pat.match(s):
                    j += 1
                    buf = []
                    while j < search_limit:
                        s2 = lines[j].strip()
                        if text_pat.match(s2) or chapter_pat.match(s2):
                            break
                        buf.append(s2)
                        j += 1
                    purport_text = re.sub(r"\s+", " ", " ".join(buf)).strip()[:2000]
                    continue

                j += 1

            if translation_text:
                entry = ScriptureEntry(
                    text_name="Bhagavad Gita",
                    section="",
                    chapter=str(current_chapter),
                    verse=verse_ref,
                    translation=translation_text,
                    translation_source="A.C. Bhaktivedanta Swami Prabhupada",
                    tradition="Vedic",
                )
                entries.append(entry.to_dict())
            i = j
            continue

        i += 1

    entries = _deduplicate(entries)
    return entries


def _deduplicate(entries: list[dict]) -> list[dict]:
    seen = {}
    for e in entries:
        key = f"{e['chapter']}:{e['verse']}"
        if key not in seen or len(e["translation"]) > len(seen[key]["translation"]):
            seen[key] = e
    return sorted(seen.values(), key=lambda x: (int(x["chapter"]), _vs(x["verse"])))


def _vs(v: str) -> int:
    try:
        return int(v.split("-")[0])
    except ValueError:
        return 0
