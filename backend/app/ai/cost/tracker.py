"""In-memory telemetry and cost estimation tracker for LLM and Embedding API calls."""

import threading
import time
from collections import defaultdict
from typing import Any, Dict, Optional


# Configurable approximate pricing per 1,000 tokens for observability (OpenAI pricing reference)
ESTIMATED_RATES_PER_1K_TOKENS = {
    "gpt-4o-mini": {"input": 0.00015, "output": 0.00060},
    "text-embedding-3-small": {"input": 0.00002, "output": 0.0},
    "default": {"input": 0.00020, "output": 0.00060},
}


class AICostTracker:
    """Thread-safe usage and cost telemetry tracker for AI operations."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._operations = defaultdict(int)
        self._failures = defaultdict(int)
        self._tokens_in = defaultdict(int)
        self._tokens_out = defaultdict(int)
        self._cache_hits = defaultdict(int)
        self._cache_misses = defaultdict(int)
        self._start_time = time.time()

    def reset(self) -> None:
        """Reset all tracked metrics."""
        with self._lock:
            self._operations.clear()
            self._failures.clear()
            self._tokens_in.clear()
            self._tokens_out.clear()
            self._cache_hits.clear()
            self._cache_misses.clear()
            self._start_time = time.time()

    def record_usage(
        self,
        operation: str,
        model: str,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        latency_ms: float = 0.0,
        success: bool = True,
    ) -> None:
        """Convenience method to record usage matching common observability signatures."""
        self.record_call(
            operation=operation,
            model=model,
            input_tokens=prompt_tokens,
            output_tokens=completion_tokens,
            success=success,
            cache_hit=False,
        )

    def record_cache_hit(self, operation: str) -> None:
        """Record cache hit for an operation."""
        self.record_call(operation=operation, model="cached", cache_hit=True)

    def record_cache_miss(self, operation: str) -> None:
        """Record cache miss for an operation."""
        with self._lock:
            self._cache_misses[operation] += 1

    def record_call(
        self,
        operation: str,
        model: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        success: bool = True,
        cache_hit: bool = False,
    ) -> None:
        """Record an individual AI call with token counts and status."""
        with self._lock:
            if cache_hit:
                self._cache_hits[operation] += 1
                return

            self._cache_misses[operation] += 1
            self._operations[operation] += 1
            self._tokens_in[model] += max(0, input_tokens)
            self._tokens_out[model] += max(0, output_tokens)
            if not success:
                self._failures[operation] += 1

    def get_summary(self) -> Dict[str, Any]:
        """Generate summary report including estimated cost and cache efficiency."""
        with self._lock:
            total_cost = 0.0
            token_breakdown = {}

            all_models = set(self._tokens_in.keys()).union(self._tokens_out.keys())
            for model in all_models:
                in_tok = self._tokens_in[model]
                out_tok = self._tokens_out[model]
                rates = ESTIMATED_RATES_PER_1K_TOKENS.get(model, ESTIMATED_RATES_PER_1K_TOKENS["default"])
                model_cost = (in_tok / 1000.0) * rates["input"] + (out_tok / 1000.0) * rates["output"]
                total_cost += model_cost
                token_breakdown[model] = {
                    "input_tokens": in_tok,
                    "output_tokens": out_tok,
                    "total_tokens": in_tok + out_tok,
                    "estimated_cost_usd": round(model_cost, 5),
                }

            total_hits = sum(self._cache_hits.values())
            total_misses = sum(self._cache_misses.values())
            hit_rate = round(total_hits / (total_hits + total_misses), 2) if (total_hits + total_misses) > 0 else 0.0

            total_tokens = sum(m["total_tokens"] for m in token_breakdown.values())
            total_ops = sum(self._operations.values())

            return {
                "uptime_seconds": round(time.time() - self._start_time, 2),
                "total_estimated_cost_usd": round(total_cost, 4),
                "total_operations": total_ops,
                "total_calls": total_ops,
                "total_tokens": total_tokens,
                "total_failures": sum(self._failures.values()),
                "cache_hit_rate": hit_rate,
                "cache_hits": total_hits,
                "cache_misses": total_misses,
                "operations": dict(self._operations),
                "failures": dict(self._failures),
                "models": token_breakdown,
            }


# Global singleton instance
ai_cost_tracker = AICostTracker()
