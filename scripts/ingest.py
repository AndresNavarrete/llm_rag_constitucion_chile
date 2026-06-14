from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cl_legal_rag.config import settings
from cl_legal_rag.database import upsert_chunks
from cl_legal_rag.parser import load_markdown, split_by_articles


def main() -> None:
    """Ejecuta pipeline de ingesta para poblar Chroma local."""
    try:
        markdown_text = load_markdown(settings.data_file)
        chunks = split_by_articles(markdown_text)
        inserted = upsert_chunks(
            chunks,
            collection_name=settings.current_collection_name,
        )
    except Exception as exc:
        print(f"[ERROR] Fallo la ingesta: {exc}")
        raise SystemExit(1) from exc

    print(f"[OK] Ingesta completada. Chunks insertados/actualizados: {inserted}")
    print(f"[INFO] Chroma DB en: {settings.chroma_dir}")


if __name__ == "__main__":
    main()
