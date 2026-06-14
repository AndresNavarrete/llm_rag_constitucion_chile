from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List


ARTICLE_HEADER_RE = re.compile(
    r"^(?P<header>#{1,6}\s*Art[ií]culo\s+(?P<number>[\w\.-]+).*)$",
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


def split_by_articles(markdown_text: str, source: str = "legalize-cl") -> List[ParsedChunk]:
    """Divide markdown por articulos y conserva metadatos de capitulo."""
    matches = list(ARTICLE_HEADER_RE.finditer(markdown_text))
    if not matches:
        raise ValueError(
            "No se encontraron encabezados de articulo. "
            "Verifica el formato esperado: '## Articulo X'."
        )

    chunks: List[ParsedChunk] = []
    current_chapter = "Sin capitulo"

    lines = markdown_text.splitlines()
    for line in lines:
        chapter_match = CHAPTER_HEADER_RE.match(line.strip())
        if chapter_match:
            current_chapter = chapter_match.group(1).strip()

    for idx, match in enumerate(matches):
        start = match.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(markdown_text)
        content = markdown_text[start:end].strip()
        article_number = match.group("number").strip()

        # Busca capitulo mas cercano hacia atras para metadato.
        previous_text = markdown_text[:start]
        chapter_lines = previous_text.splitlines()
        chapter_for_chunk = "Sin capitulo"
        for line in reversed(chapter_lines):
            chapter_match = CHAPTER_HEADER_RE.match(line.strip())
            if chapter_match:
                chapter_for_chunk = chapter_match.group(1).strip()
                break

        chunk = ParsedChunk(
            chunk_id=f"articulo_{article_number}_{idx}",
            text=content,
            metadata={
                "articulo": article_number,
                "capitulo": chapter_for_chunk,
                "fuente": source,
            },
        )
        chunks.append(chunk)

    return chunks
