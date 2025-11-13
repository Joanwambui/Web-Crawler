# Scrapy settings for books project

BOT_NAME = "books"

SPIDER_MODULES = ["books.spiders"]
NEWSPIDER_MODULE = "books.spiders"

# -------------------------------------------------------------------
# CRAWLING BEHAVIOR / POLITENESS
# -------------------------------------------------------------------

ROBOTSTXT_OBEY = True

USER_AGENT = (
    "books-monitor-bot/1.0 "
    "(contact: your-email@example.com)"
)

CONCURRENT_REQUESTS = 8
CONCURRENT_REQUESTS_PER_DOMAIN = 8
DOWNLOAD_DELAY = 1.0
COOKIES_ENABLED = False
TELNETCONSOLE_ENABLED = False

# -------------------------------------------------------------------
# RETRY / ROBUSTNESS
# -------------------------------------------------------------------

RETRY_ENABLED = True
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 522, 524, 408, 429]

AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1.0
AUTOTHROTTLE_MAX_DELAY = 10.0
AUTOTHROTTLE_TARGET_CONCURRENCY = 4.0
AUTOTHROTTLE_DEBUG = False

# -------------------------------------------------------------------
# MIDDLEWARES
# -------------------------------------------------------------------

DOWNLOADER_MIDDLEWARES = {
    # Example if you ever add rotating UAs or proxies
    # "scrapy.downloadermiddlewares.useragent.UserAgentMiddleware": None,
    # "scrapy_user_agents.middlewares.RandomUserAgentMiddleware": 400,
}

# -------------------------------------------------------------------
# ITEM PIPELINES (Mongo + Change Detection)
# -------------------------------------------------------------------

ITEM_PIPELINES = {
    "books.pipelines.MongoPipeline": 300,
}

# -------------------------------------------------------------------
# ✅ MONGO CONFIG (NOW USING ATLAS)
# -------------------------------------------------------------------
# -------------------------------------------------------------------
# MONGO CONFIG (FORCE .env LOAD)
# -------------------------------------------------------------------
import os
from pathlib import Path
from dotenv import load_dotenv

# Path: books/books/settings.py
# project_root = C:\FilersKeepers\fk_crawler\books
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

print("\n========== DEBUG .ENV LOADING ==========")
print("settings.py is running from:", Path(__file__).resolve())
print("Project base directory:", BASE_DIR)
print("Looking for .env at:", ENV_PATH)

if ENV_PATH.exists():
    print("✓ .env FOUND — loading now...")
    load_dotenv(dotenv_path=ENV_PATH)
else:
    print("❌ .env NOT FOUND at this path!")

MONGO_URL = os.getenv("MONGODB_URL")
MONGO_DATABASE = os.getenv("MONGODB_DB_NAME")

print("MONGO_URI loaded as:", MONGO_URL)
print("MONGO_DATABASE loaded as:", MONGO_DATABASE)
print("=========================================\n")

if not MONGO_URL:
    raise ValueError("ERROR: MONGODB_URL is missing — .env not loaded")



# -------------------------------------------------------------------
# RESUME SUPPORT (JOBDIR)
# -------------------------------------------------------------------
JOBDIR = "crawl_state/books_monitor"

# -------------------------------------------------------------------
# LOGGING
# -------------------------------------------------------------------
LOG_LEVEL = "INFO"
LOG_FILE = "logs/books_crawler.log"

# -------------------------------------------------------------------
# OUTPUT / ENCODING
# -------------------------------------------------------------------
FEED_EXPORT_ENCODING = "utf-8"

HTTPCACHE_ENABLED = False
