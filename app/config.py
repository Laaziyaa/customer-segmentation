"""
Central configuration for Customer Segmentation Agent.
Uses pathlib and environment variables to ensure zero hard-coded relative paths.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))
RAW_DATA_PATH = Path(os.getenv("RAW_DATA_PATH", DATA_DIR / "raw" / "bank-additional-full.csv"))
PROCESSED_DATA_DIR = Path(os.getenv("PROCESSED_DATA_DIR", DATA_DIR / "processed"))
MODELS_DIR = Path(os.getenv("MODELS_DIR", DATA_DIR / "models"))
UPLOADS_DIR = Path(os.getenv("UPLOADS_DIR", DATA_DIR / "uploads"))
OUTPUTS_DIR = Path(os.getenv("OUTPUTS_DIR", DATA_DIR / "outputs"))

# Ensure runtime directories exist
for directory in (DATA_DIR, PROCESSED_DATA_DIR, MODELS_DIR, UPLOADS_DIR, OUTPUTS_DIR):
    directory.mkdir(parents=True, exist_ok=True)

# CORS configuration: strict explicit origins allow credentials safely
_DEFAULT_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
    "https://customer-segmentation-agent.vercel.app",
]

_env_origins = os.getenv("CORS_ORIGINS", "")
if _env_origins:
    CORS_ORIGINS = [o.strip() for o in _env_origins.split(",") if o.strip()]
else:
    CORS_ORIGINS = _DEFAULT_ORIGINS

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL_NAME = os.getenv("GROQ_MODEL_NAME", "llama-3.1-8b-instant")

MINIBATCH_THRESHOLD = int(os.getenv("MINIBATCH_THRESHOLD", "10000"))
DEFAULT_K = int(os.getenv("DEFAULT_K", "4"))
