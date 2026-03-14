"""Parse resumes from .pdf and .docx files."""

import logging
from pathlib import Path
from typing import Any

import docx
import pdfplumber

logger = logging.getLogger(__name__)


def parse_resume(file_path: str | Path) -> dict[str, Any] | None:
    """Extract text from a resume file.

    Args:
        file_path: Path to the resume file (.pdf or .docx)

    Returns:
        Dict with 'candidate_name' and 'text' keys, or None if parsing fails
    """
    file_path = Path(file_path)
    suffix = file_path.suffix.lower()

    try:
        if suffix == ".pdf":
            text = _parse_pdf(file_path)
        elif suffix == ".docx":
            text = _parse_docx(file_path)
        else:
            logger.warning(f"Skipping unsupported file type: {file_path}")
            return None

        if not text or not text.strip():
            logger.warning(f"Empty content after parsing: {file_path}")
            return None

        # Use filename (without extension) as candidate name
        candidate_name = file_path.stem

        return {
            "candidate_name": candidate_name,
            "text": text
        }

    except Exception as e:
        logger.warning(f"Failed to parse {file_path}: {e}")
        return None


def _parse_pdf(file_path: Path) -> str:
    """Extract text from a PDF file."""
    text_parts = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return "\n".join(text_parts)


def _parse_docx(file_path: Path) -> str:
    """Extract text from a DOCX file."""
    doc = docx.Document(file_path)
    paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
    return "\n".join(paragraphs)