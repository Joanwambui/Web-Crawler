import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from fastapi_app.main import app
from fastapi_app.routes.books import books_col, changes_col


# ------------------------------------------------------
# Fake Cursor — behaves like pymongo cursor for tests
# ------------------------------------------------------
class FakeCursor:
    def __init__(self, data):
        self.data = data

    def skip(self, n):
        return FakeCursor(self.data[n:])

    def limit(self, n):
        return FakeCursor(self.data[:n])

    def sort(self, *args, **kwargs):
        # pymongo returns a cursor after .sort()
        return self

    def __iter__(self):
        return iter(self.data)

    def __len__(self):
        return len(self.data)   # ✔ FIX: required for JSON serialization


# ------------------------------------------------------
# FIXTURE — Mocks MongoDB collections
# ------------------------------------------------------
@pytest.fixture
def client():

    # -----------------------
    # Mock BOOKS collection
    # -----------------------
    books_col.find = MagicMock(return_value=FakeCursor([
        {
            "_id": "123",
            "title": "Test Book",
            "category": "Fiction",
            "price_incl_tax": "£20.00",
            "price_excl_tax": "£18.00",
            "availability": "In stock (5 available)",
            "rating": 4,
            "number_of_reviews": 12
        }
    ]))

    books_col.count_documents = MagicMock(return_value=1)

    books_col.find_one = MagicMock(return_value={
        "_id": "123",
        "title": "Test Book",
        "category": "Fiction",
        "price_incl_tax": "£20.00",
        "availability": "In stock (5 available)",
        "rating": 4,
        "number_of_reviews": 9
    })

    # -----------------------
    # Mock CHANGES collection
    # -----------------------
    changes_col.find = MagicMock(return_value=FakeCursor([
        {
            "_id": "chg123",
            "book_id": "123",
            "type": "updated",
            "old": {"price_incl_tax": "£25.00"},
            "new": {"price_incl_tax": "£20.00"},
            "timestamp": "2025-11-12T00:00:00"
        }
    ]))

    return TestClient(app)


# ------------------------------------------------------
# TEST 1 — GET /books (basic)
# ------------------------------------------------------
def test_get_books_basic(client):
    response = client.get("/books/?x-api-key=supersecretapikey")
    assert response.status_code == 200

    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["title"] == "Test Book"


# ------------------------------------------------------
# TEST 2 — GET /books?category=
# ------------------------------------------------------
def test_get_books_category_filter(client):
    response = client.get("/books/?category=Fiction&x-api-key=supersecretapikey")
    assert response.status_code == 200

    data = response.json()
    assert data["items"][0]["category"] == "Fiction"


# ------------------------------------------------------
# TEST 3 — GET /books?rating=
# ------------------------------------------------------
def test_get_books_rating_filter(client):
    response = client.get("/books/?rating=4&x-api-key=supersecretapikey")
    assert response.status_code == 200

    data = response.json()
    assert data["items"][0]["rating"] == 4


# ------------------------------------------------------
# TEST 4 — GET /books/{id}
# ------------------------------------------------------
def test_get_single_book(client):
    response = client.get("/books/123?x-api-key=supersecretapikey")
    assert response.status_code == 200
    assert response.json()["title"] == "Test Book"


# ------------------------------------------------------
# TEST 5 — GET /books/changes
# ------------------------------------------------------
def test_get_changes(client):
    response = client.get("/books/changes?x-api-key=supersecretapikey")
    assert response.status_code == 200

    data = response.json()
    assert data["count"] == 1          # ✔ will pass
    assert data["items"][0]["type"] == "updated"


# ------------------------------------------------------
# TEST 6 — Missing API Key
# ------------------------------------------------------
def test_missing_api_key(client):
    response = client.get("/books/")
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or missing API key"


# ------------------------------------------------------
# TEST 7 — Rate Limit Exceeded
# ------------------------------------------------------
def test_rate_limit(client):
    from fastapi_app.routes.books import _requests

    _requests["supersecretapikey"] = {
        "count": 100,
        "window_start": 9999999999
    }

    response = client.get("/books/?x-api-key=supersecretapikey")
    assert response.status_code == 429
    assert "Rate limit exceeded" in response.json()["detail"]
