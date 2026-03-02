import logging
import re

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

log = logging.getLogger(__name__)

IMAGE_URL_PATTERN = re.compile(
    r"https://pbs\.twimg\.com/media/[A-Za-z0-9_-]+\?format=[a-zA-Z0-9_]+(?:&amp;|&)name=[a-zA-Z0-9_]+"
)

TWEET_LINK_PATTERN = re.compile(r"/([^/]+)/status/(\d+)")


def find_articles(driver) -> list[WebElement]:
    return driver.find_elements(By.CSS_SELECTOR, 'article[data-testid="tweet"]')


def has_video(article: WebElement) -> bool:
    if article.find_elements(By.TAG_NAME, "video"):
        return True
    if article.find_elements(By.CSS_SELECTOR, '[data-testid="videoPlayer"]'):
        return True
    if article.find_elements(By.CSS_SELECTOR, '[data-testid="videoComponent"]'):
        return True
    return False


def extract_image_urls(article: WebElement) -> list[str]:
    selectors = ['img[src*="pbs.twimg.com/media"]']

    urls = []
    for selector in selectors:
        try:
            images = article.find_elements(By.CSS_SELECTOR, selector)
            for img in images:
                src = img.get_attribute("src")
                if src and src not in urls:
                    urls.append(src)
        except Exception:
            pass

    if not urls:
        html = article.get_attribute("innerHTML")
        if html:
            raw_urls = IMAGE_URL_PATTERN.findall(html)
            for u in raw_urls:
                cleaned = u.replace("&amp;", "&")
                if cleaned not in urls:
                    urls.append(cleaned)

    return urls


def clean_url_to_orig(url: str) -> tuple[str, str]:
    url = url.replace("&amp;", "&")
    png_url = re.sub(r"format=[a-zA-Z0-9_]+", "format=png", url)
    png_orig = re.sub(r"&name=[a-zA-Z0-9_]+", "&name=orig", png_url)
    orig = re.sub(r"&name=[a-zA-Z0-9_]+", "&name=orig", url)
    return png_orig, orig


def extract_meta(article: WebElement) -> dict:
    author = "unknown"
    tweet_id = "unknown"
    tweet_time = "unknown"
    tweet_text = ""

    links = article.find_elements(By.CSS_SELECTOR, 'a[href*="/status/"]')
    for link in links:
        href = link.get_attribute("href") or ""
        match = TWEET_LINK_PATTERN.search(href)
        if match:
            author = match.group(1)
            tweet_id = match.group(2)
            break

    time_elements = article.find_elements(By.TAG_NAME, "time")
    if time_elements:
        tweet_time = time_elements[0].get_attribute("datetime") or "unknown"

    text_elements = article.find_elements(By.CSS_SELECTOR, '[data-testid="tweetText"]')
    if text_elements:
        tweet_text = text_elements[0].text

    return {
        "author": author,
        "tweet_id": tweet_id,
        "time": tweet_time,
        "text": tweet_text,
    }
