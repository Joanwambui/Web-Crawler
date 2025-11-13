# books/spiders/book_spider.py

import hashlib
from datetime import datetime

import scrapy

#from books.items import BooksItem
from books.items import BooksItem





class BookSpider(scrapy.Spider):
    """
    Spider: BookSpider

    Purpose:
        - Crawl all books from https://books.toscrape.com
        - Extract detailed information for each book page
        - Handle pagination and transient errors gracefully
        - Store metadata and raw HTML for change detection

    Crawled fields:
        url, source_url, title, description, category,
        rating, price_excl_tax, price_incl_tax,
        availability, number_of_reviews, image_url,
        raw_html, _id, content_hash, crawl_timestamp, status
    """

    name = "book_spider"
    allowed_domains = ["books.toscrape.com"]
    start_urls = ["https://books.toscrape.com/"]

    # Extra per-spider settings (global ones are in settings.py)
    custom_settings = {
        "DOWNLOAD_DELAY": 1.0,
        "RETRY_TIMES": 3,
    }

    # ------------------------------------------------------------------
    # Startup (compatible with Scrapy 2.13+)
    # ------------------------------------------------------------------
    def start_requests(self):
        """
        Generate initial requests. Kept explicit so we can attach errback.
        Scrapy will also call `start()` in newer versions, which delegates to this.
        """
        for url in self.start_urls:
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                errback=self.log_error,
            )

    async def start(self):
        """
        Scrapy 2.13+ coroutine entrypoint.
        Delegates to start_requests() for compatibility.
        """
        for req in self.start_requests():
            yield req

    # ------------------------------------------------------------------
    # List pages: extract book links + follow pagination
    # ------------------------------------------------------------------
    def parse(self, response):
        """Parse the listing page, schedule detail pages, and follow next page."""

        # 1) Detail pages
        for book in response.css("article.product_pod"):
            relative_url = book.css("h3 a::attr(href)").get()
            if not relative_url:
                continue

            yield response.follow(
                relative_url,
                callback=self.parse_book_page,
                errback=self.log_error,
            )

        # 2) Pagination
        next_page = response.css("li.next > a::attr(href)").get()
        if next_page:
            self.logger.info(f"Navigating to next page: {next_page}")
            yield response.follow(
                next_page,
                callback=self.parse,
                errback=self.log_error,
            )

    # ------------------------------------------------------------------
    # Detail page: extract all required fields
    # ------------------------------------------------------------------
    def parse_book_page(self, response):
        """Extract structured data for a single book page."""
        item = BooksItem()

        # Core URLs / metadata
        item["url"] = response.url
        item["source_url"] = response.url

        # Title & category
        item["title"] = response.css(".product_main h1::text").get(default="").strip()
        item["category"] = response.css(
            "ul.breadcrumb li:nth-last-child(2) a::text"
        ).get(default="").strip()

        # Rating (convert "Three" -> 3)
        item["rating"] = self.extract_rating(response)

        # Table values
        item["price_excl_tax"] = self.extract_table_value(
            response, "Price (excl. tax)"
        )
        item["price_incl_tax"] = self.extract_table_value(
            response, "Price (incl. tax)"
        )
        item["availability"] = self.extract_table_value(
            response, "Availability"
        )
        item["number_of_reviews"] = self.extract_table_value(
            response, "Number of reviews"
        )

        # Description
        item["description"] = response.css(
            "#product_description ~ p::text"
        ).get(default="").strip()

        # Image URL
        img_src = response.css("div.item.active img::attr(src)").get()
        item["image_url"] = response.urljoin(img_src) if img_src else None

        # Raw HTML snapshot for fallback
        item["raw_html"] = response.text

        # ------------------------------------------------------------------
        # Hashes + metadata for change detection (used by MongoPipeline)
        # ------------------------------------------------------------------
        # Stable deduplication key
        item["_id"] = hashlib.sha256(item["url"].encode("utf-8")).hexdigest()

        # Content hash: only fields we care about for change detection
        content_string = (
            f"{item['title']}"
            f"{item['price_incl_tax']}"
            f"{item['availability']}"
            f"{item['description']}"
            f"{item['category']}"
        )
        item["content_hash"] = hashlib.sha256(
            content_string.encode("utf-8")
        ).hexdigest()

        # Metadata
        item["crawl_timestamp"] = datetime.utcnow().isoformat()
        item["status"] = "new"  # Pipeline may later update to "updated"/"unchanged"

        yield item

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def extract_rating(self, response):
        """Convert star-rating CSS class into numeric rating."""
        rating_class = response.css("p.star-rating::attr(class)").get()
        if not rating_class:
            return None

        rating_text = rating_class.replace("star-rating", "").strip()
        mapping = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}
        return mapping.get(rating_text)

    def extract_table_value(self, response, label: str) -> str:
        """Pull a value from the product table by label, with a safe default."""
        selector = f'//th[text()="{label}"]/following-sibling::td/text()'
        return response.xpath(selector).get(default="").strip()

    def log_error(self, failure):
        """Log failed requests for debugging and monitoring."""
        self.logger.error(f"Request failed: {repr(failure)}")
