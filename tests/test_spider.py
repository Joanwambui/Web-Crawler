# tests/test_spider.py

import pytest
from scrapy.http import HtmlResponse, Request
#from books.books.spiders.book_spider import BookSpider
from books.books.spiders.book_spider import BookSpider



# ---------------------------------------------------------
# Utility: Build a fake Scrapy HTML response
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
# TEST 1 — parse(): Extract book links + pagination
# ---------------------------------------------------------
def test_parse_extracts_book_links_and_pagination():
    spider = BookSpider()

    html = """
    <html>
      <body>
        <article class="product_pod">
          <h3><a href="book_1.html">Book 1</a></h3>
        </article>

        <ul class="pager">
            <li class="next"><a href="page-2.html">next</a></li>
        </ul>
      </body>
    </html>
    """

    response = fake_response("https://books.toscrape.com/", html)

    results = list(spider.parse(response))

    assert len(results) == 2
    assert results[0].url.endswith("book_1.html")
    assert results[1].url.endswith("page-2.html")


# ---------------------------------------------------------
# TEST 2 — parse_book_page(): Extract all fields
# ---------------------------------------------------------
def test_parse_book_page_extracts_all_fields():
    spider = BookSpider()

    # ✔ FIXED: breadcrumb structure now matches spider logic
    html = """
    <html>
      <body>
        <ul class="breadcrumb">
          <li>Home</li>
          <li><a>Poetry</a></li>
          <li>Book</li>
        </ul>

        <div class="product_main">
            <h1>A Light in the Attic</h1>
            <p class="star-rating Three"></p>
        </div>

        <table>
          <tr><th>Price (excl. tax)</th><td>£51.77</td></tr>
          <tr><th>Price (incl. tax)</th><td>£53.77</td></tr>
          <tr><th>Availability</th><td>In stock (22 available)</td></tr>
          <tr><th>Number of reviews</th><td>5</td></tr>
        </table>

        <div id="product_description"></div>
        <p>This is a great book.</p>

        <div class="item active">
            <img src="/media/cache/fe/8c/fe8c.jpg" />
        </div>
      </body>
    </html>
    """

    response = fake_response(
        "https://books.toscrape.com/book_999/index.html",
        html
    )

    results = list(spider.parse_book_page(response))
    assert len(results) == 1

    item = results[0]

    assert item["title"] == "A Light in the Attic"
    assert item["category"] == "Poetry"          # ✔ FIXED
    assert item["rating"] == 3
    assert item["price_excl_tax"] == "£51.77"
    assert item["price_incl_tax"] == "£53.77"
    assert item["availability"] == "In stock (22 available)"
    assert item["number_of_reviews"] == "5"
    assert item["description"] == "This is a great book."
    assert item["image_url"].endswith("fe8c.jpg")
    assert item["url"].endswith("book_999/index.html")

    # Metadata checks
    assert "_id" in item
    assert "content_hash" in item
    assert "crawl_timestamp" in item
    assert item["status"] == "new"


# ---------------------------------------------------------
# TEST 3 — extract_rating()
# ---------------------------------------------------------
def test_extract_rating_from_css_class():
    spider = BookSpider()

    html = """
    <html>
        <p class="star-rating Five"></p>
    </html>
    """

    response = fake_response("https://example.com", html)

    assert spider.extract_rating(response) == 5


# ---------------------------------------------------------
# TEST 4 — Missing rating returns None
# ---------------------------------------------------------
def test_extract_rating_missing():
    spider = BookSpider()

    html = "<html></html>"
    response = fake_response("https://example.com", html)

    assert spider.extract_rating(response) is None


# ---------------------------------------------------------
# TEST 5 — extract_table_value()
# ---------------------------------------------------------
def test_extract_table_value():
    spider = BookSpider()

    html = """
    <html>
        <table>
            <tr><th>Price (incl. tax)</th><td>£39.99</td></tr>
        </table>
    </html>
    """

    response = fake_response("https://example.com", html)
    value = spider.extract_table_value(response, "Price (incl. tax)")

    assert value == "£39.99"
