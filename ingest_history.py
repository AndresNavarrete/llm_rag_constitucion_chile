from __future__ import annotations

from src.config import settings
from src.database import upsert_chunks
from src.history_extractor import extract_current_chunks_from_repo, extract_history_chunks


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
