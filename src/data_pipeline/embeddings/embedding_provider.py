import hashlib
import json
import math
import os
import urllib.request
from typing import Protocol


class EmbeddingProvider(Protocol):
    dimension: int

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        ...


class HashEmbeddingProvider:
    def __init__(self, dimension: int = 384) -> None:
        self.dimension = dimension

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimension
        tokens = text.split() or [text]
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimension
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign

        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]


class HttpEmbeddingProvider:
    def __init__(self, url: str, dimension: int = 384) -> None:
        if not url:
            raise ValueError("EMBEDDING_API_URL is required when EMBEDDING_PROVIDER=http")
        self.url = url
        self.dimension = dimension

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        body = json.dumps({"texts": texts}).encode("utf-8")
        request = urllib.request.Request(
            self.url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = json.loads(response.read().decode("utf-8"))
        embeddings = payload.get("embeddings")
        if not isinstance(embeddings, list):
            raise ValueError("Embedding API response must contain an embeddings list")
        return embeddings


def create_embedding_provider() -> EmbeddingProvider:
    provider = os.getenv("EMBEDDING_PROVIDER", "hash").lower()
    dimension = int(os.getenv("EMBEDDING_DIM", os.getenv("QDRANT_VECTOR_SIZE", "384")))

    if provider == "hash":
        return HashEmbeddingProvider(dimension=dimension)
    if provider == "http":
        return HttpEmbeddingProvider(os.getenv("EMBEDDING_API_URL", ""), dimension=dimension)
    raise ValueError(f"Unsupported EMBEDDING_PROVIDER: {provider}")
