import fcntl
import json
import os
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import BaseModel


@contextmanager
def file_lock(lock_path: str, timeout: int = 5):
    """
    File locking context manager using fcntl.
    Works on Linux and OSX.

    Args:
        lock_path: Path to the lock file
        timeout: Maximum time to wait for lock in seconds
    """
    start_time = time.time()
    lock_file = None

    try:
        while True:
            try:
                # Open or create lock file
                lock_file = open(lock_path, "w")

                # Try to acquire lock without blocking
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break  # Lock acquired

            except BlockingIOError:
                # Lock not acquired
                if lock_file:
                    lock_file.close()
                    lock_file = None

                if time.time() - start_time > timeout:
                    raise TimeoutError(
                        f"Could not acquire lock after {timeout} seconds"
                    )

                time.sleep(0.1)  # Short sleep before retry

        try:
            yield
        finally:
            if lock_file:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
                lock_file.close()

    finally:
        # Clean up lock file
        try:
            if lock_file:
                lock_file.close()
            if os.path.exists(lock_path):
                os.unlink(lock_path)
        except OSError:
            pass


class FileCache:
    """Thread-safe JSON file-based cache for storing data."""

    def __init__(self, cache_file: str, value_format: BaseModel):
        self.cache_file = Path(cache_file)
        self.value_format = value_format
        self.cache_data: Dict[str, BaseModel] = dict()

        # Create lock file path
        self.lock_path = str(self.cache_file) + ".lock"

        self._ensure_cache_dir()
        self._load_cache()

    def _ensure_cache_dir(self):
        """Ensure cache directory exists."""
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)

    def _load_cache(self):
        """Load cache data with file locking."""
        if not self.cache_file.is_file():
            return

        with file_lock(self.lock_path):
            try:
                with open(self.cache_file, "r") as f:
                    json_cache: Dict[str, Dict[str, Any]] = json.load(f)
                    self.cache_data = {
                        k: self.value_format.model_validate(v)
                        for k, v in json_cache.items()
                    }
            except json.JSONDecodeError:
                self.cache_data = dict()
            except Exception as e:
                print(f"Error loading cache: {str(e)}")
                self.cache_data = dict()

    def get(self, key: str) -> Optional[BaseModel]:
        """Thread-safe get operation."""
        return self.cache_data.get(key)

    def set(self, key: str, value: BaseModel) -> None:
        """Thread-safe set operation."""
        # Update in-memory data
        self.cache_data[key] = value

        # Write to file with lock
        with file_lock(self.lock_path):
            try:
                with open(self.cache_file, "w") as f:
                    json_cache: Dict[str, Dict[str, Any]] = {
                        k: v.model_dump() for k, v in self.cache_data.items()
                    }
                    json.dump(json_cache, f, indent=4)
            except Exception as e:
                print(f"Error saving to cache: {str(e)}")
                # Remove from memory if we couldn't save
                if key in self.cache_data:
                    del self.cache_data[key]
                raise

    def make_key_for_messages(self, messages: list) -> str:
        """Generate cache key from messages. Must be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement this method")
