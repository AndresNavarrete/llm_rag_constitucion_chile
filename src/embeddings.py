from __future__ import annotations

from typing import List

from langchain_core.embeddings import Embeddings
from openai import OpenAI

from src.config import settings
from src.openai_usage import log_openai_usage


class LoggedOpenAIEmbeddings(Embeddings):
    """Embeddings OpenAI con registro local de uso y costo."""

    def __init__(self, model: str) -> None:
        self.model = model
        self.client = OpenAI(api_key=settings.openai_api_key)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        response = self.client.embeddings.create(model=self.model, input=texts)
        usage = {
            "prompt_tokens": getattr(response.usage, "prompt_tokens", 0),
            "completion_tokens": 0,
            "total_tokens": getattr(response.usage, "total_tokens", 0),
        }
        log_openai_usage(
            endpoint="embeddings.create",
            model=self.model,
            request_meta={"items": len(texts), "kind": "documents"},
            usage=usage,
        )
        return [item.embedding for item in response.data]

    def embed_query(self, text: str) -> List[float]:
        response = self.client.embeddings.create(model=self.model, input=text)
        usage = {
            "prompt_tokens": getattr(response.usage, "prompt_tokens", 0),
            "completion_tokens": 0,
            "total_tokens": getattr(response.usage, "total_tokens", 0),
        }
        log_openai_usage(
            endpoint="embeddings.create",
            model=self.model,
            request_meta={"items": 1, "kind": "query"},
            usage=usage,
        )
        return response.data[0].embedding
