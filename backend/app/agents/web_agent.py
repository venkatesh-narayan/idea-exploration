import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional

import requests
from app.caching import ContentFileCache, PerplexityFileCache
from app.models.cache import PerplexityCallRecord, URLScrapeRecord
from bs4 import BeautifulSoup
from readability import Document

logger = logging.getLogger(__name__)


class WebAgent:
    """
    Provides:
        1) A 'search' method that queries Perplexity.
        2) A 'scrape_citations' method that fetches the cited pages concurrently.
    """

    def __init__(
        self,
        perplexity_model: str = "llama-3.1-sonar-large-128k-online",
        perplexity_request_timeout: int = 30,
        scrape_citations_timeout: int = 10,
    ):
        self.api_key = os.getenv("PERPLEXITY_API_KEY")
        self.perplexity_model = perplexity_model
        self.perplexity_cache = PerplexityFileCache()
        self.content_cache = ContentFileCache()
        self.perplexity_request_timeout = perplexity_request_timeout
        self.scrape_citations_timeout = scrape_citations_timeout
        self.perplexity_url = "https://api.perplexity.ai/chat/completions"

    def search(self, query: str) -> List[str]:
        """Queries Perplexity. Returns a list of URLs (citations from Perplexity)."""

        messages = [
            {
                "role": "system",
                "content": "Be specific and precise. Follow every detail in the query",
            },
            {"role": "user", "content": query},
        ]
        cache_key = self.perplexity_cache.make_key_for_messages(
            model=self.perplexity_model, messages=messages
        )
        cached = self.perplexity_cache.get(cache_key)
        if cached:
            logger.info(f"Perplexity cache hit for query: {query}")
            return cached.citations

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        response = requests.post(
            url=self.perplexity_url,
            headers=headers,
            json={
                "model": self.perplexity_model,
                "messages": messages,
                "temperature": 0,
            },
            timeout=self.perplexity_request_timeout,
        )
        if response.status_code != 200:
            raise Exception(
                "Perplexity search request failed with status "
                f"{response.status_code}: {response.text}"
            )

        data = response.json()
        answer = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        citations = data.get("citations", [])

        perplexity_record = PerplexityCallRecord(
            model=self.perplexity_model,
            messages=messages,
            citations=citations,
            response=data,
            answer=answer,
        )

        logger.info(f"Setting Perplexity cache for query {query}...")
        self.perplexity_cache.set(cache_key, perplexity_record)
        logger.info(f"Perplexity cache set for query {query}")

        return citations

    def scrape_citations(self, citations: List[str]) -> List[URLScrapeRecord]:
        """
        Concurrently scrape each URL from the results.
        Return a dict: {url -> text_content}
        """

        def fetch(url: str) -> Optional[URLScrapeRecord]:
            cache_key = self.content_cache.make_key_for_messages(url)
            cached = self.content_cache.get(cache_key)
            if cached:
                return cached

            try:
                resp = requests.get(url, timeout=self.scrape_citations_timeout)
                if resp.status_code == 200:
                    # Use readability for main content extraction
                    doc = Document(resp.text)
                    readable_text = doc.summary()

                    # Clean up the text
                    soup = BeautifulSoup(readable_text, "html.parser")
                    clean_text = soup.get_text(separator="\n", strip=True)

                    record = URLScrapeRecord(url=url, content=clean_text)
                    self.content_cache.set(cache_key, record)
                    return record
                else:
                    print(url, f"Error with URL {url}: status {resp.status_code}")
                    return None

            except Exception as e:
                print(f"Exception for url {url}: {e}")
                return None

        content: List[URLScrapeRecord] = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(fetch, url) for url in citations]

        for f in as_completed(futures):
            result = f.result()
            if result:
                content.append(result)

        return content
