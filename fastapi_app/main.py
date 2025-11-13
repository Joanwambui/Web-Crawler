import os
from pathlib import Path
from dotenv import load_dotenv

# ------------------------------------------------------------
# Load .env BEFORE anything else
# ------------------------------------------------------------
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

print("DEBUG MONGO_URL =", os.getenv("MONGODB_URL"))
print("DEBUG MONGO_DB =", os.getenv("MONGODB_DB_NAME"))

# ------------------------------------------------------------
# Create MongoDB connection ONCE here (shared across all modules)
# ------------------------------------------------------------
from pymongo import MongoClient

mongo_url = os.getenv("MONGODB_URL")
mongo_db = os.getenv("MONGODB_DB_NAME")

if not mongo_url or not mongo_db:
    raise RuntimeError("MongoDB environment variables missing. Check your .env file.")

client = MongoClient(mongo_url)
db = client[mongo_db]

# ------------------------------------------------------------
# FastAPI app setup
# ------------------------------------------------------------
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi_app.routes import books

app = FastAPI(
    title="BooksToScrape Monitoring API",
    version="1.0.0",
    description="Production-style API exposing books and change logs from the Scrapy + MongoDB pipeline."
)

# Register routes
app.include_router(books.router)


# ------------------------------------------------------------
# Custom OpenAPI Schema (including dropdown categories)
# ------------------------------------------------------------
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    from fastapi_app.main import db  # safe import
    books_col = db["books"]

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    # Auto-fill category dropdown
    try:
        categories = sorted(
            {
                c.strip().title()
                for c in books_col.distinct("category")
                if isinstance(c, str) and c.strip()
            }
        )

        paths = openapi_schema.get("paths", {})
        books_get = paths.get("/books/", {}).get("get", {})

        if "parameters" in books_get:
            for param in books_get["parameters"]:
                if param.get("name") == "category":
                    param["schema"]["enum"] = categories
                    param["description"] = "Select a category (auto-filled from MongoDB)"
                    break

        app.openapi_schema = openapi_schema

    except Exception as e:
        print(f"[OpenAPI Injection Error] {e}")

    return app.openapi_schema


app.openapi = custom_openapi
