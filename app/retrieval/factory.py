"""Build a retriever from the processed chunks and the source registry."""
import json
from pathlib import Path

from app.retrieval.bm25 import BM25Index
from app.retrieval.retriever import Retriever


def load_chunks(cfg):
    """Read data/processed/chunks.jsonl, built by 'python cli.py ingest'."""
    path = Path(cfg.PROCESSED_DIR) / "chunks.jsonl"
    if not path.exists():
        raise FileNotFoundError(f"{path} not found; run 'python cli.py ingest' first")
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def build_retriever(cfg, with_embeddings=True):
    """Return a Retriever with BM25 and, optionally, the pinned embedding model."""
    from app.retrieval.embeddings import EmbeddingIndex, pinned_encoder

    chunks = load_chunks(cfg)
    sources = json.loads(Path(cfg.SOURCES_FILE).read_text(encoding="utf-8"))
    embeddings = None
    if with_embeddings:
        encoder = pinned_encoder(cfg)
        embeddings = EmbeddingIndex(chunks, encoder, Path(cfg.PROCESSED_DIR) / "embeddings",
                                    f"{encoder.model_name}@{encoder.revision}")
    return Retriever(chunks, sources, bm25=BM25Index(chunks), embeddings=embeddings,
                     candidates=cfg.RETRIEVAL_CANDIDATES, rrf_k=cfg.RRF_K)
