"""
Embedding Service — singleton for managing local embedding model lifecycle.

Downloads the model to a project-local storage path on first run, then loads
from disk on subsequent runs — avoiding repeated online downloads.

When running on CPU, applies PyTorch thread-tuning and optional dynamic
quantization for faster inference.
"""

from __future__ import annotations

import os
from pathlib import Path

import torch
from core.logging import get_logger

logger = get_logger("embedding_service")

MODEL_NAME = "Qwen/Qwen3-Embedding-0.6B"
LOCAL_MODEL_DIR = Path("./storage/models/qwen-embedding-0.6B")

_CPU_BATCH_SIZE = 64


def _optimize_cpu_threading() -> None:
    """Pin PyTorch to use all available CPU cores for matrix ops."""
    n_cores = os.cpu_count() or 4
    torch.set_num_threads(n_cores)
    os.environ.setdefault("OMP_NUM_THREADS", str(n_cores))
    os.environ.setdefault("MKL_NUM_THREADS", str(n_cores))
    os.environ.setdefault("OPENBLAS_NUM_THREADS", str(n_cores))


def _try_quantize(model):  # type: ignore[no-untyped-def]
    """Apply dynamic int8 quantization to linear layers for CPU speedup."""
    try:
        quantized = torch.quantization.quantize_dynamic(
            model,
            {torch.nn.Linear},
            dtype=torch.qint8,
        )
        logger.info("cpu_int8_quantization_applied")
        return quantized
    except Exception:
        logger.info("cpu_int8_quantization_skipped")
        return model


class EmbeddingService:
    """Singleton service for the local sentence-transformers embedding model.

    Stores the downloaded model under ``LOCAL_MODEL_DIR`` so that subsequent
    starts skip the HuggingFace download entirely.

    On CPU the model is dynamically quantized to int8 (Linear layers) and
    PyTorch threading is tuned to the available core count.
    """

    _instance: EmbeddingService | None = None
    _model = None
    _device: str = "cpu"

    def __new__(cls) -> EmbeddingService:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @staticmethod
    def _model_exists_locally() -> bool:
        """Check whether the model files already exist on disk."""
        return LOCAL_MODEL_DIR.is_dir() and any(LOCAL_MODEL_DIR.iterdir())

    def initialize(self) -> None:
        """Load the model into memory, downloading first if needed."""
        if self._model is not None:
            logger.info("embedding_model_already_initialized")
            return

        from sentence_transformers import SentenceTransformer

        if torch.cuda.is_available():
            self._device = "cuda"
        else:
            self._device = "cpu"
            _optimize_cpu_threading()

        logger.info("embedding_model_device", device=self._device)

        if self._model_exists_locally():
            logger.info("loading_embedding_model_from_disk", path=str(LOCAL_MODEL_DIR))
            model = SentenceTransformer(str(LOCAL_MODEL_DIR), device=self._device)
        else:
            logger.info("downloading_embedding_model", model=MODEL_NAME)
            LOCAL_MODEL_DIR.parent.mkdir(parents=True, exist_ok=True)
            model = SentenceTransformer(MODEL_NAME, device=self._device)
            logger.info("saving_embedding_model_to_disk", path=str(LOCAL_MODEL_DIR))
            model.save(str(LOCAL_MODEL_DIR))

        if self._device == "cpu":
            model = _try_quantize(model)

        self._model = model
        logger.info("embedding_model_initialized")

    @property
    def model(self):
        if self._model is None:
            raise RuntimeError(
                "EmbeddingService not initialized. "
                "Call EmbeddingService().initialize() first."
            )
        return self._model

    @property
    def is_initialized(self) -> bool:
        return self._model is not None

    def embed_text(self, text: str, is_query: bool = False) -> list[float]:
        """Embed a single piece of text."""
        prompt_name = "query" if is_query else None
        embedding = self.model.encode(
            text,
            prompt_name=prompt_name,
            show_progress_bar=False,
        )
        return embedding.tolist()

    def embed_batch(
        self, texts: list[str], is_query: bool = False
    ) -> list[list[float]]:
        """Embed a list of texts, optionally using CPU-tuned batch size."""
        if not texts:
            return []
        prompt_name = "query" if is_query else None
        embeddings = self.model.encode(
            texts,
            prompt_name=prompt_name,
            batch_size=_CPU_BATCH_SIZE if self._device == "cpu" else 32,
            show_progress_bar=False,
        )
        return embeddings.tolist()
