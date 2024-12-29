from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class URLScrapeRecord(BaseModel):
    """Record of the content from scraping a URL."""

    url: str
    content: str


class OpenAICallRecord(BaseModel):
    """Record of a OpenAI API call and response."""

    model: str
    messages: List[Dict[str, str]]
    structured_output_dict: Dict[str, Any]  # structured output (BaseModel --> dict)
    reasoning_output: Optional[str] = None  # reasoning output (str)


class PerplexityCallRecord(BaseModel):
    """Record of a Perplexity API call and response."""

    model: str
    citations: List[str]
    messages: List[Dict[str, str]]
    response: Dict[str, Any]  # full response from API
    answer: str
