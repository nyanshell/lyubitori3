import logging
import random
import time
from pathlib import Path

import requests as http_requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

from fav_collector import config
from fav_collector.human import human_scroll, random_mouse_jitter
from fav_collector.storage import compute_hash, download_image, load_seen_hashes, save_image_and_meta
from fav_collector.tweets import clean_url_to_orig, extract_image_urls, extract_meta, find_articles, has_video

DEBUG_SCREENSHOT_DIR = Path("debug_screenshots")
DEBUG_HTML_DIR = Path("debug_html")

log = logging.getLogger("fav_collector")


def setup_logging():
    logging.basicConfig(
        level=config.LOG_LEVEL,
        format=config.LOG_FORMAT,
    )


def _get_existing_session() -> tuple[str | None, dict]:
    base_url = config.WEBDRIVER_URL.rstrip("/")
    if base_url.endswith("/wd/hub"):
        base_url = base_url[:-7]
    try:
        status = http_requests.get(f"{base_url}/status", timeout=10).json()
        for node in status.get("value", {}).get("nodes", []):
            for slot in node.get("slots", []):
                session = slot.get("session")
                if session:
                    return session["sessionId"], session.get("capabilities", {})
    except Exception as exc:
        log.debug("Failed to query grid status: %s", exc)
    return None, {}


def create_driver() -> tuple[webdriver.Remote, bool]:
    session_id, caps = _get_existing_session()

    if session_id:
        original_start = webdriver.Remote.start_session

        def _attach(self, capabilities):
            self.session_id = session_id
            self.caps = caps

        webdriver.Remote.start_session = _attach
        try:
            driver = webdriver.Remote(command_executor=config.WEBDRIVER_URL, options=Options())
        finally:
            webdriver.Remote.start_session = original_start

        try:
            handles = driver.window_handles
            if handles:
                driver.switch_to.window(handles[-1])
            else:
                driver.switch_to.new_window("tab")
            log.info("Attached to existing session %s (url: %s)", session_id, driver.current_url)
            return driver, True
        except Exception as exc:
            log.warning("Session %s unusable (%s), creating new one", session_id, exc)
            try:
                base_url = config.WEBDRIVER_URL.rstrip("/")
                if base_url.endswith("/wd/hub"):
                    base_url = base_url[:-7]
                http_requests.delete(f"{base_url}/session/{session_id}", timeout=10)
            except Exception:
                pass
            time.sleep(2)

    options = Options()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    if config.CHROME_PROFILE_PATH:
        options.add_argument(f"--user-data-dir={config.CHROME_PROFILE_PATH}")

    driver = webdriver.Remote(
        command_executor=config.WEBDRIVER_URL,
        options=options,
    )

    try:
        driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"},
        )
    except Exception as exc:
        log.debug("CDP command not supported: %s", exc)

    log.info("Created new session %s", driver.session_id)
    return driver, False


def navigate_to_likes(driver: webdriver.Remote):
    log.info("Navigating to %s", config.LIKES_URL)
    driver.get(config.LIKES_URL)
    time.sleep(config.PAGE_LOAD_WAIT)
    log.info("Current URL after navigation: %s", driver.current_url)


def ensure_on_likes_page(driver: webdriver.Remote):
    current_url = driver.current_url or ""
    if f"{config.TWITTER_USER}/likes" in current_url:
        log.info("Already on likes page (URL check)")
        return

    navigate_to_likes(driver)


def save_debug_snapshot(driver: webdriver.Remote, label: str):
    ts = int(time.time())
    DEBUG_SCREENSHOT_DIR.mkdir(exist_ok=True)
    DEBUG_HTML_DIR.mkdir(exist_ok=True)
    try:
        screenshot_path = DEBUG_SCREENSHOT_DIR / f"{label}_{ts}.png"
        driver.save_screenshot(str(screenshot_path))
        log.info("Debug screenshot saved: %s", screenshot_path)
    except Exception as exc:
        log.warning("Failed to save debug screenshot: %s", exc)
    try:
        html_path = DEBUG_HTML_DIR / f"{label}_{ts}.html"
        html_path.write_text(driver.page_source, encoding="utf-8")
        log.info("Debug HTML saved: %s", html_path)
    except Exception as exc:
        log.warning("Failed to save debug HTML: %s", exc)


def handle_error(driver: webdriver.Remote):
    log.warning("Error detected, refreshing page")
    driver.refresh()
    time.sleep(config.RETRY_WAIT)


def process_articles(
    driver: webdriver.Remote,
    seen_hashes: set[str],
) -> int:
    articles = find_articles(driver)
    log.info("Found %d articles on page", len(articles))

    new_count = 0
    for article in articles:
        try:
            if has_video(article):
                continue

            if not (image_urls := extract_image_urls(article)):
                continue

            meta = extract_meta(article)

            seen_pairs: set[tuple[str, str]] = set()
            for url in image_urls:
                if "pbs.twimg.com/media/" not in url:
                    continue
                png_orig, orig = clean_url_to_orig(url)
                pair = (png_orig, orig)
                if pair in seen_pairs:
                    continue
                seen_pairs.add(pair)

                image_bytes = download_image(png_orig)
                used_url = png_orig
                if image_bytes is None and png_orig != orig:
                    image_bytes = download_image(orig)
                    used_url = orig

                if image_bytes is None:
                    continue

                image_hash = compute_hash(image_bytes)
                if image_hash in seen_hashes:
                    continue

                seen_hashes.add(image_hash)
                save_image_and_meta(image_bytes, meta, used_url, image_hash, config.DOWNLOADS_DIR)
                new_count += 1
        except Exception as exc:
            log.warning("Error processing article: %s", exc)

    log.info("Downloaded %d new images this cycle", new_count)
    return new_count


def run(max_stale: int):
    log.info("Starting fav collector (max_stale=%d)", max_stale)

    driver, attached = create_driver()
    seen_hashes = load_seen_hashes(config.DOWNLOADS_DIR)

    try:
        ensure_on_likes_page(driver)

        stale_cycles = 0
        cycle = 0
        current_scroll_min = config.SCROLL_PIXELS_MIN
        current_scroll_max = config.SCROLL_PIXELS_MAX

        while True:
            cycle += 1

            random_mouse_jitter(driver)
            scroll_px = random.randint(current_scroll_min, current_scroll_max)
            human_scroll(driver, scroll_px)

            wait = random.uniform(config.SCROLL_WAIT_MIN, config.SCROLL_WAIT_MAX)
            log.info(
                "Cycle %d: scrolled %dpx, waiting %.1fs",
                cycle,
                scroll_px,
                wait,
            )
            time.sleep(wait)

            new_count = process_articles(driver, seen_hashes)

            if new_count > 0:
                current_scroll_min = config.SCROLL_PIXELS_MIN
                current_scroll_max = config.SCROLL_PIXELS_MAX
                stale_cycles = 0
            else:
                stale_cycles += 1
                current_scroll_min = min(
                    int(current_scroll_min * config.SCROLL_GROWTH_FACTOR),
                    config.SCROLL_PIXELS_MAX_LIMIT,
                )
                current_scroll_max = min(
                    int(current_scroll_max * config.SCROLL_GROWTH_FACTOR),
                    config.SCROLL_PIXELS_MAX_LIMIT,
                )

            if stale_cycles >= max_stale:
                log.info("No new content for %d cycles, may have reached the end", stale_cycles)
                save_debug_snapshot(driver, "end_of_feed")
                break

    except KeyboardInterrupt:
        log.info("Stopped by user")
    except Exception as exc:
        log.exception("Fatal error: %s", exc)
    finally:
        if not attached:
            try:
                driver.quit()
            except Exception:
                pass
