from __future__ import annotations

from typing import List

from langchain_core.embeddings import Embeddings
from openai import OpenAI

from cl_legal_rag.config import settings
from cl_legal_rag.openai_usage import log_openai_usage


class LoggedOpenAIEmbeddings(Embeddings):
    """Embeddings OpenAI con registro local de uso y costo."""

    def __init__(self, model: str) -> None:
        self.model = model
        self.client = OpenAI(api_key=settings.openai_api_key)

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        """Estimacion simple de tokens para batching defensivo."""
        return max(1, len(text) // 4)

    def _split_batches(self, texts: List[str]) -> List[List[str]]:
        """Parte textos en batches para evitar exceder limite por request."""
        batches: List[List[str]] = []
        current_batch: List[str] = []
        current_tokens = 0

        for text in texts:
            text_tokens = self._estimate_tokens(text)

            if not current_batch:
                current_batch = [text]
                current_tokens = text_tokens
                continue

            would_exceed_tokens = (
                current_tokens + text_tokens > settings.embedding_max_tokens_per_request
            )
            would_exceed_items = (
                len(current_batch) + 1 > settings.embedding_max_items_per_request
            )

            if would_exceed_tokens or would_exceed_items:
                batches.append(current_batch)
                current_batch = [text]
                current_tokens = text_tokens
            else:
                current_batch.append(text)
                current_tokens += text_tokens

        if current_batch:
            batches.append(current_batch)
        return batches

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        embeddings: List[List[float]] = []
        batches = self._split_batches(texts)

        for idx, batch in enumerate(batches, start=1):
            response = self.client.embeddings.create(model=self.model, input=batch)
            usage = {
                "prompt_tokens": getattr(response.usage, "prompt_tokens", 0),
                "completion_tokens": 0,
                "total_tokens": getattr(response.usage, "total_tokens", 0),
            }
            log_openai_usage(
                endpoint="embeddings.create",
                model=self.model,
                request_meta={
                    "items": len(batch),
                    "kind": "documents",
                    "batch_index": idx,
                    "batch_count": len(batches),
                },
                usage=usage,
            )
            embeddings.extend(item.embedding for item in response.data)

        return embeddings

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
