"""
daily_scheduler.py
-------------------
Runs the BooksToScrape crawler once per day, detects data changes,
and generates a daily change report.

Uses APScheduler (cron style)
"""

import datetime
import logging
import os
import sys
import time
import signal
from subprocess import run, CalledProcessError
from apscheduler.schedulers.blocking import BlockingScheduler

# ---------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))          # .../fk_crawler/scheduler
PROJECT_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "books"))  # .../fk_crawler/books
REPORT_SCRIPT = os.path.join(BASE_DIR, "generate_report.py")

# ---------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

log_path = os.path.join(LOG_DIR, "daily_scheduler.log")
logging.basicConfig(
    filename=log_path,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

# ---------------------------------------------------------------------
# Core task: Run the crawler and generate report
# ---------------------------------------------------------------------
def run_crawler():
    start_time = datetime.datetime.now()
    logging.info("🕐 Starting scheduled crawl at %s", start_time)

    try:
        # 1) Run Scrapy
        logging.info("▶ Running: scrapy crawl book_spider (cwd=%s)", PROJECT_DIR)
        run(["scrapy", "crawl", "book_spider"], check=True, cwd=PROJECT_DIR)
        logging.info("✅ Crawl finished successfully")

        # 2) Run Report Generator
        logging.info("▶ Running: generate_report.py")
        run([sys.executable, REPORT_SCRIPT], check=True)
        logging.info("📊 Daily report generated successfully")

    except CalledProcessError as e:
        logging.error("❌ Subprocess failed: %s", e)

    except Exception as e:
        logging.exception("⚠️ Unexpected error during scheduled run: %s", e)

    end_time = datetime.datetime.now()
    duration = (end_time - start_time).total_seconds()
    logging.info("🕓 Crawl + report completed in %.2f seconds\n", duration)


# ---------------------------------------------------------------------
# Scheduler setup
# ---------------------------------------------------------------------
from apscheduler.schedulers.background import BackgroundScheduler
scheduler = BackgroundScheduler(timezone="Africa/Nairobi")
scheduler.add_job(run_crawler, "cron", hour=21, minute=12, id="daily_crawl_job")
# scheduler.add_job(run_crawler, "interval", minutes=1, id="test_crawl_job")


# ---------------------------------------------------------------------
# Graceful shutdown handler (CTRL+C works on Windows + Linux)
# ---------------------------------------------------------------------
def shutdown(signum, frame):
    logging.info("🛑 Received stop signal (%s). Shutting down scheduler...", signum)
    try:
        scheduler.shutdown(wait=False)
    except Exception:
        pass
    sys.exit(0)


# Register CTRL+C and terminate signals
signal.signal(signal.SIGINT, shutdown)   # CTRL+C
signal.signal(signal.SIGTERM, shutdown)  # kill signal


# ---------------------------------------------------------------------
# Start Scheduler
# ---------------------------------------------------------------------
if __name__ == "__main__":
    logging.info("📅 Scheduler started... waiting for next run.")
    scheduler.start()
    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        shutdown(None, None)