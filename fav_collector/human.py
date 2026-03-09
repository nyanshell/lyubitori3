import logging
import random
import time

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from fav_collector import config

log = logging.getLogger(__name__)


def _bezier(t: float, p0: float, p1: float, p2: float, p3: float) -> float:
    return (1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t**2 * p2 + t**3 * p3


def _smoothstep(t: float) -> float:
    return t * t * (3 - 2 * t)


def move_mouse(driver: WebDriver, start_x: int, start_y: int, end_x: int, end_y: int):
    cx1 = start_x + random.randint(-40, 40)
    cy1 = start_y + random.randint(-40, 40)
    cx2 = end_x + random.randint(-40, 40)
    cy2 = end_y + random.randint(-40, 40)

    steps = random.randint(config.MOUSE_STEPS_MIN, config.MOUSE_STEPS_MAX)

    prev_x, prev_y = start_x, start_y
    for i in range(1, steps + 1):
        t = i / steps
        t_eased = _smoothstep(t)

        bx = int(_bezier(t_eased, start_x, cx1, cx2, end_x))
        by = int(_bezier(t_eased, start_y, cy1, cy2, end_y))

        bx += random.randint(-1, 1)
        by += random.randint(-1, 1)

        dx = bx - prev_x
        dy = by - prev_y

        if dx != 0 or dy != 0:
            try:
                ActionChains(driver).move_by_offset(dx, dy).perform()
            except Exception:
                return

        prev_x += dx
        prev_y += dy

        base_delay = 0.005 + 0.01 * (1 - 4 * (t - 0.5) ** 2)
        time.sleep(base_delay + random.uniform(0, 0.005))


def human_scroll(driver: WebDriver, total_pixels: int | None = None):
    if total_pixels is None:
        total_pixels = random.randint(config.SCROLL_PIXELS_MIN, config.SCROLL_PIXELS_MAX)

    steps = random.randint(8, 15)
    base_step = total_pixels / steps

    for i in range(steps):
        jitter = random.uniform(0.7, 1.3)
        chunk = base_step * jitter
        driver.execute_script(f"window.scrollBy(0, {chunk})")

        progress = (i + 1) / steps
        delay = random.uniform(0.03, 0.08) * (1 + progress * 0.5)
        time.sleep(delay)

    if random.random() < 0.2:
        correction = random.randint(10, 30)
        driver.execute_script(f"window.scrollBy(0, -{correction})")
        time.sleep(random.uniform(0.1, 0.3))


def random_mouse_jitter(driver: WebDriver):
    try:
        viewport_w = driver.execute_script("return window.innerWidth")
        viewport_h = driver.execute_script("return window.innerHeight")

        margin = 100
        target_x = random.randint(margin, viewport_w - margin)
        target_y = random.randint(margin, viewport_h - margin)

        dx = random.randint(-150, 150)
        dy = random.randint(-150, 150)

        move_mouse(driver, target_x, target_y, target_x + dx, target_y + dy)
    except Exception as exc:
        log.debug("Mouse jitter failed: %s", exc)
