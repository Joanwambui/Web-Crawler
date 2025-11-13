from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, HttpUrl, field_validator
import re


class BookOut(BaseModel):
    """
    API representation of a single book document from MongoDB.
    """
    id: str = Field(alias="_id")
    url: HttpUrl
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    price_incl_tax: Optional[str] = None
    price_excl_tax: Optional[str] = None
    availability: Optional[str] = None
    number_of_reviews: Optional[int] = None
    image_url: Optional[HttpUrl] = None
    rating: Optional[int] = None
    status: Optional[str] = None
    crawl_timestamp: Optional[datetime] = None
    last_seen: Optional[datetime] = None

    # Validate prices using regex
    @field_validator("price_incl_tax", "price_excl_tax")
    @classmethod
    def validate_price(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return v
        if not re.match(r"^£\d+(\.\d{2})?$", v.strip()):
            raise ValueError("Price must look like £12.34")
        return v

    class Config:
        allow_population_by_field_name = True
        json_schema_extra = {
            "example": {
                "_id": "d3f8a7e8a0",
                "url": "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
                "title": "A Light in the Attic",
                "category": "Poetry",
                "price_incl_tax": "£51.77",
                "availability": "In stock (22 available)",
                "rating": 3,
                "number_of_reviews": 5
            }
        }


class ChangeLogOut(BaseModel):
    """
    API representation of a change log entry from books_changes collection.
    """
    id: str = Field(alias="_id")
    book_id: str
    type: str
    old: Optional[Dict[str, Any]] = None
    new: Optional[Dict[str, Any]] = None
    timestamp: datetime

    class Config:
        allow_population_by_field_name = True
        json_schema_extra = {
            "example": {
                "_id": "c9f3a74f12",
                "book_id": "a1b2c3d4",
                "type": "updated",
                "old": {"price_incl_tax": "£45.00"},
                "new": {"price_incl_tax": "£39.00"},
                "timestamp": "2025-11-11T09:00:00Z"
            }
        }


class BooksPage(BaseModel):
    """
    Paginated list of books.
    """
    total: int
    page: int
    page_size: int
    items: List[BookOut]
