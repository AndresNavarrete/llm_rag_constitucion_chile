from __future__ import annotations

from typing import List, Tuple

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

from src.config import settings
from src.parser import ParsedChunk


def build_embeddings() -> OpenAIEmbeddings:
    """Construye el cliente de embeddings OpenAI."""
    return OpenAIEmbeddings(
        model=settings.embedding_model,
        api_key=settings.openai_api_key,
    )


def load_vector_store() -> Chroma:
    """Carga/crea el vector store local Chroma."""
    settings.chroma_dir.mkdir(parents=True, exist_ok=True)

    return Chroma(
        collection_name=settings.collection_name,
        embedding_function=build_embeddings(),
        persist_directory=str(settings.chroma_dir),
    )


def upsert_chunks(chunks: List[ParsedChunk]) -> int:
    """Inserta o actualiza chunks en Chroma y retorna cantidad."""
    if not chunks:
        return 0

    vector_store = load_vector_store()
    docs = [Document(page_content=chunk.text, metadata=chunk.metadata) for chunk in chunks]
    ids = [chunk.chunk_id for chunk in chunks]
    vector_store.add_documents(documents=docs, ids=ids)
    return len(chunks)


def search_similar(query: str, k: int) -> List[Tuple[Document, float]]:
    """Busca documentos similares junto a su score de similitud."""
    vector_store = load_vector_store()
    return vector_store.similarity_search_with_relevance_scores(query=query, k=k)
