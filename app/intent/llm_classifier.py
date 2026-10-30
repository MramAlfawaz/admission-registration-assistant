"""Proposed intent classifier: the local model with a structured JSON prompt."""
import logging

from app.intent.taxonomy import INTENTS
from app.models.prompts import fill, load_prompt

log = logging.getLogger(__name__)


class LLMIntentClassifier:
    """Classify questions by asking the local model for one intent label."""

    def __init__(self, client, prompt_name="classify_intent_v1", prompts_dir="prompts"):
        self.client = client
        self.header, template = load_prompt(prompt_name, prompts_dir)
        intent_list = "\n".join(f"- {name}: {meaning}" for name, meaning in INTENTS.items())
        self.template = fill(template, intents=intent_list)

    def classify(self, question):
        """Return an intent label; unusable model output becomes OUT_OF_SCOPE.

        Args:
            question: the student question.

        Returns:
            An intent label from the taxonomy.
        """
        try:
            output = self.client.generate_json(fill(self.template, question=question))
        except ValueError as e:
            log.warning("unusable model output, routing as OUT_OF_SCOPE: %s", e)
            return "OUT_OF_SCOPE"
        intent = str(output.get("intent", "")).strip().upper()
        if intent not in INTENTS:
            log.warning("model returned unknown intent %r, routing as OUT_OF_SCOPE", intent)
            return "OUT_OF_SCOPE"
        return intent
