# environment

Where the system has been run, and every setting it reads.

## environments

| environment | hardware | software | status |
|---|---|---|---|
| development (all reported numbers) | MacBook Pro, Intel Core i5, 8 GB RAM, CPU only | macOS 15, Python 3.11.9, Ollama with `qwen2.5:3b` (`357c53fb659c`) | used throughout |
| local Docker (`docker/docker-compose.yml`) | any machine with Docker and about 6 GB free disk | `python:3.11.9-slim`, `ollama/ollama:0.35.0` | written; first real build is the deployment step |
| public demo (`Dockerfile`, Hugging Face Space) | free CPU Space | one container: the app (gunicorn, port 7860) and Ollama | written; first real build is the deployment step |
| Windows | — | — | **not tested** |

Pinned versions: `.python-version` (3.11.9), `requirements.txt` (every package `==`), `models.lock`
(Ollama digest and Hugging Face commit hash), the two Docker base images by tag.

## settings

All read in `config/config.py`, the only source of settings; set them in `.env` (created from
`.env.example` by `python setup.py`) or as environment variables.

| setting | default | meaning |
|---|---|---|
| `LLM_MODEL` | `qwen2.5:3b` | generation model in Ollama; must be listed in `models.lock` |
| `EMBED_MODEL` | `intfloat/multilingual-e5-small` | embedding model; revision from `models.lock` |
| `OLLAMA_URL` | `http://localhost:11434` | where Ollama listens |
| `TEMPERATURE` / `SEED` | `0` / `42` | reproducibility (rule 1.2); do not change during evaluation |
| `ALLOW_MODEL_FALLBACK` | `false` | never `true` for reported results (rule 1.3) |
| `LLM_TIMEOUT` | `300` (600 in Docker) | seconds per model call before falling back to rule sentences and quotes |
| `TOP_K` / `RETRIEVAL_CANDIDATES` / `RRF_K` | `5` / `50` / `60` | passages kept; candidates per method; fusion constant |
| `GEN_EVIDENCE_LIMIT` / `GEN_EVIDENCE_CHARS` | `3` / `700` | passages and characters per passage sent to the model |
| `RAW_DIR` / `PROCESSED_DIR` | `data/raw` / `data/processed` | documents and built data (not committed) |
| `CACHE_DIR` | `data/cache` (a runtime folder in Docker) | model-call cache; a deployed instance keeps it outside the repository (`docs/data-handling.md`) |
| `ESCALATION_LOG` | `data/processed/escalations.jsonl` | escalation records without question text |
| `LOG_LEVEL` | `INFO` | application log level |

Docker-only variables: `START_OLLAMA` (1 in the Space image: start Ollama inside the container), `PORT`
(7860 on Spaces, 8000 locally), `OLLAMA_KEEP_ALIVE` (keep the model loaded between questions).

## resources

About 2 GB of RAM for `qwen2.5:3b`, 0.5 GB for the embedding model; disk: 2 GB for the model, 0.5 GB for
the embedding model, about 1 GB for Python packages.
