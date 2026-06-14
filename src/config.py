from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Settings:
    """Configuracion central de rutas y modelos."""

    project_root: Path = Path(__file__).resolve().parent.parent
    data_file: Path = project_root / "data" / "constitucion.md"
    raw_repo_dir: Path = project_root / "data" / "raw" / "constitucion_chile"
    chroma_dir: Path = project_root / "chroma_db"
    logs_dir: Path = project_root / "logs"
    openai_usage_log: Path = logs_dir / "openai_usage.jsonl"
    current_collection_name: str = "current_constitution"
    history_collection_name: str = "constitutional_history"

    embedding_model: str = "text-embedding-3-small"
    chat_model: str = "gpt-4o-mini"
    retrieval_k: int = 3

    @property
    def openai_api_key(self) -> str:
        """Retorna la API key de OpenAI o lanza error si no existe."""
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key:
            raise ValueError(
                "No se encontro OPENAI_API_KEY en variables de entorno. "
                "Define la variable antes de ejecutar ingest.py o app.py"
            )
        return api_key


settings = Settings()
