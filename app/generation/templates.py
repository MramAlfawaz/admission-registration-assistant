"""Fixed bilingual texts for every non-answer status; the model never writes these."""

DATE_BASIS = {"ar": "بناءً على المعلومات المعتمدة المتاحة بتاريخ {as_of}.",
              "en": "Based on approved information as of {as_of}."}
CONTACT = {"ar": "يرجى التواصل مع عمادة القبول والتسجيل.",
           "en": "Please contact the Deanship of Admission and Registration."}
TEXTS = {
    "INSUFFICIENT_EVIDENCE": {
        "ar": "لا تتوفر لديّ معلومات معتمدة كافية للإجابة عن هذا السؤال بدقة.",
        "en": "I could not find approved information that answers this question reliably."},
    "CONFLICTING_EVIDENCE": {
        "ar": "الوثائق المعتمدة تذكر معلومات مختلفة في هذه النقطة، ولا يمكنني تحديد أيها المعمول به.",
        "en": "The approved documents give different information on this point, and I cannot determine which one applies."},
    "OUT_OF_SCOPE": {
        "ar": "هذا السؤال خارج نطاق شؤون القبول والتسجيل التي أستطيع الإجابة عنها.",
        "en": "This question is outside the admission and registration matters I can answer."},
}
OUT_OF_SCOPE_ACTION = {"ar": "يرجى التواصل مع الجهة المختصة في الجامعة.",
                      "en": "Please contact the relevant university office."}
QUOTE_INTRO = {"ar": "ورد في المصدر المعتمد:", "en": "The approved source states (in Arabic):"}
CLARIFY_OPTIONS = {
    "withdrawal_scope": [("course", {"ar": "مقرر واحد", "en": "One course"}),
                         ("semester", {"ar": "الفصل الدراسي كاملاً", "en": "The whole semester"}),
                         ("program", {"ar": "البرنامج", "en": "The program"})],
    "degree_level": [("phd", {"ar": "الدكتوراه", "en": "PhD"}), ("master", {"ar": "الماجستير", "en": "Master's"}),
                     ("diploma", {"ar": "الدبلوم العالي", "en": "Higher diploma"})],
}
CLARIFY = {
    "withdrawal_scope": {
        "ar": "هل تقصد الانسحاب من مقرر واحد، أم الاعتذار عن الفصل الدراسي كاملاً، أم الانسحاب من البرنامج؟",
        "en": "Do you mean dropping one course, withdrawing from the whole semester, or withdrawing from the program?"},
    "degree_level": {
        "ar": "هل سؤالك عن الدكتوراه، أم الماجستير، أم الدبلوم العالي؟",
        "en": "Is your question about the PhD, a master's degree, or a higher diploma?"},
}
