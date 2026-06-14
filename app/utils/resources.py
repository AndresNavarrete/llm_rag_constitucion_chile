from __future__ import annotations

from pathlib import Path

import streamlit as st


BASE_APP_DIR = Path(__file__).resolve().parents[1]


@st.cache_data(show_spinner=False)
def load_text_resource(relative_path: str) -> str:
    """Carga texto desde app/ en base a ruta relativa."""
    resource_path = BASE_APP_DIR / relative_path
    return resource_path.read_text(encoding="utf-8")
