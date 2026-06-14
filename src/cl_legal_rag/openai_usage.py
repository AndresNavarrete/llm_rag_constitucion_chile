from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from cl_legal_rag.config import settings


@dataclass(frozen=True)
class ModelPricing:
    """Precio por millon de tokens para un modelo."""

    input_per_million: float
    output_per_million: float


PRICING_USD_PER_MILLION: Dict[str, ModelPricing] = {
    "text-embedding-3-small": ModelPricing(input_per_million=0.02, output_per_million=0.0),
    "gpt-4o-mini": ModelPricing(input_per_million=0.15, output_per_million=0.60),
}


def ensure_log_dir() -> None:
    """Crea el directorio de logs si no existe."""
    settings.logs_dir.mkdir(parents=True, exist_ok=True)


def estimate_cost_usd(model: str, input_tokens: int, output_tokens: int = 0) -> float:
    """Calcula costo estimado segun tabla local de precios."""
    pricing = PRICING_USD_PER_MILLION.get(model)
    if not pricing:
        return 0.0

    input_cost = (input_tokens / 1_000_000) * pricing.input_per_million
    output_cost = (output_tokens / 1_000_000) * pricing.output_per_million
    return input_cost + output_cost


def log_openai_usage(
    *,
    endpoint: str,
    model: str,
    request_meta: Dict[str, Any],
    usage: Optional[Dict[str, int]] = None,
) -> None:
    """Escribe un evento de uso OpenAI en JSONL local."""
    ensure_log_dir()

    prompt_tokens = int((usage or {}).get("prompt_tokens", 0))
    completion_tokens = int((usage or {}).get("completion_tokens", 0))
    total_tokens = int((usage or {}).get("total_tokens", prompt_tokens + completion_tokens))
    estimated_cost_usd = estimate_cost_usd(
        model=model,
        input_tokens=prompt_tokens,
        output_tokens=completion_tokens,
    )

    event = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "endpoint": endpoint,
        "model": model,
        "request_meta": request_meta,
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
        },
        "estimated_cost_usd": round(estimated_cost_usd, 8),
    }

    with settings.openai_usage_log.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
