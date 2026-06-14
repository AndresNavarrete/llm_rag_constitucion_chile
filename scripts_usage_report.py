from __future__ import annotations

import json
from collections import defaultdict

from src.config import settings


def main() -> None:
    if not settings.openai_usage_log.exists():
        print("No existe log de uso aun:", settings.openai_usage_log)
        return

    total_cost = 0.0
    total_prompt_tokens = 0
    total_completion_tokens = 0
    count = 0

    by_model = defaultdict(lambda: {"calls": 0, "cost": 0.0, "prompt": 0, "completion": 0})
    by_endpoint = defaultdict(lambda: {"calls": 0, "cost": 0.0})

    with settings.openai_usage_log.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            count += 1
            model = item.get("model", "unknown")
            endpoint = item.get("endpoint", "unknown")
            usage = item.get("usage", {})
            cost = float(item.get("estimated_cost_usd", 0.0))

            prompt = int(usage.get("prompt_tokens", 0))
            completion = int(usage.get("completion_tokens", 0))

            total_prompt_tokens += prompt
            total_completion_tokens += completion
            total_cost += cost

            by_model[model]["calls"] += 1
            by_model[model]["cost"] += cost
            by_model[model]["prompt"] += prompt
            by_model[model]["completion"] += completion

            by_endpoint[endpoint]["calls"] += 1
            by_endpoint[endpoint]["cost"] += cost

    print("=== OpenAI Usage Summary ===")
    print("Log file:", settings.openai_usage_log)
    print("Calls:", count)
    print("Prompt tokens:", total_prompt_tokens)
    print("Completion tokens:", total_completion_tokens)
    print("Estimated cost USD:", round(total_cost, 6))

    print("\nBy model:")
    for model, data in sorted(by_model.items()):
        print(
            f"- {model}: calls={data['calls']}, prompt={data['prompt']}, "
            f"completion={data['completion']}, cost=${data['cost']:.6f}"
        )

    print("\nBy endpoint:")
    for endpoint, data in sorted(by_endpoint.items()):
        print(f"- {endpoint}: calls={data['calls']}, cost=${data['cost']:.6f}")


if __name__ == "__main__":
    main()
