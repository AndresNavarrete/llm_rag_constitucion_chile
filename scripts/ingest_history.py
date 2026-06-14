from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cl_legal_rag.config import settings
from cl_legal_rag.database import upsert_chunks
from cl_legal_rag.history_extractor import (
    extract_current_chunks_from_repo,
    extract_history_chunks,
)


def main() -> None:
    """Ingesta commit-aware: vigente + historico incremental por commit."""
    try:
        if not settings.raw_repo_dir.exists():
            raise FileNotFoundError(
                f"No existe repo raw en {settings.raw_repo_dir}. Clonalo primero."
            )

        current_chunks = extract_current_chunks_from_repo(settings.raw_repo_dir)
        history_chunks = extract_history_chunks(settings.raw_repo_dir)

        inserted_current = upsert_chunks(
            current_chunks,
            collection_name=settings.current_collection_name,
        )
        inserted_history = upsert_chunks(
            history_chunks,
            collection_name=settings.history_collection_name,
        )
    except Exception as exc:
        print(f"[ERROR] Fallo la ingesta historica: {exc}")
        raise SystemExit(1) from exc

    print("[OK] Ingesta historica completada")
    print(f"[INFO] Coleccion vigente: {settings.current_collection_name} -> {inserted_current}")
    print(f"[INFO] Coleccion historica: {settings.history_collection_name} -> {inserted_history}")
    print(f"[INFO] Chroma DB en: {settings.chroma_dir}")


if __name__ == "__main__":
    main()
