from hashlib import sha256
from typing import Dict, List, Optional

from app.caching.base import FileCache
from app.models.cache import OpenAICallRecord


class OpenAIFileCache(FileCache):
    """Make sure to store `OpenAICallRecord` objects in the cache."""

    def __init__(self, cache_file: str = "openai_cache.json"):
        super().__init__(cache_file, OpenAICallRecord)

    def get(self, key: str) -> Optional[OpenAICallRecord]:
        return super().get(key)

    def set(self, key: str, value: OpenAICallRecord) -> None:
        super().set(key, value)

    def make_key_for_messages(
        self, engine_name: str, messages: List[Dict[str, str]]
    ) -> str:
        """
        Combine role + content from message chain, then hash it.
        """

        combined = f"{engine_name}||"
        for msg in messages:
            combined += f"{msg['role']}:{msg['content']}||"

        return sha256(combined.encode("utf-8")).hexdigest()
