# docker and deployment

## local: `docker compose -f docker/docker-compose.yml up --build` is slow the first time
**Why:** it downloads the Python image, the CPU build of PyTorch, the documents, the embedding model and
`qwen2.5:3b` (about 3 GB in total). Later runs reuse them (the model is kept in the `ollama-models` volume).

## local: the app container exits with "documents not downloaded"
**Why:** the documents are fetched while the image is built; the university site was unreachable.
**Fix:** rebuild later, or put the files in `data/raw/` before building (they are copied into the image).

## Hugging Face: the push is rejected ("binary files" or "file too large")
**Why:** Spaces refuse binary files outside Git LFS/Xet, including in old commits.
**Fix:** push a single snapshot commit of the current files (README, "public demo"): the history, which once
held `.DS_Store` files, is not sent.

## Hugging Face: build fails at `python setup.py`
**Why:** read the build log line above the failure: documents not downloaded (site unreachable from the
build machine), or "Pinned model ... is unavailable" (the `qwen2.5:3b` tag changed).
**Fix:** for the site, retry the build; for the model, see `models.md`.

## Hugging Face: answers take one to three minutes, or the page times out
**Why:** the free CPU Space is slower than a laptop, and the first question after the Space wakes loads both models.
**Fix:** ask again after the first answer; questions from the evaluation sets come from the cache instantly.
`LLM_TIMEOUT` is 600 s in the image.
