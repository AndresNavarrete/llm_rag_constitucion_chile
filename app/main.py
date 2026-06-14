from __future__ import annotations

import sys
from pathlib import Path
from typing import Generator, List

import streamlit as st
from openai import OpenAI

# Permite ejecutar la app sin instalar el paquete en editable.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cl_legal_rag.config import settings
from cl_legal_rag.database import search_similar
from cl_legal_rag.openai_usage import log_openai_usage


SYSTEM_PROMPT = """Eres un asistente legal especializado en la Constitucion Politica de la Republica de Chile.
Toda respuesta debe comenzar exactamente con: "Mi estimado, ".
Responde estrictamente usando el CONTEXTO RECUPERADO.
Si la respuesta no se puede deducir del contexto, responde exactamente:
'Mi estimado, no cuento con informacion oficial suficiente en el documento recuperado para responder con precision.'
Siempre cita el articulo cuando sea posible.
"""


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


def main() -> None:
    """App Streamlit para consultas RAG sobre la Constitucion de Chile."""
    st.set_page_config(page_title="CL Legal RAG", page_icon="⚖️", layout="centered")
    st.title("Cl-Legal-RAG")
    st.caption("Consultas constitucionales con recuperacion de contexto")

    question = st.text_area(
        "Haz tu pregunta sobre la Constitucion Politica de la Republica de Chile:",
        placeholder="Ejemplo: Que establece el articulo 19 sobre igualdad ante la ley?",
        height=100,
    )
    mode = st.radio(
        "Modo de consulta",
        options=["Vigente", "Historica"],
        horizontal=True,
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
                k=settings.retrieval_k,
                collection_name=collection_name,
            )
        except Exception as exc:
            st.error(f"Error en retrieval: {exc}")
            return

        if not results:
            st.error("No se encontraron fragmentos en la base vectorial. Ejecuta scripts/ingest.py.")
            return

        context_blocks: List[str] = []
        with st.expander("Ver contexto recuperado", expanded=False):
            for doc, score in results:
                articulo = doc.metadata.get("articulo", "N/A")
                capitulo = doc.metadata.get("capitulo", "N/A")
                ley = doc.metadata.get("ley", "N/A")
                commit_date = doc.metadata.get("commit_date", "N/A")
                st.markdown(
                    f"**Articulo {articulo}** | {capitulo} | ley={ley} | fecha={commit_date} | score={score:.3f}"
                )
                st.write(doc.page_content)
                context_blocks.append(doc.page_content)

        st.subheader("Respuesta")
        try:
            user_prompt = build_user_prompt(question=question.strip(), context_blocks=context_blocks)
            st.write_stream(stream_answer(user_prompt))
        except Exception as exc:
            st.error(f"Error en generacion: {exc}")


if __name__ == "__main__":
    main()
