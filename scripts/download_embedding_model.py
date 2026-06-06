"""
Standalone script to download and initialize the local embedding model.

Used by development.sh to ensure the model is ready before starting servers.
Since Phase 3, this is deprecated as embeddings are namespace-specific and remote.
"""

from __future__ import annotations


def main() -> None:
    print("Local embedding model initialization is now skipped (using remote APIs).")


if __name__ == "__main__":
    main()
