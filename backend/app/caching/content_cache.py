from hashlib import sha256
from typing import Optional

from app.caching.base import FileCache
from app.models.cache import URLScrapeRecord


class ContentFileCache(FileCache):
    """Make sure to store `URLScrapeRecord` objects in the cache."""

    def __init__(self, cache_file: str = "content_cache.json"):
        super().__init__(cache_file, URLScrapeRecord)

    def get(self, key: str) -> Optional[URLScrapeRecord]:
        return super().get(key)

    def set(self, key, value: URLScrapeRecord) -> None:
        super().set(key, value)

    def make_key_for_messages(self, url: str) -> str:
        """
        Combine role + content from message chain, then hash it.
        """

        return sha256(url.encode("utf-8")).hexdigest()
