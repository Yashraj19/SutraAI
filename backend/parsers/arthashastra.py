"""Parser for Kautilya's Arthashastra (R. Shamasastry 1915) PDF.
Prose text organized by Book > Chapter. No verse numbers.
We chunk by chapter, with paragraph-level sub-chunks for large chapters.
"""

import re
from .base import ScriptureEntry, extract_pdf_text

MAX_CHUNK_CHARS = 1500


def parse(pdf_path: str) -> list[dict]:
    full_text = extract_pdf_text(pdf_path)
    lines = full_text.split("\n")
    entries = []

    current_book = ""
    current_chapter = ""
    current_chapter_title = ""
    chapter_buffer = []

    header_pat = re.compile(r"^Kautilya's Arthashastra\s*$", re.IGNORECASE)
    book_pat = re.compile(r"^BOOK\s+([IVXLC]+)\s*$", re.IGNORECASE)
    chapter_pat = re.compile(r"^CHAPTER\s+([IVXLC]+)\.\s*(.+)", re.IGNORECASE)
    end_pat = re.compile(r"^\[Thus ends Chapter", re.IGNORECASE)
    page_num_pat = re.compile(r"^\d+\s*$")

    def flush_chapter():
        nonlocal chapter_buffer
        if not chapter_buffer or not current_chapter:
            chapter_buffer = []
            return
        text = re.sub(r"\s+", " ", " ".join(chapter_buffer)).strip()
        if len(text) < 20:
            chapter_buffer = []
            return

        chunks = _split_into_chunks(text)
        for idx, chunk in enumerate(chunks):
            verse_label = "1" if len(chunks) == 1 else str(idx + 1)
            entry = ScriptureEntry(
                text_name="Arthashastra",
                section=f"Book {current_book}" if current_book else "",
                chapter=current_chapter,
                verse=verse_label,
                translation=chunk,
                translation_source="R. Shamasastry (1915)",
                tradition="Arthashastra",
            )
            entries.append(entry.to_dict())
        chapter_buffer = []

    for line in lines:
        stripped = line.strip()

        if not stripped or header_pat.match(stripped) or page_num_pat.match(stripped):
            continue

        book_match = book_pat.match(stripped)
        if book_match:
            flush_chapter()
            current_book = book_match.group(1)
            continue

        ch_match = chapter_pat.match(stripped)
        if ch_match:
            flush_chapter()
            current_chapter = ch_match.group(1)
            current_chapter_title = ch_match.group(2).strip().rstrip(".")
            continue

        if end_pat.match(stripped):
            chapter_buffer.append(stripped)
            flush_chapter()
            continue

        chapter_buffer.append(stripped)

    flush_chapter()
    return entries


def _split_into_chunks(text: str) -> list[str]:
    """Split long chapter text into paragraph-level chunks."""
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
