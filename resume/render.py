"""Typst rendering and PDF text extraction."""
from __future__ import annotations

import json
from pathlib import Path

import typst
from pypdf import PdfReader

from .model import BuildError, Document

TEMPLATE = Path(__file__).with_name("template.typ")


def render(doc: Document, pdf_path: Path) -> dict:
    """Compile the document to `pdf_path`. Returns {bullet_id: rendered_line_count}."""
    inputs = {"data": json.dumps(doc.to_json(), ensure_ascii=False)}
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        # Bundled fonts only, so the output is identical on every machine.
        typst.compile(str(TEMPLATE), output=str(pdf_path), sys_inputs=inputs,
                      ignore_system_fonts=True)
        meta = json.loads(typst.query(str(TEMPLATE), "<bullet>", sys_inputs=inputs,
                                      ignore_system_fonts=True))
    except typst.TypstError as e:  # pragma: no cover - template bugs
        raise BuildError(f"typst failed: {e}") from e
    return {m["value"]["id"]: m["value"]["lines"] for m in meta}


def extract(pdf_path: Path) -> tuple[str, int]:
    """Plain text as a parser would see it (pure-Python extraction), and the page count."""
    reader = PdfReader(str(pdf_path))
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    return text, len(reader.pages)
