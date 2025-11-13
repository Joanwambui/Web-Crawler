# tests/test_api.py

from fastapi.testclient import TestClient
from fastapi_app.main import app

client = TestClient(app)


def test_app_starts():
    """API should start successfully."""
    response = client.get("/docs")
    assert response.status_code == 200


def test_books_route_exists():
    """Books router should be registered from main.py."""
    response = client.get("/books/")
    # because API key is missing, we expect 401
    assert response.status_code in [401, 422]


def test_openapi_loads():
    """Ensure the custom OpenAPI schema generates without errors."""
    response = client.get("/openapi.json")
    assert response.status_code == 200

    data = response.json()
    assert "paths" in data
    assert "/books/" in data["paths"]
