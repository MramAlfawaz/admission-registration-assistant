#!/bin/sh
# Start the assistant (and Ollama, when START_OLLAMA=1, as on Hugging Face Spaces).
set -e

if [ "${START_OLLAMA:-0}" = "1" ]; then
    ollama serve > /tmp/ollama.log 2>&1 &
    until ollama list > /dev/null 2>&1; do sleep 1; done
fi

# Model-call cache for this container, outside the repository files (docs/data-handling.md):
# it starts from the committed evaluation cache, and entries older than 30 days are deleted daily.
CACHE_DIR="${CACHE_DIR:-/tmp/assistant-cache}"
mkdir -p "$CACHE_DIR" "$(dirname "${ESCALATION_LOG:-/tmp/escalations.jsonl}")"
cp -Rn data/cache/. "$CACHE_DIR"/ 2>/dev/null || true
( while true; do find "$CACHE_DIR" -type f -mtime +30 -delete; sleep 86400; done ) &

# One worker holds one copy of the models; threads serve requests while the model is busy.
# The timeout is longer than one answer on a slow CPU (LLM_TIMEOUT, 600 s in the images).
exec gunicorn wsgi:app --bind "0.0.0.0:${PORT:-8000}" --workers 1 --threads 4 --timeout 660
