"""Measure an intent classifier against the labelled question set."""
import json
from pathlib import Path

from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score

from app.intent.taxonomy import INTENTS


def load_questions(path, split=None):
    """Read labelled questions, optionally keeping one split ("dev" or "test")."""
    rows = [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line]
    return [r for r in rows if split in (None, r["split"])]


def score(rows, predictions):
    """Return accuracy, macro-F1, per-intent metrics and a confusion matrix.

    Args:
        rows: labelled questions.
        predictions: predicted intents, in the same order.

    Returns:
        A dictionary of metrics.
    """
    gold = [r["intent"] for r in rows]
    labels = [i for i in INTENTS if i in set(gold) | set(predictions)]
    tp = sum(g == p == "OUT_OF_SCOPE" for g, p in zip(gold, predictions))
    fp = sum(p == "OUT_OF_SCOPE" != g for g, p in zip(gold, predictions))
    fn = sum(g == "OUT_OF_SCOPE" != p for g, p in zip(gold, predictions))
    oos_f1 = 2 * tp / (2 * tp + fp + fn) if tp else 0.0
    return {
        "n": len(rows),
        "accuracy": round(accuracy_score(gold, predictions), 4),
        "macro_f1": round(f1_score(gold, predictions, labels=labels, average="macro", zero_division=0), 4),
        "out_of_scope_f1": round(oos_f1, 4),
        "per_intent": classification_report(gold, predictions, labels=labels,
                                            output_dict=True, zero_division=0),
        "confusion": {"labels": labels,
                      "matrix": confusion_matrix(gold, predictions, labels=labels).tolist()},
    }


def evaluate(classify, rows):
    """Score a classifier overall and separately for each language.

    Args:
        classify: function mapping a question string to an intent.
        rows: labelled questions.

    Returns:
        A dict with "overall", one entry per language, and the errors.
    """
    predictions = [classify(r["question"]) for r in rows]
    result = {"overall": score(rows, predictions)}
    for lang in sorted({r["language"] for r in rows}):
        idx = [i for i, r in enumerate(rows) if r["language"] == lang]
        result[lang] = score([rows[i] for i in idx], [predictions[i] for i in idx])
    result["errors"] = [{"id": r["id"], "question": r["question"], "gold": r["intent"], "predicted": p}
                        for r, p in zip(rows, predictions) if r["intent"] != p]
    return result
