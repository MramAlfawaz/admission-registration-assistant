from pathlib import Path

from app.intent.llm_classifier import LLMIntentClassifier

PROMPTS = Path(__file__).resolve().parent.parent / "prompts"


class FakeClient:
    def __init__(self, output=None, error=None):
        self.output, self.error, self.prompts = output, error, []

    def generate_json(self, prompt):
        self.prompts.append(prompt)
        if self.error:
            raise self.error
        return self.output


def test_valid_label_returned():
    client = FakeClient({"intent": "fees"})
    assert LLMIntentClassifier(client, prompts_dir=PROMPTS).classify("كم الرسوم؟") == "FEES"


def test_prompt_contains_question_and_labels():
    client = FakeClient({"intent": "FEES"})
    LLMIntentClassifier(client, prompts_dir=PROMPTS).classify("كم الرسوم؟")
    assert "كم الرسوم؟" in client.prompts[0] and "COURSE_WITHDRAWAL" in client.prompts[0]
    assert "{{" not in client.prompts[0]


def test_unknown_label_routed_out_of_scope():
    client = FakeClient({"intent": "PIZZA"})
    assert LLMIntentClassifier(client, prompts_dir=PROMPTS).classify("x") == "OUT_OF_SCOPE"


def test_invalid_json_routed_out_of_scope():
    client = FakeClient(error=ValueError("bad json"))
    assert LLMIntentClassifier(client, prompts_dir=PROMPTS).classify("x") == "OUT_OF_SCOPE"
