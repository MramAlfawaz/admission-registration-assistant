# models

## "Ollama is not reachable at http://localhost:11434"
**Why:** the Ollama app is not running.
**Fix:** open Ollama (macOS: Applications; Windows: Start menu; Linux: `ollama serve`). Check with
`ollama list`. If Ollama runs elsewhere, set `OLLAMA_URL` in `.env`.

## "Pinned model qwen2.5:3b (357c53fb659c) is unavailable"
**Why:** the model is not pulled, or the tag now points to different weights.
**Fix:** `ollama pull qwen2.5:3b`, then `python cli.py check-model`. If the digest still differs, the tag was
updated upstream: do not edit `models.lock` to make the error go away (that is the silent substitution
rule 1.3 forbids). See the handover memo, "what breaks", for the procedure.

## answers time out ("model unavailable while drafting (ReadTimeout)")
**Why:** a slow CPU, or another program using the memory. The 3B model needs about 2 GB of free RAM.
**Fix:** close heavy programs; raise `LLM_TIMEOUT` in `.env` (seconds; default 300, 600 in Docker). The
assistant still answers from rule sentences and quotes when the model times out, so nothing unsafe is shown.

## the first question takes minutes, or `setup.py` step 4 seems stuck
**Why:** the embedding model (about 470 MB) is downloading, then 186 passages are embedded once.
**Fix:** wait; it happens once and is cached (`~/.cache/huggingface`, `data/processed/embeddings/`).
`python setup.py` does it up front so it never surprises a student.

## embedding model download fails behind a proxy
**Fix:** set `HTTPS_PROXY`, or download once on another network; the files are cached by revision.
