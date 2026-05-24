"""
Standalone script to download and initialize the local embedding model.

Used by development.sh to ensure the model is ready before starting servers.

Usage:
    python -m scripts.download_embedding_model
"""

from __future__ import annotations


def main() -> None:
    print("Initializing local embedding model (Qwen/Qwen3-Embedding-0.6B)...")
    from core.embedding_service import EmbeddingService

    service = EmbeddingService()
    service.initialize()
    print("Embedding model is ready.")


if __name__ == "__main__":
    main()
