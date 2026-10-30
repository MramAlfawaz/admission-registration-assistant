import datetime as dt
import json
import tempfile
from pathlib import Path

import numpy as np
import pytest

from app.documents.version_selector import in_force
from app.intent.language import detect_language
from app.retrieval.bm25 import BM25Index
from app.retrieval.embeddings import EmbeddingIndex
from app.retrieval.evaluate import evaluate, load_gold, score_question
from app.retrieval.hybrid import reciprocal_rank_fusion
from app.retrieval.retriever import Retriever
from app.retrieval.tokenize import tokenize

ROOT = Path(__file__).resolve().parent.parent
SOURCES = [
    {"source_id": "REG-1", "effective_from": "2024-01-01", "effective_to": None},
    {"source_id": "GUIDE-OLD", "effective_from": "2025-01-01", "effective_to": "2025-12-31"},
    {"source_id": "GUIDE-NEW", "effective_from": "2026-01-01", "effective_to": None},
]
CHUNKS = [
    {"chunk_id": "REG-1#001", "source_id": "REG-1", "section": "الحرمان",
     "text": "يحرم الطالب من دخول الاختبار النهائي إذا قلت نسبة حضوره عن 75%"},
    {"chunk_id": "REG-1#002", "source_id": "REG-1", "section": "التأجيل",
     "text": "يتقدم الطالب بطلب التأجيل قبل نهاية الأسبوع الأول من الدراسة"},
    {"chunk_id": "GUIDE-OLD#001", "source_id": "GUIDE-OLD", "section": "علم الجريمة",
     "text": "مدة الدراسة في ماجستير علم الجريمة عامان دراسيان"},
    {"chunk_id": "GUIDE-NEW#001", "source_id": "GUIDE-NEW", "section": "علم الجريمة",
     "text": "مدة الدراسة في ماجستير علم الجريمة عام دراسي واحد"},
    # filler passages: BM25 gives zero weight to a word found in half the corpus,
    # so a realistic test corpus needs more than four passages
    {"chunk_id": "REG-1#003", "source_id": "REG-1", "section": "الرسوم",
     "text": "تسدد الرسوم الدراسية في بداية كل فصل دراسي"},
    {"chunk_id": "REG-1#004", "source_id": "REG-1", "section": "الاختبار الشامل",
     "text": "يعقد الاختبار الشامل في الأسبوع الرابع من الفصل الأول"},
    {"chunk_id": "REG-1#005", "source_id": "REG-1", "section": "مراتب الشرف",
     "text": "تمنح مرتبة الشرف الأولى للطالب الحاصل على معدل مرتفع"},
    {"chunk_id": "REG-1#006", "source_id": "REG-1", "section": "الوثائق",
     "text": "الوثائق المطلوبة الهوية الوطنية وجواز السفر والسجل الأكاديمي"},
]


class FakeEncoder:
    """Bag-of-tokens vectors so semantic search can be tested without a model."""

    def __init__(self):
        self.vocab, self.calls = {}, 0

    def encode(self, texts):
        self.calls += 1
        vectors = []
        for t in texts:
            v = np.zeros(64, dtype=np.float32)
            for tok in tokenize(t):
                v[self.vocab.setdefault(tok, len(self.vocab) % 64)] += 1
            vectors.append(v / (np.linalg.norm(v) or 1))
        return np.stack(vectors)


def test_tokenize_strips_articles_and_stopwords():
    assert tokenize("هل والاختبارات في الفصل؟") == ["اختبارات", "فصل"]
    assert tokenize("What is the GPA?") == ["gpa"]


def test_bm25_finds_attendance_rule():
    r = Retriever(CHUNKS, SOURCES, bm25=BM25Index(CHUNKS))
    assert r.search("كم نسبة الحضور لدخول الاختبار النهائي؟", "2026-10-14", "bm25", k=1)[0]["chunk_id"] == "REG-1#001"


def test_only_versions_in_force_are_searched():
    r = Retriever(CHUNKS, SOURCES, bm25=BM25Index(CHUNKS))
    now = [c["chunk_id"] for c in r.search("مدة ماجستير علم الجريمة", "2026-10-14", "bm25", k=4)]
    past = [c["chunk_id"] for c in r.search("مدة ماجستير علم الجريمة", "2025-06-01", "bm25", k=4)]
    assert "GUIDE-NEW#001" in now and "GUIDE-OLD#001" not in now
    assert "GUIDE-OLD#001" in past and "GUIDE-NEW#001" not in past


def test_reciprocal_rank_fusion_order():
    assert reciprocal_rank_fusion([[1, 2, 3], [3, 1]], k=60) == [1, 3, 2]


def test_hybrid_uses_both_indexes():
    tmp = tempfile.mkdtemp()
    emb = EmbeddingIndex(CHUNKS, FakeEncoder(), tmp, "fake")
    r = Retriever(CHUNKS, SOURCES, bm25=BM25Index(CHUNKS), embeddings=emb)
    top = r.search("طلب التأجيل", "2026-10-14", "hybrid", k=1)
    assert top[0]["chunk_id"] == "REG-1#002"


def test_passage_embeddings_are_cached():
    tmp = tempfile.mkdtemp()
    encoder = FakeEncoder()
    EmbeddingIndex(CHUNKS, encoder, tmp, "fake")
    EmbeddingIndex(CHUNKS, encoder, tmp, "fake")
    assert encoder.calls == 1


def test_recall_counts_evidence_groups():
    gold = {"evidence": [["CAL#006"], ["HB#010", "HB#011"]]}
    m = score_question(gold, ["HB#011", "X", "Y", "Z", "W", "CAL#006"])
    assert m["recall@5"] == 0.5 and m["recall@10"] == 1.0 and m["precision@5"] == 0.2


def test_evaluate_reports_failures_and_no_leaks():
    r = Retriever(CHUNKS, SOURCES, bm25=BM25Index(CHUNKS))
    gold = [{"id": "G1", "question": "مدة ماجستير علم الجريمة", "language": "ar",
             "as_of": "2026-10-14", "evidence": [["GUIDE-NEW#001"]]},
            {"id": "G2", "question": "parking", "language": "en",
             "as_of": "2026-10-14", "evidence": [["REG-1#002"]]}]
    result = evaluate(r, gold, "bm25")
    assert result["version_leaks"] == 0
    assert result["ar"]["recall@5"] == 1.0
    assert [f["id"] for f in result["failures"]] == ["G2"]


def test_gold_set_integrity():
    rows = load_gold(ROOT / "evaluation" / "retrieval" / "gold.jsonl")
    sources = {s["source_id"]: s for s in json.loads((ROOT / "data" / "sources.json").read_text(encoding="utf-8"))}
    assert len({r["id"] for r in rows}) == len(rows) >= 60
    for r in rows:
        dt.date.fromisoformat(r["as_of"])
        assert detect_language(r["question"]) == r["language"]
        for group in r["evidence"]:
            for cid in group:
                assert in_force(sources[cid.split("#")[0]], r["as_of"]), (r["id"], cid)


def test_gold_chunk_ids_exist():
    path = ROOT / "data" / "processed" / "chunks.jsonl"
    if not path.exists():
        pytest.skip("run 'python cli.py ingest' first")
    ids = {json.loads(line)["chunk_id"] for line in path.read_text(encoding="utf-8").splitlines() if line}
    for r in load_gold(ROOT / "evaluation" / "retrieval" / "gold.jsonl"):
        for group in r["evidence"]:
            assert set(group) <= ids, r["id"]
