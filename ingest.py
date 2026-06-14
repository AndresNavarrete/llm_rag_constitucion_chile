from __future__ import annotations

from src.config import settings
from src.database import upsert_chunks
from src.parser import load_markdown, split_by_articles


def main() -> None:
    """Ejecuta pipeline de ingesta para poblar Chroma local."""
    try:
        markdown_text = load_markdown(settings.data_file)
        chunks = split_by_articles(markdown_text)
        inserted = upsert_chunks(chunks)
    except Exception as exc:
        print(f"[ERROR] Fallo la ingesta: {exc}")
        raise SystemExit(1) from exc

    print(f"[OK] Ingesta completada. Chunks insertados/actualizados: {inserted}")
    print(f"[INFO] Chroma DB en: {settings.chroma_dir}")


if __name__ == "__main__":
    main()
