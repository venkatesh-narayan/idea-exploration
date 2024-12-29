from hashlib import sha256
from typing import Dict, List

from app.caching.base import FileCache
from app.models.cache import PerplexityCallRecord


class PerplexityFileCache(FileCache):
    """Make sure to store `PerplexityCallRecord` objects in the cache."""

    def __init__(self, cache_file: str = "perplexity_cache.json"):
        super().__init__(cache_file, PerplexityCallRecord)

    def get(self, key: str) -> PerplexityCallRecord:
        return super().get(key)

    def set(self, key: str, value: PerplexityCallRecord) -> None:
        super().set(key, value)

    def make_key_for_messages(self, model: str, messages: List[Dict[str, str]]) -> str:
        """
        Combine role + content from message chain, then hash it.
        """

        combined = f"{model}||"
        for msg in messages:
            combined += f"{msg['role']}:{msg['content']}||"

        return sha256(combined.encode("utf-8")).hexdigest()
