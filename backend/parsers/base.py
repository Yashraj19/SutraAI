"""
Base interface for all scripture parsers.
Every parser must produce a list of entries conforming to the standard schema.
"""

from dataclasses import dataclass, asdict
import fitz


@dataclass
class ScriptureEntry:
    text_name: str
    section: str
    chapter: str
    verse: str
    translation: str
    translation_source: str
    tradition: str  # Vedic, Epic, Buddhist, Jain, Dharmashastra, Arthashastra

    def to_dict(self) -> dict:
        return asdict(self)


def extract_pdf_text(pdf_path: str) -> str:
    doc = fitz.open(pdf_path)
    full_text = ""
    for page in doc:
        full_text += page.get_text() + "\n"
    doc.close()
    return full_text
