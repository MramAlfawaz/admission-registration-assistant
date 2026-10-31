# running the app

## "Address already in use" / the page does not open on port 5000
**Why:** on macOS, AirPlay Receiver uses port 5000.
**Fix:** the development server uses port **5001** (`python app.py`, then http://localhost:5001). If 5001
is taken too, change the port in `app.py`.

## the page says the assistant is temporarily unavailable (HTTP 503)
**Why:** the assistant could not be built or answer: usually Ollama is not running, or `ingest` was not run.
**Fix:** check `app.log` (the details go there, never to the page): start Ollama, or run `python setup.py`.

## the first answer after starting is slow
**Why:** the embedding model and the generation model load on the first question (lazy loading, so the app
starts instantly).
**Fix:** expected; later answers take about 30 s on the development Mac, instantly for cached questions.

## `evaluate-e2e` refuses to run: "set changed"
**Why:** a frozen evaluation file was edited; its sha256 no longer matches `evaluation/end_to_end/FROZEN`.
**Fix:** revert the file (`git checkout evaluation/end_to_end/`). A corrected set must be a new version,
reported beside the old one (`docs/evaluation.md`).

## zsh: "unrecognized arguments: # ..."
**Why:** a pasted command had a trailing comment; zsh does not treat `#` as a comment interactively.
**Fix:** paste commands without the comment, or run `setopt interactivecomments` once.
