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

## Hugging Face: a new question seems frozen
**Why:** the Space has 2 shared CPU cores; one model call can take minutes. Before step 13d a timed-out call
was retried twice (up to 30 minutes) and a second click queued another question.
**Check:** Logs → Container. You should see `question received`, then `[ollama]` lines, then `answered: ... N s`.
The start-up line `speed on this machine: prompt X tokens/s, generation Y tokens/s` shows how fast the hardware is.
**Fix:** click once and wait; the page now says «جارٍ البحث…». A model call over 180 s falls back to the rule
sentence. For faster answers, choose larger hardware in the Space settings (paid).
Questions from the evaluation sets asked with their reference date come from the cache instantly.
