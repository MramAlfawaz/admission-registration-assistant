import json
import tempfile
from pathlib import Path

import pytest

from app.models.llm_client import LLMClient, ModelUnavailableError, cache_key

DIGEST = "357c53fb659c" + "a" * 52


class FakeTransport:
    """Stand-in for Ollama that counts generation calls."""

    def __init__(self, models, answer):
        self.models = models
        self.answer = answer
        self.posts = 0

    def get(self, url):
        return {"models": self.models}

    def post(self, url, payload):
        self.posts += 1
        return {"response": json.dumps(self.answer)}


def make_cfg(fallback=False):
    tmp = Path(tempfile.mkdtemp())
    (tmp / "models.lock").write_text("qwen2.5:3b  357c53fb659c\n", encoding="utf-8")
    return type("Cfg", (), {
        "LLM_MODEL": "qwen2.5:3b", "OLLAMA_URL": "http://x", "TEMPERATURE": 0.0, "SEED": 42,
        "ALLOW_MODEL_FALLBACK": fallback, "LLM_TIMEOUT": 5,
        "MODELS_LOCK": str(tmp / "models.lock"), "CACHE_DIR": str(tmp / "cache"),
    })


def test_second_call_comes_from_cache():
    transport = FakeTransport([{"name": "qwen2.5:3b", "digest": DIGEST}], {"intent": "FEES"})
    client = LLMClient(make_cfg(), transport)
    assert client.generate_json("p") == {"intent": "FEES"}
    assert client.generate_json("p") == {"intent": "FEES"}
    assert transport.posts == 1


def test_cache_file_keeps_inputs():
    cfg = make_cfg()
    transport = FakeTransport([{"name": "qwen2.5:3b", "digest": DIGEST}], {"intent": "FEES"})
    LLMClient(cfg, transport).generate_json("hello")
    record = json.loads(next((Path(cfg.CACHE_DIR) / "llm").glob("*.json")).read_text(encoding="utf-8"))
    assert record["prompt"] == "hello" and record["params"]["temperature"] == 0.0


def test_cache_key_ignores_dict_order():
    a = cache_key("m", "d", "p", {"temperature": 0, "seed": 42})
    b = cache_key("m", "d", "p", {"seed": 42, "temperature": 0})
    assert a == b and a != cache_key("m", "d", "p2", {"seed": 42, "temperature": 0})


def test_missing_model_stops_with_instructions():
    transport = FakeTransport([{"name": "llama3:8b", "digest": "ffff"}], {})
    with pytest.raises(ModelUnavailableError) as err:
        LLMClient(make_cfg(), transport).generate_json("p")
    assert "ollama pull qwen2.5:3b" in str(err.value) and "llama3:8b" in str(err.value)


def test_wrong_version_stops():
    transport = FakeTransport([{"name": "qwen2.5:3b", "digest": "0000" * 16}], {})
    with pytest.raises(ModelUnavailableError):
        LLMClient(make_cfg(), transport).generate_json("p")


def test_fallback_only_when_enabled():
    transport = FakeTransport([{"name": "qwen2.5:3b", "digest": "0000" * 16}], {"intent": "FEES"})
    assert LLMClient(make_cfg(fallback=True), transport).generate_json("p") == {"intent": "FEES"}
