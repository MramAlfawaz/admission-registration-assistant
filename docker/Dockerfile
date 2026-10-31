# The assistant alone; Ollama runs as its own service (docker/docker-compose.yml).
FROM python:3.11.9-slim
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates libgomp1 \
    && rm -rf /var/lib/apt/lists/*
ENV PYTHONUNBUFFERED=1 \
    HF_HOME=/opt/hf-cache \
    CACHE_DIR=/srv/runtime/cache \
    ESCALATION_LOG=/srv/runtime/escalations.jsonl \
    LLM_TIMEOUT=600 \
    PORT=8000
WORKDIR /app

# CPU build of the pinned torch (2.2.2+cpu) instead of the default wheel with CUDA libraries.
COPY requirements.txt .
RUN pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt

COPY . .
# Documents, calendar, chunks and the embedding model are prepared at build time; the generation
# model is checked when the app first answers (Ollama is a separate service, not running here).
RUN python setup.py --skip-llm

EXPOSE 8000
CMD ["sh", "docker/start.sh"]
