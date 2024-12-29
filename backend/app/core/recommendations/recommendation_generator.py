from typing import Dict, List

from app.llm.ensemble import ReasoningLlmEnsembler
from app.models.recommendation import RecommendationSet
from app.models.tree import ProcessingGraph
from app.prompts import PROMPTS


class RecommendationGenerator:
    """
    Analyzes key information and exploration results to generate
    concrete recommendations.
    Best to use the ReasoningLlmEnsembler for this, since the graphs may be pretty
    complex, and we want to really give the best recommendations to the user with
    good reasons for why we're recommending them.
    """

    def __init__(self, model_dict: Dict[str, List[str]]):
        """Initialize recommendation components."""

        assert len(model_dict.keys()) == 1, "Only one provider supported now"
        assert len(list(model_dict.values())[0]) == 1, "Only one model supported now"

        self.llm_ensembler = ReasoningLlmEnsembler(
            model_dict=model_dict, response_format=RecommendationSet
        )

        self.system_prompt = PROMPTS["system"]["recommendation"]
        self.user_prompt = PROMPTS["user"]["recommendation"]

    def generate_recommendations(
        self,
        key_info_graph: ProcessingGraph,
        exploration_graph: ProcessingGraph,
    ) -> RecommendationSet:
        """
        Generate recommendations based on gathered information and explored solutions.

        Args:
            key_info_graph: Graph with all gathered key information
            exploration_graph: Graph with explored solution approaches

        Returns:
            Set of recommendations with rationale
        """

        # Format our gathered information
        key_info = self._format_graph_results(key_info_graph)
        explored_approaches = self._format_graph_results(exploration_graph)

        # Generate recommendations
        response = self.llm_ensembler.call_providers(
            messages=[
                {"role": "system", "content": self.system_prompt},
                {
                    "role": "user",
                    "content": self.user_prompt.format(
                        goal=key_info_graph.goal,
                        key_info=key_info,
                        explored_approaches=explored_approaches,
                    ),
                },
            ]
        )

        assert len(response.values()) == 1
        provider_response = list(response.values())[0]
        assert len(provider_response) == 1
        recommendation_set = provider_response[0]
        assert recommendation_set.primary_recommendation
        return recommendation_set

    def _format_graph_results(self, graph: ProcessingGraph) -> str:
        """Format graph results for prompt."""

        lines = []
        for node in graph.nodes:
            if not node.value:
                continue

            lines.append(f"Question: {node.question}")
            lines.append(f"Answer: {node.value}")
            lines.append(f"Source: {node.value_source}")

            if node.search_results:
                lines.append("Supporting Evidence:")
                for result in node.search_results:
                    lines.append(f"  - {result.search_result.fact}")
                    lines.append(f"    Quote: {result.search_result.quote}")
                    lines.append(f"    Source: {result.source_url}")

            if node.estimate:
                lines.append("Estimation Details:")
                lines.append(f"  Reasoning: {node.estimate.reasoning}")
                lines.append("  Assumptions:")
                for assumption in node.estimate.assumptions:
                    lines.append(f"    - {assumption}")

            lines.append("")  # Empty line between nodes

        return "\n".join(lines)
