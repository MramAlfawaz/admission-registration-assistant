"""Experiment 4: grounded assistant (condition B) against the same model with no retrieval (condition A).

Condition A output is never shown to a student; it exists to measure why grounding is needed.
Its claims are judged against the whole set of approved passages in force on the question date.
"""
import re

from app.documents.version_selector import select_sources
from app.generation.answer_generator import LANGUAGE_NAMES
from app.models.prompts import fill, load_prompt
from app.pipeline.evaluate import _coverage, check_facts, match_form, SUPPORT
from app.retrieval.tokenize import tokenize
from app.safety.verifier import NO_INFO, number_tokens

REFUSAL = NO_INFO + ["لا اعلم", "لا أعلم", "لا املك", "غير متاكد", "تواصل مع", "يرجي التواصل", "i don't know",
                     "i do not know", "not sure", "please contact", "i cannot", "i can't"]


class NoRetrievalModel:
    """Ask the local model directly; nothing retrieved, no rules, no verification."""

    def __init__(self, client, prompts_dir="prompts", prompt_name="no_retrieval_v1"):
        self.client = client
        self.header, self.template = load_prompt(prompt_name, prompts_dir)

    def answer(self, question, language, as_of):
        try:
            out = self.client.generate_json(fill(self.template, language_name=LANGUAGE_NAMES[language],
                                                 as_of=as_of, question=question))
            return str(out.get("answer", "")).strip()
        except Exception as e:  # recorded, not hidden
            return f"[error: {type(e).__name__}]"


def _sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?؟؛])\s+", " ".join(text.split())) if len(s.strip()) > 2]


def is_refusal(text):
    norm = match_form(text)
    return not text.strip() or text.startswith("[error") or any(match_form(p) in norm for p in REFUSAL)


def label_free_claims(text, language, passages):
    """Label each sentence against its best-matching approved passage (by shared words)."""
    claims = []
    for s in _sentences(text):
        words = set(tokenize(s))
        best = max(passages, key=lambda p: len(words & p["tokens"]), default=None)
        if best is None or not words & best["tokens"]:
            label = "unsupported" if language == "ar" else "unverified"
        elif number_tokens(s) - number_tokens(best["text"]):
            label = "unsupported"
        elif language == "en":
            label = "unverified"
        else:
            label = "grounded" if _coverage(s, best["text"]) >= SUPPORT else "unsupported"
        claims.append({"text": s, "label": label, "best_passage": best["chunk_id"] if best else None})
    return claims


def in_force_passages(chunks, sources, as_of):
    allowed = {s["source_id"] for s in select_sources(sources, as_of)}
    return [{"chunk_id": c["chunk_id"], "text": c["text"], "tokens": set(tokenize(c["text"]))}
            for c in chunks if c["source_id"] in allowed]


def score_condition_a(item, text, passages):
    """Score one no-retrieval answer with the same fact checks as condition B."""
    refused = is_refusal(text)
    facts_ok, forbidden = check_facts({"answer": text, "conditions": [], "required_action": ""},
                                      item.get("must_contain", []), item.get("must_not_contain", []))
    answerable = item["expected_status"] == "ANSWERABLE"
    correct = (answerable and not refused and facts_ok and not forbidden) or (not answerable and refused)
    wrong_shown = not refused and (not answerable or not facts_ok or bool(forbidden))
    claims = [] if refused else label_free_claims(text, item["language"], passages)
    return {"id": item["id"], "language": item["language"], "expected_status": item["expected_status"],
            "question": item["question"], "answer": text, "refused": refused, "facts_ok": facts_ok,
            "forbidden": forbidden, "correct": correct, "wrong_answer_shown": wrong_shown, "claims": claims}


def summarize_condition(rows):
    def block(rs):
        claims = [c for r in rs for c in r["claims"]]
        judged = [c for c in claims if c["label"] != "unverified"]
        ans = [r for r in rs if r["expected_status"] == "ANSWERABLE"]
        non = [r for r in rs if r["expected_status"] != "ANSWERABLE"]
        rate = lambda a, b: round(a / b, 3) if b else None
        return {"n": len(rs), "correct": rate(sum(r["correct"] for r in rs), len(rs)),
                "answerable_correct": rate(sum(r["correct"] for r in ans), len(ans)),
                "refused_when_it_should": rate(sum(r["refused"] for r in non), len(non)),
                "wrong_answers_shown": sum(r["wrong_answer_shown"] for r in rs),
                "grounded_claim_rate": rate(sum(c["label"] == "grounded" for c in judged), len(judged)),
                "unsupported_claim_rate": rate(sum(c["label"] == "unsupported" for c in judged), len(judged)),
                "claims_unverified": len(claims) - len(judged)}
    return {"overall": block(rows), "ar": block([r for r in rows if r["language"] == "ar"]),
            "en": block([r for r in rows if r["language"] == "en"])}


def condition_b_summary(stored_rows):
    """The same metrics for the grounded assistant, from a saved evaluate-e2e results file."""
    rows = []
    for r in stored_rows:
        answered = r["response"]["status"] == "ANSWERABLE"
        claims = r["claims"]
        rows.append({"language": r["item"]["language"], "expected_status": r["item"]["expected_status"],
                     "refused": not answered, "correct": r["correct"],
                     "wrong_answer_shown": answered and not r["correct"], "claims": claims})
    return summarize_condition(rows)
