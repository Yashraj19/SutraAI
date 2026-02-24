"""Parser for The Complete Mahabharata (Ramesh Menon) PDF.
Prose retelling organized by Cantos within Parvas. No verse numbers.
We chunk by canto with paragraph-level sub-chunks for large cantos.
"""

import re
from .base import ScriptureEntry, extract_pdf_text

MAX_CHUNK_CHARS = 1500


def parse(pdf_path: str) -> list[dict]:
    full_text = extract_pdf_text(pdf_path)
    lines = full_text.split("\n")
    entries = []

    current_parva = ""
    current_canto = ""
    canto_buffer = []
    in_body = False

    canto_pat = re.compile(r"^CANTO\s+(\d+)\s*$", re.IGNORECASE)
    parva_pat = re.compile(r"^([A-Z][A-Z\s]+PARVA(?:\s+CONTINUED)?)\s*$")
    volume_pat = re.compile(r"^VOLUME\s+", re.IGNORECASE)
    toc_skip = re.compile(r"^\d+\.\s+")
    page_num_pat = re.compile(r"^\d+\s*$")
    copyright_pat = re.compile(r"^(copyright|ISBN|published|rupa|ramesh menon)", re.IGNORECASE)

    def flush_canto():
        nonlocal canto_buffer
        if not canto_buffer or not current_canto:
            canto_buffer = []
            return
        text = re.sub(r"\s+", " ", " ".join(canto_buffer)).strip()
        if len(text) < 50:
            canto_buffer = []
            return

        chunks = _split_into_chunks(text)
        for idx, chunk in enumerate(chunks):
            verse_label = "1" if len(chunks) == 1 else str(idx + 1)
            section = current_parva if current_parva else ""
            entry = ScriptureEntry(
                text_name="Mahabharata",
                section=section,
                chapter=current_canto,
                verse=verse_label,
                translation=chunk,
                translation_source="Ramesh Menon",
                tradition="Epic",
            )
            entries.append(entry.to_dict())
        canto_buffer = []

    for line in lines:
        stripped = line.strip()

        if not stripped or page_num_pat.match(stripped) or copyright_pat.match(stripped):
            continue
        if volume_pat.match(stripped):
            continue

        canto_match = canto_pat.match(stripped)
        if canto_match:
            flush_canto()
            current_canto = canto_match.group(1)
            in_body = True
            continue

        parva_match = parva_pat.match(stripped)
        if parva_match:
            current_parva = parva_match.group(1).strip().title()
            continue

        if in_body and len(stripped) > 5:
            canto_buffer.append(stripped)

    flush_canto()
    return entries


def _split_into_chunks(text: str) -> list[str]:
    if len(text) <= MAX_CHUNK_CHARS:
        return [text]

    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    current = []
    current_len = 0

    for sent in sentences:
        if current_len + len(sent) > MAX_CHUNK_CHARS and current:
            chunks.append(" ".join(current))
            current = [sent]
            current_len = len(sent)
        else:
            current.append(sent)
            current_len += len(sent) + 1

    if current:
        chunks.append(" ".join(current))

    return chunks
