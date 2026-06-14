from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    """Configuracion central de rutas y modelos."""

    project_root: Path = Path(__file__).resolve().parent.parent
    data_file: Path = project_root / "data" / "constitucion.md"
    chroma_dir: Path = project_root / "chroma_db"
    collection_name: str = "constitucion_chile"

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
