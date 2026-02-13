BOT_NAME = "filmscraper"

SPIDER_MODULES = ["filmscraper.spiders"]
NEWSPIDER_MODULE = "filmscraper.spiders"

ROBOTSTXT_OBEY = True

DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ru,ru-RU;q=0.9,en;q=0.8",
}

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/121.0.0.0 Safari/537.36"
)

CONCURRENT_REQUESTS = 8
DOWNLOAD_DELAY = 0.5

RETRY_ENABLED = True
RETRY_TIMES = 2

HTTPERROR_ALLOWED_CODES = []

FEED_EXPORT_ENCODING = "utf-8"

