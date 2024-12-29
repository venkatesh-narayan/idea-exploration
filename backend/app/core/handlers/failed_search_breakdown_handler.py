from typing import Dict, List

from app.core.handlers.estimation_handler import EstimateHandler
from app.core.handlers.search_handler import SearchHandler
from app.llm.ensemble import ReasoningLlmEnsembler
from app.models.tree import BreakdownAttempt, FailedSearchAttempt, SearchResultWithURL
from app.prompts import PROMPTS


class FailedSearchBreakdownHandler:
    """
    Handles breaking down failed searches into more specific questions.
    If breakdown searches fail, falls back to estimation.
    Best to use the ReasoningLlmEnsembler for this.
    """

    def __init__(
        self,
        model_dict: Dict[str, List[str]],
        search_handler: SearchHandler,
        estimate_handler: EstimateHandler,
    ):
        """Initialize breakdown components."""

        assert len(model_dict.keys()) == 1, "Only one provider supported now"
        assert len(list(model_dict.values())[0]) == 1, "Only one model supported now"

        # The breakdowns we're doing are probably better off being done by a model
        # that can reason about the problem, so we use the reasoning ensembler.
        self.llm_ensembler = ReasoningLlmEnsembler(
            model_dict=model_dict, response_format=BreakdownAttempt
        )
        self.search_handler = search_handler
        self.estimate_handler = estimate_handler

        # Load prompts
        self.system_prompt = PROMPTS["system"]["breakdown"]
        self.user_prompt = PROMPTS["user"]["breakdown"]

    def handle_failed_search(
        self,
        question: str,
        context: str,
        failed_searches: List[str],
        known_facts: Dict[str, str],
    ) -> FailedSearchAttempt:
        """
        Handle a failed search by breaking it down and trying again.
        If breakdown fails, generate estimate.

        Args:
            question: The question we're trying to answer
            context: Background context
            failed_searches: Previous searches that failed
            known_facts: Facts we know that might help

        Returns:
            Tuple of:
            - The breakdown attempt (what we tried)
            - Any search results we got (empty list if none)
            - Estimate if breakdown failed (None if breakdown succeeded)
        """

        # Generate breakdown plan
        breakdown = self.generate_search_breakdown(
            question=question,
            context=context,
            failed_searches=failed_searches,
            known_facts=known_facts,
        )

        # Track any new failed searches
        all_failed_searches = failed_searches.copy()

        # Try searches for each new node
        all_results: List[SearchResultWithURL] = []
        for node in breakdown.new_nodes:
            if node.search_queries:
                node_results = self.search_handler.search_and_analyze(
                    question=node.question, search_queries=node.search_queries
                )
                if node_results:
                    all_results.extend(node_results)
                else:
                    # Track failed searches
                    all_failed_searches.extend(
                        query.query for query in node.search_queries
                    )

        # If we found useful information
        if all_results:
            breakdown.was_successful = True
            return FailedSearchAttempt(
                breakdown_attempt=breakdown, search_results=all_results, estimate=None
            )

        # If breakdown failed, fall back to estimation
        estimate = self.estimate_handler.generate_estimate(
            question=question,
            context=context,
            failed_searches=all_failed_searches,
            known_facts=known_facts,
        )

        breakdown.was_successful = False
        return FailedSearchAttempt(
            breakdown_attempt=breakdown, search_results=[], estimate=estimate
        )

    def generate_search_breakdown(
        self,
        question: str,
        context: str,
        failed_searches: List[str],
        known_facts: Dict[str, str],
    ) -> BreakdownAttempt:
        """
        Generate a plan for breaking down a question into more specific parts.

        Args:
            question: What we're trying to find out
            context: Background context
            failed_searches: Searches that have failed
            known_facts: Facts we know that might help

        Returns:
            BreakdownAttempt with strategy and specific nodes to try
        """

        response = self.llm_ensembler.call_providers(
            messages=[
                {"role": "system", "content": self.system_prompt},
                {
                    "role": "user",
                    "content": self.user_prompt.format(
                        question=question,
                        context=context,
                        failed_searches="\n".join(f"- {s}" for s in failed_searches),
                        known_facts="\n".join(
                            f"- {k}: {v}" for k, v in known_facts.items()
                        ),
                    ),
                },
            ]
        )

        assert len(response.values()) == 1
        provider_response = list(response.values())[0]
        assert len(provider_response) == 1
        breakdown_attempt = provider_response[0]
        assert (
            breakdown_attempt.original_question
            and breakdown_attempt.rationale
            and breakdown_attempt.new_nodes
        )
        return breakdown_attempt
