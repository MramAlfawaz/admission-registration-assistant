"""Semantic retrieval with a pinned multilingual embedding model."""
import hashlib
import json
import logging
from pathlib import Path

import numpy as np

from app.models.llm_client import ModelUnavailableError, read_lock
from app.retrieval.bm25 import passage_text

log = logging.getLogger(__name__)


class SentenceTransformerEncoder:
    """Load the pinned model on first use (lazy initialisation)."""

    def __init__(self, model_name, revision):
        self.model_name, self.revision, self._model = model_name, revision, None

    def encode(self, texts):
        """Return L2-normalised embeddings for a list of texts."""
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            log.info("loading %s at revision %s", self.model_name, self.revision[:12])
            self._model = SentenceTransformer(self.model_name, revision=self.revision)
        return np.asarray(self._model.encode(texts, batch_size=16, normalize_embeddings=True,
                                             show_progress_bar=False), dtype=np.float32)


def pinned_encoder(cfg):
    """Return an encoder for the embedding model pinned in models.lock.

    Raises:
        ModelUnavailableError: if the model is not listed in models.lock.
    """
    revision = read_lock(cfg.MODELS_LOCK).get(cfg.EMBED_MODEL)
    if revision is None:
        raise ModelUnavailableError(f"{cfg.EMBED_MODEL} is not listed in {cfg.MODELS_LOCK}")
    return SentenceTransformerEncoder(cfg.EMBED_MODEL, revision)


class EmbeddingIndex:
    """Score chunks by cosine similarity, caching passage embeddings on disk."""

    def __init__(self, chunks, encoder, cache_dir, model_id):
        texts = ["passage: " + passage_text(c) for c in chunks]
        key = hashlib.sha256(json.dumps([model_id, texts], ensure_ascii=False).encode("utf-8")).hexdigest()
        path = Path(cache_dir) / f"passages_{key[:16]}.npy"
        if path.exists():
            self.matrix = np.load(path)
        else:
            log.info("embedding %d passages (cached afterwards)", len(texts))
            self.matrix = encoder.encode(texts)
            path.parent.mkdir(parents=True, exist_ok=True)
            np.save(path, self.matrix)
        self.encoder = encoder

    def scores(self, query):
        """Return one cosine similarity per chunk, in chunk order."""
        q = self.encoder.encode(["query: " + query])[0]
        return list(self.matrix @ q)
