"""Load versioned prompt files (Development Standards rule 1.4)."""
from pathlib import Path


def load_prompt(name, prompts_dir="prompts"):
    """Read a prompt file and split its header from its body.

    A prompt file starts with a header between two '---' lines holding
    version, purpose and model, followed by the prompt text.

    Args:
        name: file name without extension, for example "classify_intent_v1".
        prompts_dir: folder holding the prompt files.

    Returns:
        A (header dict, body string) tuple.
    """
    text = (Path(prompts_dir) / f"{name}.md").read_text(encoding="utf-8")
    header = {}
    if text.startswith("---"):
        _, raw_header, text = text.split("---", 2)
        for line in raw_header.strip().splitlines():
            key, _, value = line.partition(":")
            header[key.strip()] = value.strip()
    return header, text.strip()


def fill(template, **values):
    """Replace {{name}} placeholders; braces elsewhere are left untouched."""
    for key, value in values.items():
        template = template.replace("{{" + key + "}}", str(value))
    return template
