import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent  # .../lactare_app/app (contem templates/, static/)
APP_DIR = BASE_DIR
LACTARE_APP_ROOT = BASE_DIR.parent  # .../lactare_app

DB_PATH = LACTARE_APP_ROOT / "data" / "blhs.db"

APP_NAME = "Vitalia"
APP_TAGLINE = "Cada gota conta para salvar uma vida"
THEME_COLOR = "#1565c0"

SECRET_KEY = "vitalia-dev-secret-troque-em-producao"
ADMIN_USERNAME = "Adm"
ADMIN_PASSWORD = "Adm123"

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
CHAT_MODEL = "claude-opus-5"
