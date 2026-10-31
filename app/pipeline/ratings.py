"""Experiment 5: rating sheets for a documented team review, and the efficiency report.

Specialist time was not available, so a documented team review rates a fixed sample of real
answers (brief, Experiment 5 allows this substitute when the limitation is stated).
"""
import csv
import json
import random
import statistics
from pathlib import Path

CRITERIA = ["correctness", "completeness", "relevance", "clarity", "source_appropriateness"]
SHEET_FIELDS = ["id", "language", "question", "as_of", "status", "answer", "conditions", "required_action",
                "sources", "date_basis"] + CRITERIA + ["rater", "notes"]
NON_ANSWER_QUOTA = {"CLARIFICATION_REQUIRED": 2, "STAFF_REVIEW_REQUIRED": 2, "OUT_OF_SCOPE": 1, "INSUFFICIENT_EVIDENCE": 1}


def _rows(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))["rows"]


def sample_answers(result_files, n_answered=14, seed=42):
    """Pick a fixed sample: answered responses plus a quota of each non-answer status."""
    rows = [r for f in result_files for r in _rows(f)]
    rng = random.Random(seed)
    answered = [r for r in rows if r["response"]["status"] == "ANSWERABLE"]
    picked = rng.sample(answered, min(n_answered, len(answered)))
    for status, k in NON_ANSWER_QUOTA.items():
        pool = [r for r in rows if r["response"]["status"] == status]
        picked += rng.sample(pool, min(k, len(pool)))
    return picked


def write_rating_sheet(rows, sources_by_id, path):
    """Write the sheet raters fill in (1 to 5 per criterion); UTF-8 with BOM so Excel shows Arabic."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=SHEET_FIELDS)
        w.writeheader()
        for r in rows:
            resp = r["response"]
            sources = " | ".join(f"{sources_by_id.get(s['source_id'], {}).get('title', s['source_id'])}"
                                 f"{' p' + str(s['page']) if s.get('page') else ''}"
                                 f"{' ' + str(s['section']) if s.get('section') else ''}" for s in resp.get("sources", []))
            w.writerow({"id": r["id"], "language": r["item"]["language"], "question": r["item"]["question"],
                        "as_of": r["item"]["as_of"], "status": resp["status"], "answer": resp["answer"],
                        "conditions": " | ".join(resp.get("conditions", [])), "required_action": resp.get("required_action", ""),
                        "sources": sources, "date_basis": resp.get("date_basis", ""),
                        **{c: "" for c in CRITERIA}, "rater": "", "notes": ""})


def score_ratings(path):
    """Summarise a filled rating sheet: mean and distribution per criterion, overall and by group."""
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = [r for r in csv.DictReader(f)]
    rated = [r for r in rows if all((r.get(c) or "").strip() for c in CRITERIA)]

    def block(rs):
        out = {"n": len(rs)}
        for c in CRITERIA:
            vals = [int(r[c]) for r in rs]
            out[c] = {"mean": round(statistics.mean(vals), 2) if vals else None,
                      "distribution": {str(k): vals.count(k) for k in range(1, 6)}}
        return out
    return {"rows": len(rows), "rated": len(rated), "raters": sorted({r["rater"] for r in rated if r.get("rater")}),
            "overall": block(rated), "ar": block([r for r in rated if r["language"] == "ar"]),
            "en": block([r for r in rated if r["language"] == "en"]),
            "answered": block([r for r in rated if r["status"] == "ANSWERABLE"]),
            "non_answers": block([r for r in rated if r["status"] != "ANSWERABLE"]),
            "low_scores": [{"id": r["id"], **{c: r[c] for c in CRITERIA}, "notes": r.get("notes", "")}
                           for r in rated if any(int(r[c]) <= 2 for c in CRITERIA)]}


CLAIM_FIELDS = ["id", "language", "type", "auto_label", "claim", "evidence", "human_label", "note"]


def write_claim_review(result_file, chunk_text, path, arabic_sample=10, seed=42):
    """English claims the scorer could not judge, plus a sample of judged Arabic claims to check agreement."""
    rows = _rows(result_file)
    claims = []
    for r in rows:
        cited = [s["chunk_id"] for s in r["response"].get("sources", []) if s.get("chunk_id")]
        evidence = " || ".join(chunk_text.get(c, "")[:400] for c in cited)
        for c in r["claims"]:
            if c["type"] == "rule":
                continue
            claims.append({"id": r["id"], "language": r["item"]["language"], "type": c["type"],
                           "auto_label": c["label"], "claim": c["text"], "evidence": evidence,
                           "human_label": "", "note": ""})
    unverified = [c for c in claims if c["auto_label"] == "unverified"]
    judged = [c for c in claims if c["auto_label"] != "unverified"]
    picked = unverified + random.Random(seed).sample(judged, min(arabic_sample, len(judged)))
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CLAIM_FIELDS)
        w.writeheader()
        w.writerows(picked)
    return len(unverified), len(picked) - len(unverified)


def score_claim_review(path):
    """Human-verified grounded rate and agreement between automatic and human labels."""
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = [r for r in csv.DictReader(f) if (r.get("human_label") or "").strip()]
    norm = lambda v: v.strip().lower()
    english = [r for r in rows if r["auto_label"] == "unverified"]
    judged = [r for r in rows if r["auto_label"] != "unverified"]
    rate = lambda a, b: round(a / b, 3) if b else None
    return {"labelled": len(rows),
            "english_claims_labelled": len(english),
            "english_grounded_rate": rate(sum(norm(r["human_label"]) == "grounded" for r in english), len(english)),
            "auto_vs_human_checked": len(judged),
            "auto_vs_human_agreement": rate(sum(norm(r["human_label"]) == norm(r["auto_label"]) for r in judged), len(judged))}


def efficiency(uncached_file, self_service_files):
    """Response times from a run with no cached model calls, and self-service rates."""
    rows = _rows(uncached_file)
    def times(rs):
        t = sorted(r["seconds"] for r in rs)
        return {"n": len(t), "median": round(statistics.median(t), 1) if t else None,
                "p90": t[int(0.9 * (len(t) - 1))] if t else None}
    answered = [r for r in rows if r["response"]["status"] == "ANSWERABLE"]
    other = [r for r in rows if r["response"]["status"] != "ANSWERABLE"]
    out = {"timing_source": Path(uncached_file).name, "all": times(rows), "answered": times(answered),
           "non_answers": times(other), "self_service": {}}
    for f in self_service_files:
        rs = _rows(f)
        out["self_service"][Path(f).name] = round(sum(r["correct"] and r["response"]["status"] == "ANSWERABLE"
                                                      for r in rs) / len(rs), 3)
    return out
