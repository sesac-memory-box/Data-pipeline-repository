#!/usr/bin/env python3
import argparse
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from data_pipeline.config import load_dotenv
from data_pipeline.embeddings import FastEmbedProvider


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Search Qdrant with the configured FastEmbed model.")
    parser.add_argument("--query", required=True, help="Search query text.")
    parser.add_argument("--top-k", type=int, default=5, help="Number of results to print.")
    parser.add_argument("--collection", default=None, help="Qdrant collection name.")
    return parser.parse_args()


def create_client():
    try:
        from qdrant_client import QdrantClient
    except ImportError as exc:
        raise RuntimeError("qdrant-client is required. Install dependencies with pip install -r requirements.txt") from exc

    return QdrantClient(
        url=os.getenv("QDRANT_URL", "http://localhost:6333"),
        api_key=os.getenv("QDRANT_API_KEY") or None,
    )


def search(client, collection_name: str, vector: list[float], top_k: int):
    if hasattr(client, "query_points"):
        result = client.query_points(
            collection_name=collection_name,
            query=vector,
            limit=top_k,
            with_payload=True,
        )
        return result.points
    return client.search(
        collection_name=collection_name,
        query_vector=vector,
        limit=top_k,
        with_payload=True,
    )


def preview(content: str, length: int = 180) -> str:
    text = " ".join((content or "").split())
    return text if len(text) <= length else text[:length] + "..."


def main() -> None:
    load_dotenv()
    args = parse_args()
    collection_name = (
        args.collection
        or os.getenv("QDRANT_COLLECTION")
        or os.getenv("QDRANT_COLLECTION_NAME")
        or "memory_box_contents"
    )
    provider = FastEmbedProvider()
    query_vector = provider.embed_texts([args.query])[0]
    client = create_client()

    try:
        results = search(client, collection_name, query_vector, args.top_k)
    except Exception as exc:
        raise RuntimeError(
            "Failed to search Qdrant "
            f"(url={os.getenv('QDRANT_URL', 'http://localhost:6333')}, collection={collection_name}). "
            "Check that Qdrant is running and the collection has been ingested."
        ) from exc

    print(f"collection={collection_name}")
    print(f"fastembed_model={provider.model_name}")
    for index, point in enumerate(results, start=1):
        payload = point.payload or {}
        score = getattr(point, "score", None)
        print(f"\n{index}. score={score}")
        print(f"title={payload.get('title', '')}")
        print(f"source={payload.get('source', payload.get('source_name', ''))}")
        print(f"content={preview(payload.get('content', ''))}")


if __name__ == "__main__":
    main()
