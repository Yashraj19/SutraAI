"""Parser for Valmiki Ramayana (Griffith English verse translation) PDF.
Organized by Book > Canto. Text is English verse, no verse numbering.
We chunk by canto with sub-chunks for long cantos.
"""

import re
from .base import ScriptureEntry, extract_pdf_text

MAX_CHUNK_CHARS = 1500


def parse(pdf_path: str) -> list[dict]:
    full_text = extract_pdf_text(pdf_path)
    lines = full_text.split("\n")
    entries = []

    current_book = ""
    current_canto = ""
    current_canto_title = ""
    canto_buffer = []

    book_pat = re.compile(r"^BOOK\s+([IVXLC]+)\.\s*", re.IGNORECASE)
    canto_pat = re.compile(r"^CANTO\s+([IVXLC]+)\s*[:.]?\s*(.*)", re.IGNORECASE)
    nav_pat = re.compile(r"^(Sacred Texts|Next:|Previous:|Footnotes|Index|p\.\s*\d+)", re.IGNORECASE)
    page_pat = re.compile(r"^\d+\s*$")
    footnote_pat = re.compile(r"^\d+:\d+")
    toc_canto_pat = re.compile(r"^Canto\s+[IVXLC]+", re.IGNORECASE)

    in_toc = True
    in_body = False

    def flush_canto():
        nonlocal canto_buffer
        if not canto_buffer or not current_canto:
            canto_buffer = []
            return

        text = re.sub(r"\s+", " ", " ".join(canto_buffer)).strip()
        text = _clean_text(text)
        if len(text) < 50:
            canto_buffer = []
            return

        chunks = _split_into_chunks(text)
        section = f"Book {current_book}" if current_book else ""
        chapter_label = f"{current_canto}"
        if current_canto_title:
            chapter_label = f"{current_canto}: {current_canto_title}"

        for idx, chunk in enumerate(chunks):
            verse_label = "1" if len(chunks) == 1 else str(idx + 1)
            entry = ScriptureEntry(
                text_name="Ramayana",
                section=section,
                chapter=chapter_label,
                verse=verse_label,
                translation=chunk,
                translation_source="Ralph T.H. Griffith (1870-1874)",
                tradition="Epic",
            )
            entries.append(entry.to_dict())
        canto_buffer = []

    for line in lines:
        stripped = line.strip()

        if not stripped or page_pat.match(stripped):
            continue

        book_match = book_pat.match(stripped)
        if book_match:
            flush_canto()
            current_book = book_match.group(1)
            in_toc = False
            in_body = False
            continue

        canto_match = canto_pat.match(stripped)
        if canto_match and not in_toc:
            flush_canto()
            current_canto = canto_match.group(1)
            title = canto_match.group(2).strip().rstrip(".")
            title = re.sub(r"\s*\d+b?\s*$", "", title).strip()
            current_canto_title = title
            in_body = True
            continue

        if in_toc:
            if book_pat.match(stripped):
                in_toc = False
            continue

        if nav_pat.match(stripped) or footnote_pat.match(stripped):
            continue

        if toc_canto_pat.match(stripped) and not in_body:
            continue

        if in_body and len(stripped) > 2:
            canto_buffer.append(stripped)

    flush_canto()
    return entries


def _clean_text(text: str) -> str:
    text = re.sub(r"\s*\d+b?\s*$", "", text)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()


def _split_into_chunks(text: str) -> list[str]:
    if len(text) <= MAX_CHUNK_CHARS:
        return [text]

    sentences = re.split(r"(?<=[.!?;])\s+", text)
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
