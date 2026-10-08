import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
DATABASE_URL = os.getenv("DATABASE_URL", "postgres://localhost:5432/kezek")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
