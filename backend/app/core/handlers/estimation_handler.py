from typing import Dict, List

from app.llm.ensemble import ReasoningLlmEnsembler
from app.models.tree import Estimate
from app.prompts import PROMPTS


class EstimateHandler:
    """
    Generates ballpark estimates with clear reasoning when exact data isn't available.
    Best to use the ReasoningLlmEnsembler for this.
    """

    def __init__(self, model_dict: Dict[str, List[str]]):
        """Initialize estimation components."""

        assert len(model_dict.keys()) == 1, "Only one provider supported now"
        assert len(list(model_dict.values())[0]) == 1, "Only one model supported now"

        # The estimation that we're doing is probably better off being done by a model
        # that can reason about the problem, so we use the reasoning ensembler.
        self.llm_ensembler = ReasoningLlmEnsembler(
            model_dict=model_dict, response_format=Estimate
        )

        # Load prompts
        self.system_prompt = PROMPTS["system"]["estimation"]
        self.user_prompt = PROMPTS["user"]["estimation"]

    def generate_estimate(
        self,
        question: str,
        context: str,
        failed_searches: List[str],
        known_facts: Dict[str, str],
    ) -> Estimate:
        """
        Generate a reasoned estimate using first principles.

        Args:
            question: What we're trying to estimate
            context: Background context for the estimation
            failed_searches: Searches we tried that didn't yield results
            known_facts: Facts we do know that might help with estimation

        Returns:
            Estimate with value, reasoning, and assumptions
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
                        known_facts=self._format_facts(known_facts),
                    ),
                },
            ]
        )

        assert len(response.values()) == 1
        provider_response = list(response.values())[0]
        assert len(provider_response) == 1
        estimate = provider_response[0]
        assert estimate.value and estimate.reasoning and estimate.assumptions
        return estimate

    def _format_facts(self, facts: Dict[str, str]) -> str:
        """Format known facts for prompt."""
        return "\n".join(f"- {k}: {v}" for k, v in facts.items())
