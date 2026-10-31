"""Call the pinned local generation model through Ollama, with caching.

Implements Development Standards rules 1.1 (pinned version check),
1.2 (temperature and seed from configuration), 1.3 (no silent fallback)
and 1.5 (every call cached on disk).
"""
import hashlib
import json
import logging
import time
from pathlib import Path

import requests

log = logging.getLogger(__name__)


class ModelUnavailableError(RuntimeError):
    """Raised when the pinned model is missing, unreachable or a different version."""


def read_lock(path):
    """Return {model name: pinned id} from models.lock."""
    pins = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if len(parts) >= 2 and not line.lstrip().startswith("#"):
            pins[parts[0]] = parts[1]
    return pins


def cache_key(model, digest, prompt, params):
    """Return a SHA-256 fingerprint of everything that affects the output."""
    blob = json.dumps({"model": model, "digest": digest, "prompt": prompt, "params": params},
                      sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


class HttpTransport:
    """Send JSON requests with a timeout and exponential backoff."""

    def __init__(self, timeout=180, retries=3):
        self.timeout = timeout
        self.retries = retries

    def get(self, url):
        """Send a GET request and return the JSON body."""
        return self._send("GET", url, None)

    def post(self, url, payload):
        """Send a POST request and return the JSON body."""
        return self._send("POST", url, payload)

    def _send(self, method, url, payload):
        """Send one request, retrying with backoff before giving up."""
        for attempt in range(self.retries):
            try:
                r = requests.request(method, url, json=payload, timeout=self.timeout)
                r.raise_for_status()
                return r.json()
            except requests.Timeout:
                # The model is still busy with the request that timed out; sending it again only queues
                # more work behind it (public demo: two clicks and their retries waited 30 minutes).
                raise
            except requests.RequestException as e:
                if attempt == self.retries - 1:
                    raise
                wait = 2 ** attempt
                log.warning("%s %s failed (%s), retrying in %ss", method, url, e, wait)
                time.sleep(wait)
        return None


class LLMClient:
    """Generate JSON answers from the pinned local model."""

    def __init__(self, cfg, transport=None):
        self.cfg = cfg
        self.model = cfg.LLM_MODEL
        self.transport = transport or HttpTransport(timeout=cfg.LLM_TIMEOUT)
        self.cache_dir = Path(cfg.CACHE_DIR) / "llm"
        self._digest = None

    def verify_model(self):
        """Return the installed digest, or stop if it differs from models.lock.

        Raises:
            ModelUnavailableError: when the model is missing, unreachable or
                not the pinned version and fallback is disabled.
        """
        if self._digest:
            return self._digest
        pinned = read_lock(self.cfg.MODELS_LOCK).get(self.model)
        if pinned is None:
            raise ModelUnavailableError(f"{self.model} is not listed in {self.cfg.MODELS_LOCK}")
        try:
            tags = self.transport.get(f"{self.cfg.OLLAMA_URL}/api/tags")
        except requests.RequestException as e:
            raise ModelUnavailableError(
                f"Ollama is not reachable at {self.cfg.OLLAMA_URL} ({e}). "
                "Open the Ollama app and try again.") from e
        installed = {m["name"]: m.get("digest", "").replace("sha256:", "")
                     for m in tags.get("models", [])}
        digest = installed.get(self.model)
        if digest is None or not digest.startswith(pinned):
            found = "not installed" if digest is None else f"installed version {digest[:12]}"
            message = (
                f"Pinned model {self.model} ({pinned}) is unavailable: {found}.\n"
                f"Installed models: {', '.join(sorted(installed)) or 'none'}\n"
                f"Install it with: ollama pull {self.model}")
            if not self.cfg.ALLOW_MODEL_FALLBACK:
                raise ModelUnavailableError(
                    message + "\nFallback is disabled: results from a different model would "
                    "not be comparable (Development Standards rule 1.3).")
            log.warning("ALLOW_MODEL_FALLBACK is on, continuing unpinned. %s", message)
            digest = digest or "unpinned"
        self._digest = digest
        return digest

    def generate_json(self, prompt):
        """Return the model's JSON answer to a prompt, from cache when possible.

        Args:
            prompt: the complete prompt text.

        Returns:
            The parsed JSON object produced by the model.

        Raises:
            ValueError: when the model output is not valid JSON.
        """
        digest = self.verify_model()
        params = {"temperature": self.cfg.TEMPERATURE, "seed": self.cfg.SEED, "format": "json"}
        path = self.cache_dir / f"{cache_key(self.model, digest, prompt, params)}.json"
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))["response"]
        payload = {"model": self.model, "prompt": prompt, "stream": False, "format": "json",
                   "options": {"temperature": params["temperature"], "seed": params["seed"]}}
        started = time.monotonic()
        raw = self.transport.post(f"{self.cfg.OLLAMA_URL}/api/generate", payload)
        try:
            response = json.loads(raw["response"])
        except (KeyError, TypeError, json.JSONDecodeError) as e:
            raise ValueError(f"model returned invalid JSON: {str(raw)[:200]}") from e
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        record = {"model": self.model, "digest": digest, "params": params, "prompt": prompt,
                  "response": response, "seconds": round(time.monotonic() - started, 2)}
        path.write_text(json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True),
                        encoding="utf-8")
        return response
