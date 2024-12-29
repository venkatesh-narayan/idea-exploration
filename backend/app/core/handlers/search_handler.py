import logging
from typing import Dict, List

import tenacity
from app.agents.web_agent import WebAgent
from app.caching import OpenAIFileCache
from app.llm.ensemble import NormalLlmEnsembler
from app.models.tree import SearchQuery, SearchResultList, SearchResultWithURL
from app.prompts import PROMPTS

logger = logging.getLogger(__name__)


class SearchHandler:
    """
    Handles web searches and analyzes results to determine if they actually
    answer our questions.
    Best to use the NormalLlmEnsembler for this.
    """

    def __init__(
        self,
        model_dict: Dict[str, List[str]],
        perplexity_model: str = "llama-3.1-sonar-large-128k-online",
        perplexity_request_timeout: int = 30,
        scrape_citations_timeout: int = 10,
    ):
        """Initialize search and analysis components."""

        assert len(model_dict.keys()) == 1, "Only one provider supported now"
        assert len(list(model_dict.values())[0]) == 1, "Only one model supported now"

        self.web_agent = WebAgent(
            perplexity_model=perplexity_model,
            perplexity_request_timeout=perplexity_request_timeout,
            scrape_citations_timeout=scrape_citations_timeout,
        )

        # For analyzing search results
        # The evaluations we're doing should be relatively simple, so we can use the
        # normal LLM ensembler.
        self.llm_ensembler = NormalLlmEnsembler(
            model_dict=model_dict, response_format=SearchResultList
        )

        # Cache for analysis results
        self.cache = OpenAIFileCache(cache_file="search_analysis_cache.json")

        # Load prompts
        self.system_prompt = PROMPTS["system"]["content_analysis"]
        self.user_prompt = PROMPTS["user"]["content_analysis"]

    def search_and_analyze(
        self, question: str, search_queries: List[SearchQuery]
    ) -> List[SearchResultWithURL]:
        """
        Execute searches and analyze results to determine if they answer our question.

        Args:
            question: The original question we're trying to answer
            search_queries: List of search queries to try

        Returns:
            List of valid SearchResults that help answer the question.
            Empty list if no useful results found.
        """

        # Execute all searches
        citations = []
        for query in search_queries:
            logger.info(f"Searching for: {query.query}")
            citations.extend(self.web_agent.search(query.query))

        if not citations:
            logger.info("No citations found")
            return []

        # Scrape content from citations
        logger.info(f"Scraping content from {len(citations)} citations")
        content = self.web_agent.scrape_citations(citations)

        if not content:
            return []

        # Analyze content in parallel with retries
        logger.info(f"Analyzing content from {len(content)} pages")
        results = [
            self._analyze_content_with_retry(
                question=question, content=page.content, source_url=page.url
            )
            for page in content
        ]

        # Flatten results list and remove empty results
        all_results = [
            result
            for sublist in results
            if sublist  # Handle None from failed retries
            for result in sublist
        ]

        return all_results

    @tenacity.retry(
        stop=tenacity.stop_after_attempt(3),
        wait=tenacity.wait_exponential(multiplier=1, min=4, max=10),
        retry=tenacity.retry_if_exception_type(Exception),
    )
    def _analyze_content_with_retry(
        self, question: str, content: str, source_url: str
    ) -> List[SearchResultWithURL]:
        """Analyze content with retry logic."""
        try:
            response = self.llm_ensembler.call_providers(
                [
                    {"role": "system", "content": self.system_prompt},
                    {
                        "role": "user",
                        "content": self.user_prompt.format(
                            question=question, content=content
                        ),
                    },
                ]
            )

            results_with_url = []
            assert len(response.values()) == 1
            provider_response = list(response.values())[0]
            assert len(provider_response) == 1
            search_results = provider_response[0]

            for result in search_results.results:
                results_with_url.append(
                    SearchResultWithURL(search_result=result, source_url=source_url)
                )

            return results_with_url

        except Exception as e:
            print(f"Error analyzing content from {source_url}: {str(e)}")
            raise
