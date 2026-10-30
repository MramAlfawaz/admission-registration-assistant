"""Assemble the assistant from configuration."""
from pathlib import Path

from app.generation.answer_generator import AnswerGenerator
from app.generation.extractive import embedding_scorer
from app.intent.llm_classifier import LLMIntentClassifier
from app.models.llm_client import LLMClient
from app.pipeline.assistant import Assistant
from app.retrieval.factory import build_retriever
from app.rules.calendar_rules import CalendarStore
from app.rules.rule_engine import RuleEngine


def build_assistant(cfg):
    """Return an Assistant wired to the pinned local models and processed data."""
    client = LLMClient(cfg)
    retriever = build_retriever(cfg, with_embeddings=True)
    sources = {s["source_id"]: s for s in retriever.sources}
    store = CalendarStore.from_dir(Path(cfg.PROCESSED_DIR) / "calendar", retriever.sources)
    return Assistant(
        classifier=LLMIntentClassifier(client, prompts_dir=cfg.PROMPTS_DIR),
        retriever=retriever,
        engine=RuleEngine.from_file(cfg.RULES_FILE, store),
        generator=AnswerGenerator(client, cfg.PROMPTS_DIR, cfg.GEN_EVIDENCE_LIMIT, cfg.GEN_EVIDENCE_CHARS),
        sources_by_id=sources,
        top_k=cfg.TOP_K,
        scorer=embedding_scorer(retriever.embeddings.encoder),
        escalation_log=cfg.ESCALATION_LOG,
    )
