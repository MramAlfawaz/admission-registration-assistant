"""Proposed intent classifier: the local model with a structured JSON prompt."""
import difflib
import logging

import requests

from app.intent.taxonomy import INTENTS
from app.models.prompts import fill, load_prompt

log = logging.getLogger(__name__)


class LLMIntentClassifier:
    """Classify questions by asking the local model for one intent label."""

    def __init__(self, client, prompt_name="classify_intent_v1", prompts_dir="prompts", fallback=None):
        self.client, self.fallback, self.last_source = client, fallback, None
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
        self.last_source = "model"
        try:
            output = self.client.generate_json(fill(self.template, question=question))
        except requests.RequestException as e:
            # Timeout or model unreachable. The application passes the keyword baseline (Experiment 1)
            # so the student still gets an answer; the evaluation commands pass none and stop instead.
            if self.fallback is None:
                raise
            log.warning("model unavailable for intent (%s); using the keyword classifier", type(e).__name__)
            self.last_source = "keyword fallback"
            return self.fallback(question)
        except ValueError as e:
            log.warning("unusable model output, routing as OUT_OF_SCOPE: %s", e)
            return "OUT_OF_SCOPE"
        intent = str(output.get("intent", "")).strip().upper()
        if intent not in INTENTS:
            # A misspelled label (v1: SEMMESTER_WITHDRAWAL) is mapped to the nearest valid one.
            close = difflib.get_close_matches(intent, list(INTENTS), n=1, cutoff=0.9)
            if close:
                log.warning("model returned %r, read as %s", intent, close[0])
                return close[0]
            log.warning("model returned unknown intent %r, routing as OUT_OF_SCOPE", intent)
            return "OUT_OF_SCOPE"
        return intent
