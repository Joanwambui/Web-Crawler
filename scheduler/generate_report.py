"""
generate_report.py
------------------

Daily change report generator for Books to Scrape.

This script is designed to be run AFTER a successful crawl:
    scrapy crawl book_spider → generate_report.py

It assumes:
  • Main collection: `books`
  • Change log collection: `books_changes`
"""

import argparse
import csv
import datetime as dt
import json
import logging
import os
from datetime import datetime, timedelta, UTC
from typing import Any, Dict, List, Tuple

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

# ---------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPORTS_DIR = os.path.join(BASE_DIR, "..", "reports")
LOG_DIR = os.path.join(BASE_DIR, "logs")

os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

log_path = os.path.join(LOG_DIR, "generate_report.log")

logging.basicConfig(
    filename=log_path,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

# ---------------------------------------------------------------------
# MongoDB configuration
# ---------------------------------------------------------------------

def get_mongo() -> Tuple[MongoClient, Database, Collection, Collection]:
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    mongo_db_name = os.getenv("MONGO_DATABASE", "books_db")

    books_collection_name = os.getenv("BOOKS_COLLECTION", "books")
    changes_collection_name = os.getenv("CHANGES_COLLECTION", "books_changes")

    client = MongoClient(mongo_uri)
    db = client[mongo_db_name]

    return client, db, db[books_collection_name], db[changes_collection_name]

# ---------------------------------------------------------------------
# Argument + Time Window Handling
# ---------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate daily change report for Books to Scrape."
    )
    parser.add_argument("--from", dest="from_date", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--to", dest="to_date", help="End date (YYYY-MM-DD)")
    return parser.parse_args()


def get_time_window(args: argparse.Namespace) -> Tuple[dt.datetime, dt.datetime]:
    now = datetime.now(UTC)
    buffer = timedelta(minutes=5)

    # Start
    if args.from_date:
        start = datetime.strptime(args.from_date, "%Y-%m-%d").replace(tzinfo=UTC)
    else:
        start = now - timedelta(days=1, minutes=5)

    # End
    if args.to_date:
        end = datetime.strptime(args.to_date, "%Y-%m-%d").replace(tzinfo=UTC) + timedelta(days=1)
    else:
        end = now + buffer

    return start, end

# ---------------------------------------------------------------------
# Query helpers
# ---------------------------------------------------------------------

def fetch_new_books(
    books_col: Collection,
    start: dt.datetime,
    end: dt.datetime,
) -> List[Dict[str, Any]]:
    """
    Books whose *first_seen* is within the window.
    last_seen will always be included for reporting.
    """
    query = {"first_seen": {"$gte": start.isoformat(), "$lt": end.isoformat()}}

    projection = {
        "_id": 1,
        "url": 1,
        "title": 1,
        "category": 1,
        "price_incl_tax": 1,
        "price_excl_tax": 1,
        "availability": 1,
        "number_of_reviews": 1,
        "image_url": 1,
        "rating": 1,
        "first_seen": 1,
        "last_seen": 1,       # <-- FIXED (included properly)
        "status": 1,
    }

    return list(books_col.find(query, projection))


def fetch_changes(
    changes_col: Collection,
    start: dt.datetime,
    end: dt.datetime,
) -> List[Dict[str, Any]]:
    """
    Book updates from books_changes collection.
    This MUST also include last_seen.
    """
    query = {"timestamp": {"$gte": start.isoformat(), "$lt": end.isoformat()}}

    projection = {
        "_id": 1,
        "book_id": 1,
        "type": 1,
        "timestamp": 1,
        "old": 1,
        "new": 1,
        "last_seen": 1,        # <-- FIXED
    }

    return list(changes_col.find(query, projection))


# ---------------------------------------------------------------------
# Report formatting
# ---------------------------------------------------------------------

def normalize_change_row(change: Dict[str, Any]) -> Dict[str, Any]:
    old_data = change.get("old") or {}
    new_data = change.get("new") or {}

    flat_fields = {}
    for k, v in new_data.items():
        flat_fields[f"{k}_new"] = v
    for k, v in old_data.items():
        flat_fields[f"{k}_old"] = v

    return {
        "book_id": str(change.get("book_id", "")),
        "type": change.get("type", "updated"),
        "timestamp": change.get("timestamp"),
        "last_seen": change.get("last_seen", ""),   # <-- FIXED
        **flat_fields,
    }


def build_report_payload(
    start: dt.datetime,
    end: dt.datetime,
    new_books: List[Dict[str, Any]],
    changes: List[Dict[str, Any]],
) -> Dict[str, Any]:
    return {
        "report_window": {
            "start": start.isoformat(),
            "end": end.isoformat(),
        },
        "summary": {
            "new_books": len(new_books),
            "updated_books": len(changes),
        },
        "new_books": new_books,
        "updated_books": [normalize_change_row(c) for c in changes],
    }

# ---------------------------------------------------------------------
# File writers
# ---------------------------------------------------------------------

def write_json_report(payload: Dict[str, Any], date_label: str) -> str:
    path = os.path.join(REPORTS_DIR, f"daily_changes_{date_label}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    return path


def write_csv_report(payload: Dict[str, Any], date_label: str) -> str:
    path = os.path.join(REPORTS_DIR, f"daily_changes_{date_label}.csv")

    rows: List[Dict[str, Any]] = []

    # New books section
    for b in payload["new_books"]:
        rows.append({
            "record_type": "new",
            "book_id": str(b.get("_id")),
            "url": b.get("url", ""),
            "title": b.get("title", ""),
            "category": b.get("category", ""),
            "price_incl_tax": b.get("price_incl_tax", ""),
            "price_excl_tax": b.get("price_excl_tax", ""),
            "availability": b.get("availability", ""),
            "number_of_reviews": b.get("number_of_reviews", ""),
            "image_url": b.get("image_url", ""),
            "rating": b.get("rating", ""),
            "first_seen": b.get("first_seen", ""),
            "last_seen": b.get("last_seen", ""),        # <-- FIXED
        })

    # Updated books section
    for c in payload["updated_books"]:
        rows.append({
            "record_type": "updated",
            **c
        })

    # Write
    if not rows:
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["record_type", "book_id"])
            writer.writeheader()
        return path

    fieldnames = sorted({k for r in rows for k in r.keys()})
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return path

# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------

def main() -> None:
    args = parse_args()
    start, end = get_time_window(args)
    client, db, books_col, changes_col = get_mongo()

    try:
        logging.info(f"Generating change report for {start} → {end}")

        new_books = fetch_new_books(books_col, start, end)
        changes = fetch_changes(changes_col, start, end)

        if len(new_books) == 0 and len(changes) == 0:
            print("[CHANGE REPORT] No changes detected during window.")
            logging.info("No changes detected — report not generated.")
            return

        payload = build_report_payload(start, end, new_books, changes)
        label = datetime.now(UTC).strftime("%Y-%m-%d_%H-%M-%S")

        json_path = write_json_report(payload, label)
        csv_path = write_csv_report(payload, label)

        print(f"[CHANGE REPORT] Report generated: {label}")
        logging.info(f"Report written: {json_path}, {csv_path}")

    except Exception as exc:
        logging.exception(f"Report generation failed: {exc}")
        print(f"[CHANGE REPORT] ERROR: {exc}")

    finally:
        client.close()


if __name__ == "__main__":
    main()
