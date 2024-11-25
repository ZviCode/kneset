import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
KNESSET_API_URL = os.getenv("KNESSET_API_URL")
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

POLLING_INTERVAL = int(os.getenv("POLLING_INTERVAL", 60))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", 3))

BASE_DIR = Path(__file__).parent.parent
CACHE_DIR = BASE_DIR / "image_cache"
STORAGE_FILE = BASE_DIR / "bot_state.json"
FONT_PATH = BASE_DIR / "assets" / "fonts" / "ARIAL.TTF"

RLM = '\u200F'
LRM = '\u200E'

FONT_SIZE = 20