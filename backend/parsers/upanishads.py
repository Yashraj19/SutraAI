"""Parser for The Upanishads (Swami Nikhilananda translation) PDF."""

import re
from .base import ScriptureEntry, extract_pdf_text

UPANISHAD_NAMES = [
    "Katha Upanishad",
    "Isa Upanishad",
    "Kena Upanishad",
    "Mundaka Upanishad",
    "Svetasvatara Upanishad",
    "Prasna Upanishad",
    "Mandukya Upanishad",
    "Aitareya Upanishad",
    "Brihadaranyaka Upanishad",
    "Taittiriya Upanishad",
    "Chhandogya Upanishad",
]


def parse(pdf_path: str) -> list[dict]:
    full_text = extract_pdf_text(pdf_path)
    lines = full_text.split("\n")
    entries = []

    current_upanishad = ""
    current_part = ""
    current_chapter = ""
    current_verse_num = ""

    upanishad_pat = re.compile(
        r"^(" + "|".join(re.escape(n) for n in UPANISHAD_NAMES) + r")\s*$"
    )
    part_pat = re.compile(r"^Part\s+(One|Two|Three|Four|Five|Six|Seven|Eight|Nine|Ten)\s*$", re.IGNORECASE)
    chapter_pat = re.compile(r"^Chapter\s+([IVXLC]+(?:\s*[–—-]\s*.+)?)\s*$", re.IGNORECASE)
    verse_pat = re.compile(r"^(\d+(?:\s*[—–-]\s*\d+)?)\s*$")
    header_pat = re.compile(r'^Source:\s*"The Upanishads')

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        if not line or header_pat.match(line) or line.isdigit() and len(line) <= 4 and not verse_pat.match(line):
            i += 1
            continue

        up_match = upanishad_pat.match(line)
        if up_match:
            current_upanishad = up_match.group(1)
            current_part = ""
            current_chapter = ""
            i += 1
            continue

        part_match = part_pat.match(line)
        if part_match:
            current_part = part_match.group(1)
            i += 1
            continue

        ch_match = chapter_pat.match(line)
        if ch_match:
            current_chapter = ch_match.group(1).strip()
            i += 1
            continue

        verse_match = verse_pat.match(line)
        if verse_match and current_upanishad:
            raw_num = verse_match.group(1).replace("—", "-").replace("–", "-").strip()
            if _is_page_number(raw_num, lines, i):
                i += 1
                continue

            current_verse_num = raw_num
            i += 1
            verse_lines = []
            while i < len(lines):
                s = lines[i].strip()
                if not s or header_pat.match(s):
                    i += 1
                    continue
                if verse_pat.match(s) and not _is_continuation(s, verse_lines):
                    break
                if upanishad_pat.match(s) or part_pat.match(s) or chapter_pat.match(s):
                    break
                verse_lines.append(s)
                i += 1

            text = re.sub(r"\s+", " ", " ".join(verse_lines)).strip()
            if text and len(text) > 10:
                section = current_upanishad
                if current_part:
                    section += f", Part {current_part}"
                if current_chapter:
                    section += f", Chapter {current_chapter}"

                entry = ScriptureEntry(
                    text_name="Upanishads",
                    section=section,
                    chapter=current_chapter or current_part or "1",
                    verse=current_verse_num,
                    translation=text,
                    translation_source="Swami Nikhilananda",
                    tradition="Vedic",
                )
                entries.append(entry.to_dict())
            continue

        i += 1

    return entries


def _is_page_number(num_str: str, lines: list[str], idx: int) -> bool:
    """Heuristic: if the number is on a line near a Source: header, it's a page number."""
    try:
        n = int(num_str)
    except ValueError:
        return False
    if n > 500:
        return True
    for offset in range(-3, 4):
        j = idx + offset
        if 0 <= j < len(lines) and 'Source: "The Upanishads' in lines[j]:
            return True
    return False


def _is_continuation(line: str, prev_lines: list[str]) -> bool:
    """Check if a number on its own line is actually part of a list in the verse text."""
    return len(prev_lines) > 0 and prev_lines[-1].endswith(",")
