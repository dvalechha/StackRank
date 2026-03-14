"""Parse Job Description from .docx files."""

from pathlib import Path

from docx import Document


def parse_jd(jd_path: str | Path) -> str:
    """Extract text from a .docx Job Description file.

    Args:
        jd_path: Path to the .docx file

    Returns:
        Extracted text as string

    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If the file is not a valid .docx
    """
    jd_path = Path(jd_path)

    if not jd_path.exists():
        raise FileNotFoundError(f"Job Description file not found: {jd_path}")

    if jd_path.suffix.lower() != ".docx":
        raise ValueError(f"Job Description must be a .docx file, got: {jd_path.suffix}")

    doc = Document(jd_path)
    paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]

    return "\n".join(paragraphs)