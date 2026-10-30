"""Hold every setting for the application."""
import os
from dotenv import load_dotenv

load_dotenv()


class BaseConfig:
    # --- models ---
    LLM_MODEL = os.getenv("LLM_MODEL", "qwen2.5:3b")
    EMBED_MODEL = os.getenv("EMBED_MODEL", "intfloat/multilingual-e5-small")
    OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
    TEMPERATURE = float(os.getenv("TEMPERATURE", "0"))
    SEED = int(os.getenv("SEED", "42"))
    ALLOW_MODEL_FALLBACK = os.getenv("ALLOW_MODEL_FALLBACK", "false").lower() == "true"
    # --- retrieval ---
    TOP_K = int(os.getenv("TOP_K", "5"))
    # --- paths ---
    SOURCES_FILE = os.getenv("SOURCES_FILE", "data/sources.json")
    RAW_DIR = os.getenv("RAW_DIR", "data/raw")
    PROCESSED_DIR = os.getenv("PROCESSED_DIR", "data/processed")
    CACHE_DIR = os.getenv("CACHE_DIR", "data/cache")
    # --- logging ---
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


class DevelopmentConfig(BaseConfig):
    DEBUG = True


class ProductionConfig(BaseConfig):
    DEBUG = False


class TestingConfig(BaseConfig):
    TESTING = True


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}
