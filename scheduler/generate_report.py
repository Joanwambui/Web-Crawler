"""
generate_report.py — CSV ONLY VERSION
-------------------------------------

Daily change report generator for BooksToScrape.

This script:
    • Filters ONLY by books_changes.date == YYYY-MM-DD
    • Generates ONLY CSV output (JSON removed)
    • Includes MongoDB debug logs
    • Handles ObjectId → string conversion safely
"""

import argparse
import csv
import os
import logging
from datetime import datetime, UTC
from typing import Dict, Any, List, Tuple

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from bson import ObjectId
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ---------------------------------------------------------------------
# Logging
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
# MongoDB Helpers
# ---------------------------------------------------------------------
def safe_value(v):
    """Convert ObjectId → str for CSV."""
    if isinstance(v, ObjectId):
        return str(v)
    return v


def get_mongo() -> Tuple[MongoClient, Database, Collection, Collection]:
    mongo_uri = os.getenv("MONGODB_URI")
    mongo_db = os.getenv("MONGODB_DB_NAME")

    print("[DEBUG] Loading MongoDB connection...")
    print(f"[DEBUG] MONGODB_URI: {mongo_uri}")
    print(f"[DEBUG] MONGODB_DB_NAME: {mongo_db}")

    if not mongo_uri:
        raise RuntimeError("MONGODB_URI missing from .env!")
    if not mongo_db:
        raise RuntimeError("MONGODB_DB_NAME missing from .env!")

    client = MongoClient(mongo_uri)

    print("[DEBUG] Pinging MongoDB Atlas...")
    client.admin.command("ping")
    print("[DEBUG] MongoDB connection successful ✓")

    db = client[mongo_db]

    if "books_changes" in db.list_collection_names():
        print("[DEBUG] books_changes collection found ✓")
    else:
        print("[WARNING] books_changes collection NOT found!")

    return client, db, db["books"], db["books_changes"]


# ---------------------------------------------------------------------
# Date Handling
# ---------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", help="YYYY-MM-DD. Defaults to today.")
    return parser.parse_args()


def get_report_date(args: argparse.Namespace) -> str:
    if args.date:
        return args.date.strip()
    return datetime.now(UTC).strftime("%Y-%m-%d")


# ---------------------------------------------------------------------
# Fetch changes by EXACT date
# ---------------------------------------------------------------------
def fetch_changes_by_date(changes_col: Collection, report_date: str) -> List[Dict[str, Any]]:
    print(f"\n[DEBUG] Querying books_changes for date={report_date}")

    results = list(changes_col.find({"date": report_date}))

    print(f"[DEBUG] Query returned {len(results)} documents")
    return results


# ---------------------------------------------------------------------
# CSV Helpers
# ---------------------------------------------------------------------
def normalize_change_row(change: Dict[str, Any]) -> Dict[str, Any]:
    """Flatten Mongo change document into CSV-safe row."""
    change_fields = change.get("changes", {})

    row = {
        "book_id": safe_value(change.get("book_id")),
        "type": change.get("type", ""),
        "date": change.get("date", ""),
        "timestamp": str(change.get("timestamp", "")),
    }

    for field, diff in change_fields.items():
        row[f"{field}_old"] = safe_value(diff.get("old"))
        row[f"{field}_new"] = safe_value(diff.get("new"))

    return row


def write_csv(changes: List[Dict[str, Any]], report_date: str) -> str:
    path = os.path.join(REPORTS_DIR, f"daily_changes_{report_date}.csv")

    if not changes:
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["status", "details"])
            writer.writerow(["none", "No changes found"])
        return path

    normalized = [normalize_change_row(c) for c in changes]
    fieldnames = sorted({k for row in normalized for k in row.keys()})

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(normalized)

    return path


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------
def main():
    args = parse_args()
    report_date = get_report_date(args)

    print("\n======================================")
    print(f"     DAILY REPORT FOR {report_date}")
    print("======================================\n")

    client, db, books_col, changes_col = get_mongo()

    try:
        changes = fetch_changes_by_date(changes_col, report_date)

        if not changes:
            print("[CHANGE REPORT] No changes found.")
            return

        print(f"[DEBUG] Preparing CSV with {len(changes)} entries...")

        csv_path = write_csv(changes, report_date)

        print("\n[CHANGE REPORT] CSV Generated Successfully!")
        print(f"[CSV]  {csv_path}")

    finally:
        client.close()


if __name__ == "__main__":
    main()
