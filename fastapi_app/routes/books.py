from fastapi import APIRouter, Query, Depends, HTTPException, Request
from pymongo import MongoClient
from typing import Optional
from enum import Enum
import os
import re
import time

router = APIRouter(prefix="/books", tags=["Books"])

# ------------------------------------------------------------
# MongoDB connection
# ------------------------------------------------------------
mongo_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
mongo_db = os.getenv("MONGODB_DB_NAME", "books_db")

client = MongoClient(mongo_url)
db = client[mongo_db]

books_col = db["books"]
changes_col = db["books_changes"]

# ------------------------------------------------------------
# API KEY + RATE LIMIT SETTINGS
# ------------------------------------------------------------
API_KEY = os.getenv("API_KEY", "supersecretapikey")
RATE_LIMIT = int(os.getenv("RATE_LIMIT_PER_HOUR", "100"))
WINDOW_SECONDS = 3600
_request_counters = {}  # {api_key: (window_start_ts, count)}


# This version keeps the field visible as "x-api-key" in Swagger
def verify_api_key(x_api_key: str = Query(..., alias="x-api-key")):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return x_api_key


def rate_limiter(api_key: str = Depends(verify_api_key)):
    now = time.time()
    window_start, count = _request_counters.get(api_key, (now, 0))

    # Reset window
    if now - window_start > WINDOW_SECONDS:
        _request_counters[api_key] = (now, 1)
        return api_key

    # Limit exceeded
    if count >= RATE_LIMIT:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Max {RATE_LIMIT} requests per hour."
        )

    _request_counters[api_key] = (window_start, count + 1)
    return api_key


# ------------------------------------------------------------
# Data cleaning
# ------------------------------------------------------------
def clean_book_data(book: dict) -> dict:
    cleaned = {}
    for field, value in book.items():
        if isinstance(value, str):
            v = " ".join(value.replace('"', "").replace("'", "").split()).strip()
            if field in ["category", "availability"]:
                v = v.title()
            cleaned[field] = v
        else:
            cleaned[field] = value
    return cleaned


# ------------------------------------------------------------
# Enums
# ------------------------------------------------------------
class SortOptions(str, Enum):
    rating_asc = "rating_asc"
    rating_desc = "rating_desc"
    price_asc = "price_asc"
    price_desc = "price_desc"
    reviews_asc = "reviews_asc"
    reviews_desc = "reviews_desc"


class RatingOptions(int, Enum):
    one = 1
    two = 2
    three = 3
    four = 4
    five = 5


# ------------------------------------------------------------
# GET /books — filtering, sorting, pagination
# ------------------------------------------------------------
@router.get(
    "/",
    dependencies=[Depends(rate_limiter)],
    summary="List books with filters and pagination"
)
async def list_books(
    category: Optional[str] = Query(None),
    rating: Optional[RatingOptions] = Query(None),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    min_reviews: Optional[int] = Query(None, ge=0),
    max_reviews: Optional[int] = Query(None, ge=0),
    sort_by: Optional[SortOptions] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    query = {"category": {"$ne": "Add a comment"}}

    if category:
        query["category"] = {
            "$regex": f"^{re.escape(category)}$",
            "$options": "i"
        }

    if rating:
        query["rating"] = int(rating)

    expr_filters = []

    # Price filter
    if min_price is not None or max_price is not None:
        expr_filters.append({
            "$and": [
                {"$gte": [{"$toDouble": {"$replaceAll": {
                    "input": "$price_incl_tax",
                    "find": "£", "replacement": ""
                }}}, min_price or 0]},
                {"$lte": [{"$toDouble": {"$replaceAll": {
                    "input": "$price_incl_tax",
                    "find": "£", "replacement": ""
                }}}, max_price or 999999]}
            ]
        })

    # Review filter
    if min_reviews is not None or max_reviews is not None:
        expr_filters.append({
            "$and": [
                {"$gte": [{"$toInt": {"$ifNull": ["$number_of_reviews", "0"]}}, min_reviews or 0]},
                {"$lte": [{"$toInt": {"$ifNull": ["$number_of_reviews", "0"]}}, max_reviews or 999999]}
            ]
        })

    if expr_filters:
        query["$expr"] = {"$and": expr_filters}

    # Pagination
    skip = (page - 1) * page_size
    total = books_col.count_documents(query)

    books = list(books_col.find(query).skip(skip).limit(page_size))

    # Sorting
    if sort_by:
        reverse = sort_by.value.endswith("desc")

        if "rating" in sort_by.value:
            books.sort(key=lambda b: int(b.get("rating", 0)), reverse=reverse)
        elif "price" in sort_by.value:
            books.sort(key=lambda b: float(
                re.sub(r"[£,]", "", b.get("price_incl_tax", "0"))
            ), reverse=reverse)
        elif "reviews" in sort_by.value:
            books.sort(key=lambda b: int(
                b.get("number_of_reviews", 0)
            ), reverse=reverse)

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [clean_book_data(b) for b in books]
    }


# ------------------------------------------------------------
# GET /books/{book_id}
# ------------------------------------------------------------
@router.get(
    "/{book_id}",
    dependencies=[Depends(rate_limiter)],
    summary="Get book details"
)
async def get_book(book_id: str):
    book = books_col.find_one({"_id": book_id})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return clean_book_data(book)


# ------------------------------------------------------------
# GET /books/changes
# ------------------------------------------------------------
@router.get(
    "/changes",
    dependencies=[Depends(rate_limiter)],
    summary="Get recent change logs"
)
async def get_changes(limit: int = Query(50, ge=1, le=500)):
    changes = list(
        changes_col.find().sort("timestamp", -1).limit(limit)
    )
    return {"count": len(changes), "items": changes}
