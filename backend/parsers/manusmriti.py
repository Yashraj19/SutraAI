"""Parser for Manusmriti PDF — chapter.verse format with English translations."""

import re
from .base import ScriptureEntry, extract_pdf_text


def parse(pdf_path: str) -> list[dict]:
    full_text = extract_pdf_text(pdf_path)
    lines = full_text.split("\n")
    entries = []

    current_chapter = "1"
    chapter_heading_pat = re.compile(r"^Chapter\s+(\d+)\s*$", re.IGNORECASE)
    verse_pat = re.compile(r"^(\d+)\.(\d+)\.\s*(.+)")
    verse_start_pat = re.compile(r"^(\d+)\.(\d+)\.\s*$")

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        ch_match = chapter_heading_pat.match(line)
        if ch_match:
            current_chapter = ch_match.group(1)
            i += 1
            continue

        inline_match = verse_pat.match(line)
        if inline_match:
            ch = inline_match.group(1)
            vs = inline_match.group(2)
            text_start = inline_match.group(3).strip()
            i += 1

            verse_lines = [text_start] if text_start else []
            while i < len(lines):
                s = lines[i].strip()
                if not s:
                    i += 1
                    continue
                if verse_pat.match(s) or verse_start_pat.match(s) or chapter_heading_pat.match(s):
                    break
                if _is_sanskrit_garbage(s):
                    i += 1
                    continue
                verse_lines.append(s)
                i += 1

            translation = re.sub(r"\s+", " ", " ".join(verse_lines)).strip()
            if translation and len(translation) > 5:
                entry = ScriptureEntry(
                    text_name="Manusmriti",
                    section=f"Chapter {ch}",
                    chapter=ch,
                    verse=vs,
                    translation=translation,
                    translation_source="G. Bühler (Sacred Books of the East)",
                    tradition="Dharmashastra",
                )
                entries.append(entry.to_dict())
            continue

        bare_match = verse_start_pat.match(line)
        if bare_match:
            ch = bare_match.group(1)
            vs = bare_match.group(2)
            i += 1
            verse_lines = []
            while i < len(lines):
                s = lines[i].strip()
                if not s:
                    i += 1
                    continue
                if verse_pat.match(s) or verse_start_pat.match(s) or chapter_heading_pat.match(s):
                    break
                if _is_sanskrit_garbage(s):
                    i += 1
                    continue
                verse_lines.append(s)
                i += 1

            translation = re.sub(r"\s+", " ", " ".join(verse_lines)).strip()
            if translation and len(translation) > 5:
                entry = ScriptureEntry(
                    text_name="Manusmriti",
                    section=f"Chapter {ch}",
                    chapter=ch,
                    verse=vs,
                    translation=translation,
                    translation_source="G. Bühler (Sacred Books of the East)",
                    tradition="Dharmashastra",
                )
                entries.append(entry.to_dict())
            continue

        i += 1

    entries = _deduplicate(entries)
    return entries


def _is_sanskrit_garbage(line: str) -> bool:
    """Detect garbled Sanskrit transliteration lines from the PDF."""
    non_ascii = sum(1 for c in line if ord(c) > 127 or c in "\\#$@{}[]¾Â")
    if len(line) > 0 and non_ascii / max(len(line), 1) > 0.15:
        return True
    if re.match(r'^[A-Z\W\d]{10,}$', line) and not any(c.islower() for c in line[:20]):
        return True
    return False


def _clean_translation(text: str) -> str:
    """Remove any trailing garbage Sanskrit from translation text."""
    parts = re.split(r'[A-Z\W]{5,}[\\#\$@{}\[\]¾Â]', text)
    if parts:
        return parts[0].strip()
    return text


def _deduplicate(entries: list[dict]) -> list[dict]:
    seen = {}
    for e in entries:
        key = f"{e['chapter']}:{e['verse']}"
        if key not in seen or len(e["translation"]) > len(seen[key]["translation"]):
            seen[key] = e
    return sorted(seen.values(), key=lambda x: (int(x["chapter"]), int(x["verse"])))
