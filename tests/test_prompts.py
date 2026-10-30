from pathlib import Path

from app.models.prompts import fill, load_prompt

ROOT = Path(__file__).resolve().parent.parent


def test_header_and_body_split():
    header, body = load_prompt("classify_intent_v1", ROOT / "prompts")
    assert header["version"] == "1" and header["model"] == "qwen2.5:3b"
    assert body.startswith("You classify questions")


def test_fill_leaves_json_braces_alone():
    assert fill('{"intent": "X"} {{q}}', q="سؤال") == '{"intent": "X"} سؤال'


def test_no_prompt_text_in_application_code():
    _, body = load_prompt("classify_intent_v1", ROOT / "prompts")
    first_line = body.splitlines()[0]
    for path in (ROOT / "app").rglob("*.py"):
        assert first_line not in path.read_text(encoding="utf-8"), path
