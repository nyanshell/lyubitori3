import logging
import tomllib
from pathlib import Path

_DEFAULTS = {
    "webdriver": {
        "url": "http://localhost:4444/wd/hub",
        "profile_path": "/home/seluser/.config/chrome",
    },
    "twitter": {
        "user": "",
    },
    "storage": {
        "downloads_dir": "downloads",
        "selector_cache": "selector_cache.json",
    },
    "behavior": {
        "scroll_wait_min": 5.0,
        "scroll_wait_max": 8.0,
        "scroll_pixels_min": 512,
        "scroll_pixels_max": 2048,
        "scroll_pixels_max_limit": 10000,
        "scroll_growth_factor": 1.1,
        "mouse_steps_min": 30,
        "mouse_steps_max": 60,
        "max_retries": 3,
        "retry_wait": 15.0,
        "vision_check_interval": 5,
        "page_load_wait": 10.0,
        "image_download_timeout": 30,
    },
    "logging": {
        "level": "INFO",
    },
}

_SETTINGS_FILE = Path("settings.toml")


def _deep_merge(base: dict, override: dict) -> dict:
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _load() -> dict:
    settings = _DEFAULTS.copy()
    if _SETTINGS_FILE.exists():
        with open(_SETTINGS_FILE, "rb") as f:
            user_settings = tomllib.load(f)
        settings = _deep_merge(settings, user_settings)
    return settings


_cfg = _load()

WEBDRIVER_URL: str = _cfg["webdriver"]["url"]
CHROME_PROFILE_PATH: str = _cfg["webdriver"]["profile_path"]

TWITTER_USER: str = _cfg["twitter"]["user"]
LIKES_URL: str = f"https://x.com/{TWITTER_USER}/likes"

DOWNLOADS_DIR: Path = Path(_cfg["storage"]["downloads_dir"])
SELECTOR_CACHE_FILE: Path = Path(_cfg["storage"]["selector_cache"])

SCROLL_WAIT_MIN: float = _cfg["behavior"]["scroll_wait_min"]
SCROLL_WAIT_MAX: float = _cfg["behavior"]["scroll_wait_max"]
SCROLL_PIXELS_MIN: int = _cfg["behavior"]["scroll_pixels_min"]
SCROLL_PIXELS_MAX: int = _cfg["behavior"]["scroll_pixels_max"]
SCROLL_PIXELS_MAX_LIMIT: int = _cfg["behavior"]["scroll_pixels_max_limit"]
SCROLL_GROWTH_FACTOR: float = _cfg["behavior"]["scroll_growth_factor"]
MOUSE_STEPS_MIN: int = _cfg["behavior"]["mouse_steps_min"]
MOUSE_STEPS_MAX: int = _cfg["behavior"]["mouse_steps_max"]
MAX_RETRIES: int = _cfg["behavior"]["max_retries"]
RETRY_WAIT: float = _cfg["behavior"]["retry_wait"]
VISION_CHECK_INTERVAL: int = _cfg["behavior"]["vision_check_interval"]
PAGE_LOAD_WAIT: float = _cfg["behavior"]["page_load_wait"]
IMAGE_DOWNLOAD_TIMEOUT: int = _cfg["behavior"]["image_download_timeout"]

LOG_LEVEL: int = getattr(logging, _cfg["logging"]["level"].upper(), logging.INFO)
LOG_FORMAT: str = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

MAX_STALE: int = 5000
