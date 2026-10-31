# Public demo on Hugging Face Spaces: the assistant and Ollama in one CPU-only container.
# For running locally, docker/docker-compose.yml runs them as two services instead.
# Build arguments are pinned like every other version (Development Standards 1.1).
ARG OLLAMA_VERSION=0.35.0

FROM ollama/ollama:${OLLAMA_VERSION} AS ollama
# Keep the CPU runtime only: the GPU libraries are several GB and a CPU Space cannot use them.
RUN find /usr/lib/ollama -mindepth 1 -maxdepth 1 -type d -exec rm -rf {} +

FROM python:3.11.9-slim
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates libgomp1 libopenblas0 libstdc++6 \
    && rm -rf /var/lib/apt/lists/*
COPY --from=ollama /usr/bin/ollama /usr/bin/ollama
COPY --from=ollama /usr/lib/ollama /usr/lib/ollama

# Spaces run the container as user 1000.
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    HF_HOME=/home/user/.cache/huggingface \
    OLLAMA_MODELS=/home/user/.ollama/models \
    OLLAMA_HOST=127.0.0.1:11434 \
    OLLAMA_KEEP_ALIVE=24h \
    OLLAMA_URL=http://127.0.0.1:11434 \
    LLM_TIMEOUT=600 \
    CACHE_DIR=/home/user/runtime/cache \
    ESCALATION_LOG=/home/user/runtime/escalations.jsonl \
    START_OLLAMA=1 \
    PORT=7860
WORKDIR /home/user/app

# CPU build of the pinned torch (2.2.2+cpu); the default Linux wheel brings about 3 GB of CUDA libraries.
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir --user --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt

COPY --chown=user . .
# Pull the pinned model, then run the bootstrap: documents, calendar, chunks, embedding model and
# the model check against models.lock. The build fails if any step fails (no silent fallback).
RUN (ollama serve > /tmp/ollama-build.log 2>&1 &) \
    && until ollama list > /dev/null 2>&1; do sleep 1; done \
    && ollama pull qwen2.5:3b \
    && python setup.py

EXPOSE 7860
CMD ["sh", "docker/start.sh"]
