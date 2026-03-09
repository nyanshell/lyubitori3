import logging
import os
from pathlib import Path


def _env(key: str, default: str) -> str:
    return os.environ.get(key, default)


def _env_int(key: str, default: int) -> int:
    return int(os.environ.get(key, default))


def _env_float(key: str, default: float) -> float:
    return float(os.environ.get(key, default))


WEBDRIVER_URL = _env("WEBDRIVER_URL", "http://localhost:4444/wd/hub")
CHROME_PROFILE_PATH = _env("CHROME_PROFILE_PATH", "/home/seluser/.config/chrome")

TWITTER_USER = _env("TWITTER_USER", "")
LIKES_URL = f"https://x.com/{TWITTER_USER}/likes"

DOWNLOADS_DIR = Path(_env("DOWNLOADS_DIR", "downloads"))

SCROLL_WAIT_MIN = _env_float("SCROLL_WAIT_MIN", 5.0)
SCROLL_WAIT_MAX = _env_float("SCROLL_WAIT_MAX", 8.0)
SCROLL_PIXELS_MIN = _env_int("SCROLL_PIXELS_MIN", 2500)
SCROLL_PIXELS_MAX = _env_int("SCROLL_PIXELS_MAX", 4000)
SCROLL_PIXELS_MAX_LIMIT = _env_int("SCROLL_PIXELS_MAX_LIMIT", 10000)
SCROLL_GROWTH_FACTOR = _env_float("SCROLL_GROWTH_FACTOR", 1.3)
MOUSE_STEPS_MIN = _env_int("MOUSE_STEPS_MIN", 30)
MOUSE_STEPS_MAX = _env_int("MOUSE_STEPS_MAX", 60)
MAX_RETRIES = _env_int("MAX_RETRIES", 3)
RETRY_WAIT = _env_float("RETRY_WAIT", 15.0)
PAGE_LOAD_WAIT = _env_float("PAGE_LOAD_WAIT", 10.0)
IMAGE_DOWNLOAD_TIMEOUT = _env_int("IMAGE_DOWNLOAD_TIMEOUT", 30)

LOG_LEVEL = getattr(logging, _env("LOG_LEVEL", "INFO").upper(), logging.INFO)
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

MAX_STALE = _env_int("MAX_STALE", 5000)
