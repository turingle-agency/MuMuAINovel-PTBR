"""Embedder preguiçoso: o modelo ONNX só é carregado na primeira chamada."""
from __future__ import annotations

import threading
from typing import Protocol

import numpy as np


class Embedder(Protocol):
    def encode(self, texts: str | list[str]) -> np.ndarray: ...


_embedder: Embedder | None = None
_embedder_lock = threading.Lock()


class _LazyOnnxEmbedder:
    def __init__(self) -> None:
        self._model = None
        self._lock = threading.Lock()

    def encode(self, texts: str | list[str]) -> np.ndarray:
        if self._model is None:
            with self._lock:
                if self._model is None:
                    from app.services.onnx_embedding import OnnxEmbeddingModel

                    self._model = OnnxEmbeddingModel()
        return self._model.encode(texts)


def get_embedder() -> Embedder:
    global _embedder
    if _embedder is None:
        with _embedder_lock:
            if _embedder is None:
                _embedder = _LazyOnnxEmbedder()
    return _embedder


def set_embedder_for_tests(embedder: Embedder | None) -> None:
    global _embedder
    _embedder = embedder
