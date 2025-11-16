# books/pipelines.py

import os
import subprocess
import pymongo
import csv
import glob
from datetime import datetime
from itemadapter import ItemAdapter
from pymongo.errors import PyMongoError
from scrapy import signals
from dotenv import load_dotenv

load_dotenv()


class MongoPipeline:
    """
    FINAL VERSION — DIFF LOGGING (Option B), FEATURE-COMPLETE, SNAPSHOT FIX APPLIED.

    ✓ Upserts books into `books`
    ✓ Detects changes by comparing before/after values
    ✓ Saves OLD SNAPSHOT BEFORE ANY UPDATE (fixed)
    ✓ Logs only changed fields into books_changes as:

      {
         "book_id": "...",
         "type": "updated",
         "changes": {
             "title": {"old": "...", "new": "..."},
             "availability": {"old": "...", "new": "..."}
         },
         "timestamp": "...",
         "date": "YYYY-MM-DD"
      }

    ✓ Per-day dedupe (book_id + date)
    ✓ Backfill also uses snapshots + live books to compute changes
    ✓ CSV is only used to provide timestamp (changed_at)
    ✓ No last_seen anywhere
    """

    COLLECTION_NAME = "books"
    CHANGELOG_COLLECTION = "books_changes"

    # Fields for diff computation
    DIFF_FIELDS = [
        "url",
        "source_url",
        "title",
        "description",
        "category",
        "rating",
        "number_of_reviews",
        "image_url",
        "price_excl_tax",
        "price_incl_tax",
        "availability",
        #"content_hash",
    ]

    # -------------------------------------------------------------------------
    def __init__(self, mongo_url: str, mongo_db: str):
        self.mongo_url = mongo_url
        self.mongo_db = mongo_db
        self.client = None
        self.db = None
        self.first_run = False

        self.items_seen = 0
        self.items_with_changes = 0
        self.change_logs_inserted = 0

        # OLD STATE before update
        self._old_snapshots = {}

    # -------------------------------------------------------------------------
    @classmethod
    def from_crawler(cls, crawler):
        pipeline = cls(
            mongo_url=crawler.settings.get("MONGO_URL"),
            mongo_db=crawler.settings.get("MONGO_DATABASE", "books_db"),
        )
        crawler.signals.connect(pipeline.spider_closed, signal=signals.spider_closed)
        return pipeline

    # -------------------------------------------------------------------------
    def open_spider(self, spider):
        import certifi

        self.client = pymongo.MongoClient(
            self.mongo_url,
            tls=True,
            tlsCAFile=certifi.where()
        )
        self.db = self.client[self.mongo_db]

        existing = self.db.list_collection_names()
        books_exists = self.COLLECTION_NAME in existing
        changes_exists = self.CHANGELOG_COLLECTION in existing

        if books_exists:
            books_empty = self.db[self.COLLECTION_NAME].count_documents({}) == 0
        else:
            books_empty = True

        self.first_run = books_empty and not changes_exists

        print("\n============================")
        print(f"[MongoPipeline] FIRST_RUN = {self.first_run}")
        print("============================\n")

        books = self.db[self.COLLECTION_NAME]
        changes = self.db[self.CHANGELOG_COLLECTION]

        books.create_index("url", unique=True)
        books.create_index("content_hash")
        books.create_index("crawl_timestamp")

        changes.create_index("book_id")
        changes.create_index("timestamp")
        changes.create_index("date")

    # -------------------------------------------------------------------------
    def close_spider(self, spider):
        pass

    # -------------------------------------------------------------------------
    def spider_closed(self, spider):
        spider.logger.info(
            f"[MongoPipeline] Crawl summary: seen={self.items_seen}, "
            f"changed={self.items_with_changes}, logged={self.change_logs_inserted}"
        )

        # Run report generator
        try:
            import sys
            spider.logger.info("[MongoPipeline] Running report generator...")

            project_root = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..", "..")
            )
            report_script = os.path.join(project_root, "scheduler", "generate_report.py")

            subprocess.run(
                [sys.executable, report_script],
                stdout=sys.stdout,
                stderr=sys.stderr,
                text=True,
                check=True,
            )
        except Exception as e:
            spider.logger.error(f"[MongoPipeline] Report generation error: {e}")

        # Backfill
        if not self.first_run:
            try:
                self._verify_and_auto_backfill(spider)
            except Exception as e:
                spider.logger.error(f"[MongoPipeline] Auto-backfill error: {e}")

        if self.client:
            self.client.close()

    # -------------------------------------------------------------------------
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        books_col = self.db[self.COLLECTION_NAME]
        self.items_seen += 1

        # Normalize strings
        for field, value in adapter.items():
            if isinstance(value, str):
                cleaned = " ".join(value.split())
                if field in ("category", "availability"):
                    cleaned = cleaned.title()
                adapter[field] = cleaned

        book_id = adapter.get("_id")

        now = datetime.utcnow().isoformat()
        adapter.setdefault("crawl_timestamp", now)
        new_doc = adapter.asdict()

        existing = books_col.find_one({"_id": book_id})

        # ALWAYS SAVE OLD SNAPSHOT BEFORE ANY DIFF/UPDATE
        if existing:
            self._old_snapshots[book_id] = dict(existing)

        # NEW DOCUMENT
        if not existing:
            new_doc["status"] = "new"
            books_col.insert_one(new_doc)

            if not self.first_run:
                changes = self._compute_changes(None, new_doc)
                self._log_change(spider, book_id, "created", changes, now)

            return item

        # EXISTING DOCUMENT → DIFF
        changes = self._compute_changes(existing, new_doc)

        if changes:
            self.items_with_changes += 1
            new_doc["status"] = "updated"

            if not self.first_run:
                self._log_change(spider, book_id, "updated", changes, now)

            books_col.update_one({"_id": book_id}, {"$set": new_doc})
            return item

        # UNCHANGED
        books_col.update_one(
            {"_id": book_id},
            {"$set": {"status": "unchanged", "crawl_timestamp": now}}
        )

        return item

    # -------------------------------------------------------------------------
    def _compute_changes(self, old_doc: dict | None, new_doc: dict) -> dict:
        """
        Return changes in Option B format:
        {
           "title": { "old": ..., "new": ... },
           "availability": { "old": ..., "new": ... }
        }
        """
        changes = {}

        for field in self.DIFF_FIELDS:
            old_val = old_doc.get(field) if old_doc else None
            new_val = new_doc.get(field)
            if old_val != new_val:
                changes[field] = {"old": old_val, "new": new_val}

        return changes

    # -------------------------------------------------------------------------
    def _log_change(self, spider, book_id, change_type, changes, timestamp):
        if not changes:
            return

        changelog = self.db[self.CHANGELOG_COLLECTION]
        ts_date = timestamp.split("T")[0]

        # Per-day dedupe (book_id + date)
        #if changelog.find_one({"book_id": book_id, "date": ts_date}):
        #    return

        entry = {
            "book_id": book_id,
            "type": change_type,
            "changes": changes,
            "timestamp": datetime.utcnow(),
            "date": ts_date,
        }

        changelog.insert_one(entry)
        self.change_logs_inserted += 1

    # -------------------------------------------------------------------------
    def _verify_and_auto_backfill(self, spider):
        """
        CSV gives:
          - book_id
          - changed_at (timestamp)

        Old/new values must come from:
          - old_doc = saved snapshot
          - new_doc = current books record
        """
        project_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..")
        )
        reports_dir = os.path.join(project_root, "reports")

        csv_files = glob.glob(os.path.join(reports_dir, "daily_changes_*.csv"))
        if not csv_files:
            return

        latest_csv = max(csv_files, key=os.path.getmtime)

        changelog = self.db[self.CHANGELOG_COLLECTION]
        books_col = self.db[self.COLLECTION_NAME]

        with open(latest_csv, "r", encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))

        backfilled = 0
        skipped_dupes = 0

        for row in rows:
            bid = row.get("book_id")
            if not bid:
                continue

            changed_at = row.get("changed_at") or datetime.utcnow().isoformat()
            ts_date = changed_at.split("T")[0]

            # Skip if exists
            if changelog.find_one({"book_id": bid, "date": ts_date}):
                skipped_dupes += 1
                continue

            # Load new values from books
            current_doc = books_col.find_one({"_id": bid})
            old_doc = self._old_snapshots.get(bid)

            changes = self._compute_changes(old_doc, current_doc)
            if not changes:
                continue

            entry = {
                "book_id": bid,
                "type": "updated",
                "changes": changes,
                "timestamp": changed_at,
                "date": ts_date,
            }

            changelog.insert_one(entry)
            backfilled += 1
            self.change_logs_inserted += 1

        print(f"[MongoPipeline] Backfill inserted={backfilled}, skipped={skipped_dupes}")
