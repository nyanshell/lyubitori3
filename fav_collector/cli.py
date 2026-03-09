import click

from fav_collector import config
from fav_collector.crawler import setup_logging, run


@click.command()
@click.option("--max-stale", type=int, default=config.MAX_STALE, show_default=True,
              help="Stop after N cycles with no new images.")
@click.option("--user", type=str, default=None,
              help="Twitter username (overrides TWITTER_USER env).")
@click.option("--downloads-dir", type=click.Path(), default=None,
              help="Directory to save images (overrides DOWNLOADS_DIR env).")
@click.option("--scroll-min", type=int, default=None,
              help="Min scroll pixels per cycle (overrides SCROLL_PIXELS_MIN env).")
@click.option("--scroll-max", type=int, default=None,
              help="Max scroll pixels per cycle (overrides SCROLL_PIXELS_MAX env).")
@click.option("--log-level", type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"], case_sensitive=False),
              default=None, help="Log level (overrides LOG_LEVEL env).")
def main(max_stale, user, downloads_dir, scroll_min, scroll_max, log_level):
    import logging
    from pathlib import Path

    if user:
        config.TWITTER_USER = user
        config.LIKES_URL = f"https://x.com/{user}/likes"
    if downloads_dir:
        config.DOWNLOADS_DIR = Path(downloads_dir)
    if scroll_min:
        config.SCROLL_PIXELS_MIN = scroll_min
    if scroll_max:
        config.SCROLL_PIXELS_MAX = scroll_max
    if log_level:
        config.LOG_LEVEL = getattr(logging, log_level.upper(), logging.INFO)

    setup_logging()
    run(max_stale=max_stale)


if __name__ == "__main__":
    main()
