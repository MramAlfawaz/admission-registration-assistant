"""HTTP routes: the student page, a JSON API and a health check.

The interface is the only place that reads the clock: in production the date a question is
about is today, and it is passed to the pipeline as an input (brief, Section 6.3). The question
text is never logged (docs/data-handling.md).
"""
import datetime as dt
import logging
import re
import time

from flask import Blueprint, current_app, jsonify, render_template, request

bp = Blueprint("main", __name__)
log = logging.getLogger(__name__)
MAX_QUESTION = 1000

STATUS_LABELS = {
    "ANSWERABLE": {"ar": "إجابة من المصادر المعتمدة", "en": "Answer from approved sources"},
    "CLARIFICATION_REQUIRED": {"ar": "نحتاج توضيحاً منك", "en": "Clarification needed"},
    "INSUFFICIENT_EVIDENCE": {"ar": "لا تتوفر معلومات معتمدة كافية", "en": "Not enough approved information"},
    "CONFLICTING_EVIDENCE": {"ar": "المصادر المعتمدة متعارضة", "en": "Approved sources disagree"},
    "OUT_OF_SCOPE": {"ar": "خارج نطاق القبول والتسجيل", "en": "Outside admission and registration"},
    "STAFF_REVIEW_REQUIRED": {"ar": "يحتاج إلى مراجعة الموظف المختص", "en": "Needs review by staff"},
}
UI = {
    "ar": {"title": "مساعد القبول والتسجيل", "subtitle": "جامعة نايف العربية للعلوم الأمنية",
           "question": "سؤالك", "date": "تاريخ السؤال", "ask": "اسأل", "busy": "جارٍ البحث…", "open_source": "فتح المستند الرسمي",
           "busy_note": "جارٍ البحث في المصادر المعتمدة. قد يستغرق ذلك بضع دقائق؛ يرجى عدم إعادة الإرسال.", "sources": "المصادر",
           "conditions": "الشروط", "action": "المطلوب منك", "confirmed": "ما يمكن تأكيده",
           "next_step": "الخطوة التالية", "generated": "أنشئت الإجابة في", "page": "صفحة",
           "notice": "هذه المساعدة لا تتخذ قرارات القبول أو التسجيل. القرار للجهة المختصة.",
           "error": "تعذر تجهيز الإجابة الآن. حاول مرة أخرى بعد قليل، أو تواصل مع عمادة القبول والتسجيل.",
           "empty": "اكتب سؤالك أولاً.", "too_long": "السؤال طويل جداً؛ اختصره من فضلك.",
           "placeholder": "مثال: متى آخر موعد للاعتذار عن الفصل الدراسي الأول؟"},
    "en": {"title": "Admission and Registration Assistant", "subtitle": "Naif Arab University for Security Sciences",
           "question": "Your question", "date": "Date the question is about", "ask": "Ask", "busy": "Searching…", "open_source": "Open the official document",
           "busy_note": "Searching the approved sources. This can take a few minutes; please do not send again.", "sources": "Sources",
           "conditions": "Conditions", "action": "What you need to do", "confirmed": "What can be confirmed",
           "next_step": "Next step", "generated": "Answer generated on", "page": "page",
           "notice": "This assistant does not make admission or registration decisions; the responsible office does.",
           "error": "The answer could not be prepared right now. Please try again shortly, or contact the Deanship of Admission and Registration.",
           "empty": "Please type your question first.", "too_long": "The question is too long; please shorten it.",
           "placeholder": "Example: When is the semester withdrawal deadline?"},
}


def get_assistant():
    """Return the assistant, built once on first use (loading models takes a few seconds)."""
    ext = current_app.extensions
    if "assistant" not in ext:
        from app.pipeline.factory import build_assistant
        ext["assistant"] = build_assistant(ext["config_class"])
    return ext["assistant"]


def _page_language(text):
    from app.intent.language import answer_language
    return answer_language(text) if text.strip() else "ar"


def _source_view(assistant, sources, language):
    """One line per document, with its pages and sections joined (step 12 test: the same document was
    listed once per passage)."""
    by_id = getattr(assistant, "sources_by_id", {}) or {}
    grouped = {}
    for s in sources:
        meta = by_id.get(s["source_id"], {})
        entry = grouped.setdefault(s["source_id"], {"title": meta.get("title", s["source_id"]), "id": s["source_id"],
                                                   "url": meta.get("url"), "places": []})
        # User feedback (step 13e): "the sources give only the document name". The title links to the
        # official document, at the first cited page for a PDF.
        if entry["url"] and s.get("page") and entry["url"].lower().endswith(".pdf") and "#" not in entry["url"]:
            entry["url"] = f"{entry['url']}#page={s['page']}"
        where = []
        if s.get("page"):
            where.append(f"{UI[language]['page']} {s['page']}")
        if s.get("section"):
            where.append(_section(str(s["section"]), language))
        place = " - ".join(where)
        if place and place not in entry["places"]:
            entry["places"].append(place)
    sep = "، " if language == "ar" else "; "
    return [{"title": e["title"], "id": e["id"], "url": e["url"], "where": sep.join(e["places"])} for e in grouped.values()]


def _section(section, language):
    """Calendar rows are stored as "row 6" or "rows 6 and 18"; show them in the answer's language."""
    if language != "ar":
        return section
    m = re.fullmatch(r"rows? (\d+)(?: and (\d+))?", section)
    if not m:
        return section
    return f"الصف {m.group(1)}" + (f" والصف {m.group(2)}" if m.group(2) else "") + " في التقويم"


def _answer(question, as_of, clarify):
    log.info("question received (as_of=%s, %d characters)", as_of, len(question))
    assistant = get_assistant()
    start = time.perf_counter()
    response = assistant.answer(question, as_of, clarification=clarify or None)
    log.info("answered: status=%s intent=%s mode=%s %.1fs", response["status"], response.get("intent"),
             response.get("_trace", {}).get("mode"), time.perf_counter() - start)
    return assistant, response


def _read_inputs(source):
    question = (source.get("question") or "").strip()
    as_of = (source.get("as_of") or "").strip() or dt.date.today().isoformat()
    dt.date.fromisoformat(as_of)  # raises ValueError for a bad date
    return question, as_of


@bp.get("/health")
def health():
    """Return service status."""
    return jsonify({"results": [{"status": "ok"}], "errors": []})


@bp.get("/")
def index():
    language = request.args.get("lang", "ar") if request.args.get("lang") in ("ar", "en") else "ar"
    return render_template("index.html", ui=UI[language], lang=language, today=dt.date.today().isoformat(),
                           question="", as_of=dt.date.today().isoformat(), result=None, error=None)


@bp.post("/ask")
def ask():
    form = request.form
    clarify = {k[len("clarify_"):]: v for k, v in form.items() if k.startswith("clarify_") and v}
    try:
        question, as_of = _read_inputs(form)
    except ValueError:
        question, as_of = (form.get("question") or "").strip(), dt.date.today().isoformat()
    language = _page_language(question)
    page = dict(ui=UI[language], lang=language, today=dt.date.today().isoformat(), question=question, as_of=as_of)
    if not question:
        return render_template("index.html", **page, result=None, error=UI[language]["empty"]), 400
    if len(question) > MAX_QUESTION:
        return render_template("index.html", **page, result=None, error=UI[language]["too_long"]), 400
    try:
        assistant, response = _answer(question, as_of, clarify)
    except Exception:
        log.exception("answer failed")  # details go to the log; the student sees a readable message
        return render_template("index.html", **page, result=None, error=UI[language]["error"]), 503
    rl = response["language"]
    result = {"r": response, "rl": rl, "ui": UI[rl], "status_label": STATUS_LABELS[response["status"]][rl],
              "sources": _source_view(assistant, response.get("sources", []), rl), "clarify": clarify}
    return render_template("index.html", **page, result=result, error=None)


@bp.post("/api/ask")
def api_ask():
    """JSON API: {"question": "...", "as_of": "YYYY-MM-DD" (optional), "clarify": {...} (optional)}."""
    body = request.get_json(silent=True) or {}
    try:
        question, as_of = _read_inputs(body)
    except ValueError:
        return jsonify({"results": [], "errors": ["as_of must be a date in YYYY-MM-DD form"]}), 400
    if not question or len(question) > MAX_QUESTION:
        return jsonify({"results": [], "errors": [f"question must be 1 to {MAX_QUESTION} characters"]}), 400
    try:
        _, response = _answer(question, as_of, body.get("clarify") or {})
    except Exception:
        log.exception("answer failed")
        return jsonify({"results": [], "errors": ["the assistant is temporarily unavailable"]}), 503
    return jsonify({"results": [{k: v for k, v in response.items() if not k.startswith("_")}], "errors": []})
