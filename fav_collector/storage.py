import hashlib
import json
import logging
import time
from pathlib import Path

import requests

from . import config

log = logging.getLogger(__name__)


def load_seen_hashes(downloads_dir: Path) -> set[str]:
    seen: set[str] = set()
    if not downloads_dir.exists():
        return seen
    for json_file in downloads_dir.glob("*.json"):
        try:
            data = json.loads(json_file.read_text(encoding="utf-8"))
            if "hash" in data:
                seen.add(data["hash"])
        except Exception:
            pass
    log.info("Loaded %d previously downloaded image hashes", len(seen))
    return seen


def compute_hash(image_bytes: bytes) -> str:
    return hashlib.md5(image_bytes).hexdigest()


def download_image(url: str) -> bytes | None:
    try:
        r = requests.get(url, timeout=config.IMAGE_DOWNLOAD_TIMEOUT)
        if r.status_code == 200:
            return r.content
        log.debug("HTTP %d for %s", r.status_code, url)
    except Exception as exc:
        log.warning("Failed to download %s: %s", url, exc)
    return None


def _determine_extension(url: str) -> str:
    if "format=png" in url:
        return ".png"
    if "format=jpg" in url or "format=jpeg" in url:
        return ".jpg"
    if "format=webp" in url:
        return ".webp"
    return ".img"


def save_image_and_meta(
    image_bytes: bytes,
    meta: dict,
    url_used: str,
    image_hash: str,
    downloads_dir: Path,
):
    downloads_dir.mkdir(parents=True, exist_ok=True)

    ts = int(time.time())
    author = meta.get("author", "unknown")
    tweet_id = meta.get("tweet_id", "unknown")
    ext = _determine_extension(url_used)
    base_name = f"{author}_{tweet_id}_{ts}_{image_hash[:8]}"

    img_path = downloads_dir / f"{base_name}{ext}"
    img_path.write_bytes(image_bytes)

    full_meta = {
        **meta,
        "url": url_used,
        "hash": image_hash,
        "download_time": ts,
    }
    json_path = downloads_dir / f"{base_name}.json"
    json_path.write_text(
        json.dumps(full_meta, indent=4, ensure_ascii=False),
        encoding="utf-8",
    )

    log.info("Saved %s", img_path.name)
