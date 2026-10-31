"""Load the model into memory at container start and log how fast this machine generates.

Run in the background by docker/start.sh, so the first student question does not pay the load time
and the container log shows the speed (public demo, step 13: answers timed out with no clue why).
Container tooling, not application code.
"""
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s warmup: %(message)s", stream=sys.stdout)
log = logging.getLogger("warmup")
URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
MODEL = os.environ.get("LLM_MODEL", "qwen2.5:3b")


def main():
    """Load the model, then time one short generation and log tokens per second."""
    started = time.monotonic()
    try:
        requests.post(f"{URL}/api/generate", json={"model": MODEL, "prompt": "", "keep_alive": "24h"}, timeout=900)
        log.info("model %s loaded in %.0f s", MODEL, time.monotonic() - started)
        r = requests.post(f"{URL}/api/generate", timeout=900, json={
            "model": MODEL, "prompt": "اكتب جملة واحدة عن الجامعة.", "stream": False,
            "options": {"num_predict": 32, "temperature": 0}}).json()
        prompt_rate = r.get("prompt_eval_count", 0) / max(r.get("prompt_eval_duration", 1) / 1e9, 1e-9)
        gen_rate = r.get("eval_count", 0) / max(r.get("eval_duration", 1) / 1e9, 1e-9)
        log.info("speed on this machine: prompt %.1f tokens/s, generation %.1f tokens/s", prompt_rate, gen_rate)
    except requests.RequestException as e:
        log.error("warm-up failed: %s", e)


if __name__ == "__main__":
    main()
