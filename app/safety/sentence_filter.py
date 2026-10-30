"""Keep only model sentences that are grounded in the evidence and about the asked situation.

The verifier checks invented values (numbers, weekdays, scripts). Real runs showed a
second failure: true facts from a different situation, glossary terms copied into
the answer, echoed prompt text and speculation. These checks run per sentence, so
one bad sentence no longer spoils, or slips through with, a good one.
"""
import re
from pathlib import Path

from app.documents.normalize import normalize_for_search
from app.retrieval.tokenize import tokenize
from app.safety.verifier import verify_text

OTHER_SITUATION = {
    "SEMESTER_WITHDRAWAL": ["الانسحاب من البرنامج", "الانسحاب من الجامعه", "withdraw from the program",
                            "withdrawal from the program", "withdraw from the university", "تكميلي",
                            "supplementary", "تاجيل", "postpon"],
    "PROGRAM_WITHDRAWAL": ["الاعتذار عن", "اعتذار", "withdraw from the semester", "semester withdrawal",
                           "تاجيل", "postpon"],
    "POSTPONEMENT": ["اعتذار", "انسحاب", "withdraw"],
    "REENROLLMENT": ["اعتذار", "تاجيل", "انسحاب", "withdraw", "postpon", "مرتبه الشرف", "honour", "honor"],
    "ATTENDANCE": ["اعتذار", "تاجيل", "انسحاب", "withdraw", "postpon"],
}
SPECULATION = ["قد لا", "ربما", "من المحتمل", "قد يكون", "may not", "might", "possibly", "perhaps"]
PROMPT_ECHO = ["only if the evidence", "conditions written in the evidence", "your 1 to 3 sentences",
               "what the student should do", "من الادله", "النص الاول", "النقطه 1 من النص",
               "according to the evidence", "passage"]
# Harmless openings are trimmed, not treated as faults.
PREAMBLE = re.compile(r"^(بناءً على|بناء على|استناداً إلى|استنادا إلى|based on|according to)[^،,:]{0,40}[،,:]\s*", re.I)
TERM_ID = re.compile(r"\b\d{4}-T[12]\b")


def load_glossary(path):
    """Return (arabic, english) term pairs from the glossary prompt file."""
    pairs = []
    for line in Path(path).read_text(encoding="utf-8").split("---")[-1].splitlines():
        if "=" in line:
            ar, en = (x.strip() for x in line.split("=", 1))
            pairs.append((ar, en))
    return pairs


def split_sentences(text):
    """Split model text into sentences, trimming harmless openings."""
    parts = re.split(r"(?<=[.!?؟؛])\s+", " ".join(text.split()))
    sentences = [PREAMBLE.sub("", p.strip()) for p in parts]
    return [p[0].upper() + p[1:] if p[:1].isascii() else p for p in sentences if len(p) > 2]


def sentence_issues(sentence, language, evidence_texts, rule_outputs, rule_texts, intent, glossary, question=""):
    """Return why a sentence must be dropped; an empty list keeps it."""
    issues = verify_text(sentence, language, list(evidence_texts) + list(rule_texts), rule_outputs, question)
    norm = normalize_for_search(sentence)
    evidence_norm = normalize_for_search(" ".join(list(evidence_texts) + list(rule_texts)))
    if TERM_ID.search(sentence):
        issues.append(f"internal term id: {TERM_ID.search(sentence).group(0)}")
    if any(p in norm for p in SPECULATION):
        issues.append("speculation")
    if any(p in norm for p in PROMPT_ECHO):
        issues.append("echoes prompt text")
    for phrase in OTHER_SITUATION.get(intent, []):
        if phrase in norm:
            issues.append(f"other situation: {phrase}")
            break
    evidence_tokens = set(tokenize(" ".join(list(evidence_texts) + list(rule_texts) + [question])))
    for ar, en in glossary:
        ar_n = normalize_for_search(ar)
        mentioned = ar_n in norm or set(tokenize(ar)) <= set(tokenize(sentence)) or en.lower() in sentence.lower()
        if mentioned and not set(tokenize(ar)) <= evidence_tokens:
            issues.append(f"term not in evidence: {ar}")
            break
    tokens = set(tokenize(sentence))
    for rt in rule_texts:
        rule_tokens = set(tokenize(rt))
        if tokens and len(tokens & rule_tokens) / len(tokens) >= 0.6:
            issues.append("repeats the fixed sentence")
            break
    if language == "ar" and len(tokens) >= 4:
        if len(tokens & evidence_tokens) / len(tokens) < 0.5:
            issues.append("mostly words not in evidence")
    return issues


def filter_sentences(text, **context):
    """Return (kept sentences, dropped [(sentence, issues)]) for a block of model text."""
    kept, dropped = [], []
    for s in split_sentences(text):
        issues = sentence_issues(s, **context)
        (dropped.append((s, issues)) if issues else kept.append(s))
    return kept, dropped


def filter_items(items, min_words=4, **context):
    """Filter short list items such as conditions: real sentences only, each grounded."""
    kept = []
    for item in items:
        if len(item.split()) >= min_words and not sentence_issues(item, **context):
            kept.append(item)
    return kept
