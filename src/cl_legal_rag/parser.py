from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


ARTICLE_HEADER_RE = re.compile(
    r"^(?P<header>#{1,6}\s*Art[ií]culo\s+(?P<number>[\w\.\- ]+).*)$",
    re.IGNORECASE | re.MULTILINE,
)
CHAPTER_HEADER_RE = re.compile(r"^#{1,6}\s*(Cap[ií]tulo\s+.+)$", re.IGNORECASE)


@dataclass
class ParsedChunk:
    """Representa un fragmento indexable de la Constitucion."""

    chunk_id: str
    text: str
    metadata: Dict[str, str]


def load_markdown(path: Path) -> str:
    """Carga un archivo markdown desde disco."""
    if not path.exists():
        raise FileNotFoundError(f"No se encontro el archivo fuente: {path}")

    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise OSError(f"Error al leer el archivo {path}: {exc}") from exc


def extract_chapter_title(markdown_text: str, fallback: str = "Sin capitulo") -> str:
    """Extrae el primer titulo de capitulo detectado en el texto."""
    for line in markdown_text.splitlines():
        chapter_match = CHAPTER_HEADER_RE.match(line.strip())
        if chapter_match:
            return chapter_match.group(1).strip()
    return fallback


def split_by_articles(
    markdown_text: str,
    source: str = "legalize-cl",
    chapter: Optional[str] = None,
    chunk_prefix: str = "articulo",
    extra_metadata: Optional[Dict[str, str]] = None,
) -> List[ParsedChunk]:
    """Divide markdown por articulos y conserva metadatos relevantes."""
    matches = list(ARTICLE_HEADER_RE.finditer(markdown_text))
    if not matches:
        raise ValueError(
            "No se encontraron encabezados de articulo. "
            "Verifica el formato esperado: '##/### Articulo X'."
        )

    chunks: List[ParsedChunk] = []
    chapter_name = chapter or extract_chapter_title(markdown_text)
    metadata_extra = extra_metadata or {}

    for idx, match in enumerate(matches):
        start = match.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(markdown_text)
        content = markdown_text[start:end].strip()
        article_number = match.group("number").strip()

        chunk = ParsedChunk(
            chunk_id=f"{chunk_prefix}_{article_number}_{idx}",
            text=content,
            metadata={
                "articulo": article_number,
                "capitulo": chapter_name,
                "fuente": source,
                **metadata_extra,
            },
        )
        chunks.append(chunk)

    return chunks
