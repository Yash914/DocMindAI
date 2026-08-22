from pathlib import Path


# ==============================
# Project Configuration
# ==============================

# Root directory of the project
BASE_DIR = Path(__file__).resolve().parent


# ==============================
# Data Directories
# ==============================

DATA_DIR = BASE_DIR / "data"

INPUT_DIR = DATA_DIR / "input"

PROCESSED_DIR = DATA_DIR / "processed"


# Create required directories automatically
INPUT_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


# ==============================
# Application Information
# ==============================

APP_NAME = "DocMind AI"

APP_VERSION = "0.1.0"