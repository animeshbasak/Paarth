"""Text embedding with a local-first provider chain (Phase 5).

Order: **Ollama** (local, default) → **OpenRouter** (cloud, opt-in fallback).
This mirrors SuperAgent's "local first" ethos — no mandatory cloud call. The
cloud leg only fires when ``OPENROUTER_API_KEY`` is set *and* the local daemon
is unreachable.

``httpx`` is imported lazily so the default (non-vector) install never pulls
it in. Tests inject a fake ``embed_fn`` instead of hitting either backend.
"""

from __future__ import annotations

import os

Vector = list[float]

# nomic-embed-text emits 768-dim vectors, matching QdrantStore's default dim.
DEFAULT_OLLAMA_MODEL = "nomic-embed-text"
DEFAULT_OLLAMA_URL = "http://127.0.0.1:11434"
DEFAULT_OPENROUTER_URL = "https://openrouter.ai/api/v1"
DEFAULT_OPENROUTER_MODEL = "openai/text-embedding-3-small"


class EmbeddingError(RuntimeError):
    """Raised when no provider in the chain could produce an embedding."""


def embed(text: str, *, timeout: float = 15.0) -> Vector:
    """Embed ``text``, trying Ollama first then OpenRouter.

    Raises ``EmbeddingError`` if every available provider fails. Callers that
    must not fail (the write path) should treat this as best-effort and catch.
    """
    try:
        return _ollama_embed(text, timeout=timeout)
    except EmbeddingError as local_exc:
        if os.environ.get("OPENROUTER_API_KEY"):
            try:
                return _openrouter_embed(text, timeout=timeout)
            except EmbeddingError as cloud_exc:
                raise EmbeddingError(
                    f"ollama failed ({local_exc}); openrouter failed ({cloud_exc})"
                ) from cloud_exc
        raise


def _ollama_embed(text: str, *, timeout: float) -> Vector:
    httpx = _import_httpx()
    url = os.environ.get("SUPERAGENT_MEMORY_OLLAMA_URL", DEFAULT_OLLAMA_URL).rstrip("/")
    model = os.environ.get("SUPERAGENT_MEMORY_EMBED_MODEL", DEFAULT_OLLAMA_MODEL)
    try:
        resp = httpx.post(
            f"{url}/api/embeddings",
            json={"model": model, "prompt": text},
            timeout=timeout,
        )
        resp.raise_for_status()
        vec = resp.json().get("embedding")
    except Exception as exc:  # httpx errors, JSON errors, connection refused
        raise EmbeddingError(f"ollama embed failed: {exc}") from exc
    if not vec:
        raise EmbeddingError("ollama returned an empty embedding")
    return [float(x) for x in vec]


def _openrouter_embed(text: str, *, timeout: float) -> Vector:
    httpx = _import_httpx()
    key = os.environ["OPENROUTER_API_KEY"]
    url = os.environ.get("SUPERAGENT_MEMORY_OPENROUTER_URL", DEFAULT_OPENROUTER_URL).rstrip("/")
    model = os.environ.get("SUPERAGENT_MEMORY_CLOUD_EMBED_MODEL", DEFAULT_OPENROUTER_MODEL)
    try:
        resp = httpx.post(
            f"{url}/embeddings",
            headers={"Authorization": f"Bearer {key}"},
            json={"model": model, "input": text},
            timeout=timeout,
        )
        resp.raise_for_status()
        data = resp.json().get("data") or []
        vec = data[0]["embedding"] if data else None
    except Exception as exc:
        raise EmbeddingError(f"openrouter embed failed: {exc}") from exc
    if not vec:
        raise EmbeddingError("openrouter returned an empty embedding")
    return [float(x) for x in vec]


def _import_httpx():
    try:
        import httpx
    except ImportError as exc:  # pragma: no cover - exercised only without the extra
        raise EmbeddingError(
            "httpx not installed. Run: pip install -e '.[vector]'"
        ) from exc
    return httpx
