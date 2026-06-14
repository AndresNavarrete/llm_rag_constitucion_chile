from __future__ import annotations

import sys
from datetime import date
from pathlib import Path
from typing import Dict, Generator, List, Optional

import streamlit as st
from openai import OpenAI

# Permite ejecutar la app sin instalar el paquete en editable.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from cl_legal_rag.config import settings
from cl_legal_rag.database import list_metadata_values, search_similar
from cl_legal_rag.openai_usage import log_openai_usage
from utils.resources import load_text_resource

SYSTEM_PROMPT = load_text_resource("prompts/system_prompt.md")


def build_user_prompt(question: str, context_blocks: List[str]) -> str:
    """Construye prompt final con contexto recuperado."""
    joined_context = "\n\n---\n\n".join(context_blocks)
    return f"""CONTEXTO RECUPERADO:\n{joined_context}\n\nPREGUNTA DEL USUARIO:\n{question}"""


def stream_answer(prompt: str) -> Generator[str, None, None]:
    """Genera respuesta en streaming usando OpenAI Chat Completions."""
    client = OpenAI(api_key=settings.openai_api_key)

    stream = client.chat.completions.create(
        model=settings.chat_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
        stream=True,
        stream_options={"include_usage": True},
    )

    usage = None
    for chunk in stream:
        if getattr(chunk, "usage", None):
            usage = {
                "prompt_tokens": chunk.usage.prompt_tokens,
                "completion_tokens": chunk.usage.completion_tokens,
                "total_tokens": chunk.usage.total_tokens,
            }
        choices = getattr(chunk, "choices", None) or []
        if choices:
            delta = choices[0].delta.content
            if delta:
                yield delta

    log_openai_usage(
        endpoint="chat.completions.create",
        model=settings.chat_model,
        request_meta={
            "stream": True,
            "temperature": 0,
            "prompt_chars": len(prompt),
        },
        usage=usage,
    )


@st.cache_data(show_spinner=False)
def load_history_filter_options() -> Dict[str, List[str]]:
    """Carga opciones historicas de filtros basadas en metadatos reales."""
    leyes = list_metadata_values(settings.history_collection_name, "ley")
    fechas = sorted(
        [
            value
            for value in list_metadata_values(settings.history_collection_name, "commit_date")
            if value != "HEAD"
        ]
    )
    return {"leyes": leyes, "fechas": fechas}


def parse_iso_date(value: str) -> Optional[date]:
    """Parsea fecha ISO YYYY-MM-DD a date."""
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def main() -> None:
    """App Streamlit para consultas RAG sobre la Constitucion de Chile."""
    st.set_page_config(page_title="CL Legal RAG", page_icon="⚖️", layout="wide")
    st.markdown(f"<style>{load_text_resource('styles/main.css')}</style>", unsafe_allow_html=True)

    st.markdown(load_text_resource("templates/hero.html"), unsafe_allow_html=True)

    left_col, right_col = st.columns([2.2, 1], gap="large")
    with left_col:
        question = st.text_area(
            "Tu pregunta constitucional",
            placeholder="Ejemplo: Que establece el articulo 19 sobre igualdad ante la ley?",
            height=130,
        )

    with right_col:
        mode = st.radio(
            "Modo de consulta",
            options=["Vigente", "Historica"],
            horizontal=True,
        )
        retrieval_k = st.slider(
            "Alcance de contexto (top-k)",
            min_value=2,
            max_value=8,
            value=settings.retrieval_k,
            help="A mayor valor, se consideran mas articulos para responder.",
        )

    metadata_filter: Optional[dict] = None
    if mode == "Historica":
        history_options = load_history_filter_options()
        leyes = history_options.get("leyes", [])
        fechas = history_options.get("fechas", [])
        parsed_dates = [d for d in (parse_iso_date(raw) for raw in fechas) if d is not None]
        default_start = min(parsed_dates) if parsed_dates else date(1810, 1, 1)
        default_end = max(parsed_dates) if parsed_dates else date.today()

        with st.container():
            st.subheader("Filtros historicos")
            h_col1, h_col2, h_col3 = st.columns([1.2, 1, 1])
            with h_col1:
                selected_ley = st.selectbox(
                    "Ley/Decreto",
                    options=["Todas"] + leyes,
                    index=0,
                )
            with h_col2:
                use_start_date = st.checkbox("Aplicar fecha desde", value=False)
                start_date = st.date_input(
                    "Desde",
                    value=default_start,
                    min_value=date(1810, 1, 1),
                    max_value=date.today(),
                    format="YYYY-MM-DD",
                )
            with h_col3:
                use_end_date = st.checkbox("Aplicar fecha hasta", value=False)
                end_date = st.date_input(
                    "Hasta",
                    value=default_end,
                    min_value=date(1810, 1, 1),
                    max_value=date.today(),
                    format="YYYY-MM-DD",
                )

        metadata_filter = {}
        if selected_ley != "Todas":
            metadata_filter["ley"] = selected_ley

        date_filter = {}
        if use_start_date and isinstance(start_date, date):
            date_filter["$gte"] = start_date.isoformat()
        if use_end_date and isinstance(end_date, date):
            date_filter["$lte"] = end_date.isoformat()
        if date_filter:
            metadata_filter["commit_date"] = date_filter

        if not metadata_filter:
            metadata_filter = None

        if parsed_dates:
            st.caption(
                f"Cobertura historica disponible: {min(parsed_dates).isoformat()} a {max(parsed_dates).isoformat()}."
            )

    if st.button("Consultar", type="primary"):
        if not question.strip():
            st.warning("Escribe una pregunta antes de consultar.")
            return

        try:
            collection_name = (
                settings.current_collection_name
                if mode == "Vigente"
                else settings.history_collection_name
            )
            results = search_similar(
                query=question.strip(),
                k=retrieval_k,
                collection_name=collection_name,
                metadata_filter=metadata_filter,
            )
        except Exception as exc:
            st.error(f"Error en retrieval: {exc}")
            return

        if not results:
            missing_data_script = "scripts/ingest_history.py" if mode == "Historica" else "scripts/ingest.py"
            st.error(
                f"No se encontraron fragmentos en la base vectorial para modo {mode}. "
                f"Ejecuta {missing_data_script}."
            )
            return

        context_blocks: List[str] = []
        with st.expander("Ver contexto recuperado", expanded=False):
            for doc, score in results:
                articulo = doc.metadata.get("articulo", "N/A")
                capitulo = doc.metadata.get("capitulo", "N/A")
                ley = doc.metadata.get("ley", "N/A")
                commit_date = doc.metadata.get("commit_date", "N/A")
                st.markdown(
                    (
                        f"**Articulo {articulo}** | **{capitulo}**  \n"
                        f"**Ley:** **{ley}** | **Fecha:** {commit_date}"
                    )
                )
                st.write(doc.page_content)
                context_blocks.append(
                    (
                        f"[METADATA] articulo={articulo} | capitulo={capitulo} | ley={ley} | "
                        f"commit_date={commit_date} | score={score:.3f}\n\n"
                        f"{doc.page_content}"
                    )
                )

        st.subheader("Respuesta")
        st.caption("La respuesta separa hechos textuales del contexto e interpretacion del asistente.")
        try:
            user_prompt = build_user_prompt(question=question.strip(), context_blocks=context_blocks)
            st.write_stream(stream_answer(user_prompt))
        except Exception as exc:
            st.error(f"Error en generacion: {exc}")


if __name__ == "__main__":
    main()
