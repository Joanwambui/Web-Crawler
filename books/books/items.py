# books/items.py
import scrapy

class BooksItem(scrapy.Item):
    # Unique identifier for deduplication & change detection
    _id = scrapy.Field()              # SHA256 hash of URL
    content_hash = scrapy.Field()     # SHA256 hash of main content (for change detection)

    # Core scraped data
    url = scrapy.Field()
    title = scrapy.Field()
    description = scrapy.Field()
    category = scrapy.Field()
    rating = scrapy.Field()
    number_of_reviews = scrapy.Field()
    image_url = scrapy.Field()

    # Pricing details
    price_excl_tax = scrapy.Field()
    price_incl_tax = scrapy.Field()
    availability = scrapy.Field()

    # Metadata
    crawl_timestamp = scrapy.Field()  # When the crawl occurred
    status = scrapy.Field()           # e.g., "new", "updated", "unchanged"
    source_url = scrapy.Field()       # URL where the item was scraped from
    raw_html = scrapy.Field()         # Store raw HTML snapshot for fallback
    last_seen = scrapy.Field()