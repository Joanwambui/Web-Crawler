# tests/test_utils.py

import pytest
from scrapy.http import HtmlResponse, Request

# Import utilities from your actual code
from fastapi_app.routes.books import clean_book_data

from books.books.spiders.book_spider import BookSpider



# ---------------------------------------------------------
# Utility: Build fake Scrapy HTML response
# ---------------------------------------------------------
def fake_response(url: str, html: str):
    request = Request(url=url)
    response = HtmlResponse(
        url=url,
        request=request,
        body=html,
        encoding="utf-8"
    )
    return response


# ---------------------------------------------------------
# TEST 1 — clean_book_data()
# ---------------------------------------------------------
def test_clean_book_data_normalizes_strings():

    raw = {
        "title": "  The 'Great' Book  ",
        "category": "fiCTion",
        "availability": " in stock (5 available) ",
        "rating": 5
    }

    cleaned = clean_book_data(raw)

    assert cleaned["title"] == "The Great Book"
    assert cleaned["category"] == "Fiction"     # .title() expected
    assert cleaned["availability"] == "In Stock (5 Available)"
    assert cleaned["rating"] == 5                # non-strings unchanged


# ---------------------------------------------------------
# TEST 2 — extract_table_value()
# ---------------------------------------------------------
def test_extract_table_value_finds_correct_value():
    spider = BookSpider()

    html = """
    <html>
      <table>
        <tr><th>Price (incl. tax)</th><td>£39.99</td></tr>
        <tr><th>Price (excl. tax)</th><td>£35.99</td></tr>
      </table>
    </html>
    """

    response = fake_response("https://example.com", html)

    assert spider.extract_table_value(response, "Price (incl. tax)") == "£39.99"
    assert spider.extract_table_value(response, "Price (excl. tax)") == "£35.99"


# ---------------------------------------------------------
# TEST 3 — extract_table_value() returns None if missing
# ---------------------------------------------------------
def test_extract_table_value_missing_returns_none():
    spider = BookSpider()

    html = "<html><table></table></html>"
    response = fake_response("https://example.com", html)

    assert spider.extract_table_value(response, "Nonexistent Field") == ""



# ---------------------------------------------------------
# TEST 4 — extract_rating()
# ---------------------------------------------------------
def test_extract_rating_parses_css_class():
    spider = BookSpider()

    html = """
    <html>
      <p class="star-rating Four"></p>
    </html>
    """
    response = fake_response("https://example.com", html)

    assert spider.extract_rating(response) == 4


# ---------------------------------------------------------
# TEST 5 — extract_rating() returns None when missing
# ---------------------------------------------------------
def test_extract_rating_returns_none_when_missing():
    spider = BookSpider()

    html = "<html></html>"
    response = fake_response("https://example.com", html)

    assert spider.extract_rating(response) is None
