from __future__ import annotations

from typing import List, Optional, Tuple

from langchain_chroma import Chroma
from langchain_core.documents import Document

from cl_legal_rag.config import settings
from cl_legal_rag.embeddings import LoggedOpenAIEmbeddings
from cl_legal_rag.parser import ParsedChunk


def build_embeddings() -> LoggedOpenAIEmbeddings:
    """Construye el cliente de embeddings OpenAI."""
    return LoggedOpenAIEmbeddings(model=settings.embedding_model)


def load_vector_store(collection_name: str) -> Chroma:
    """Carga/crea el vector store local Chroma."""
    settings.chroma_dir.mkdir(parents=True, exist_ok=True)

    return Chroma(
        collection_name=collection_name,
        embedding_function=build_embeddings(),
        persist_directory=str(settings.chroma_dir),
    )


def upsert_chunks(chunks: List[ParsedChunk], collection_name: str) -> int:
    """Inserta o actualiza chunks en Chroma y retorna cantidad."""
    if not chunks:
        return 0

    vector_store = load_vector_store(collection_name=collection_name)
    docs = [Document(page_content=chunk.text, metadata=chunk.metadata) for chunk in chunks]
    ids = [chunk.chunk_id for chunk in chunks]
    vector_store.add_documents(documents=docs, ids=ids)
    return len(chunks)


def search_similar(
    query: str,
    k: int,
    collection_name: str,
    metadata_filter: Optional[dict] = None,
) -> List[Tuple[Document, float]]:
    """Busca documentos similares junto a su score de similitud."""
    vector_store = load_vector_store(collection_name=collection_name)
    return vector_store.similarity_search_with_relevance_scores(
        query=query,
        k=k,
        filter=metadata_filter,
    )


def list_metadata_values(collection_name: str, field: str) -> List[str]:
    """Lista valores unicos de un campo de metadata dentro de una coleccion."""
    vector_store = load_vector_store(collection_name=collection_name)
    payload = vector_store.get(include=["metadatas"])
    metadatas = payload.get("metadatas", []) if payload else []

    values = set()
    for metadata in metadatas:
        if not metadata:
            continue
        value = metadata.get(field)
        if value is None:
            continue
        text_value = str(value).strip()
        if text_value:
            values.add(text_value)

    return sorted(values)
