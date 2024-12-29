from typing import Dict, List, Optional

from app.core.graphs.base import GraphGenerator
from app.models.tree import InitialInfoGraphWithGoal, ProcessingNode


class KeyInfoGraphGenerator(GraphGenerator):
    """
    Generates graph of essential information needed for a goal,
    regardless of implementation approach.
    """

    def __init__(self, model_dict: Dict[str, List[str]]):
        """Initialize key info generator components."""
        super().__init__(model_dict=model_dict, prompt_name="key_info_generation")

    def generate_graph(
        self,
        goal: str,
        context: str,
        known_facts: Dict[str, str],
        explored_nodes: Optional[List[ProcessingNode]] = None,
    ) -> InitialInfoGraphWithGoal:
        """
        Generate graph of essential information needs.

        Args:
            goal: The user's original goal
            context: Additional context about the goal
            known_facts: Facts we've gathered so far
            explored_nodes: Nodes that have been explored (from previous depths)

        Returns:
            Tree of information nodes we need to gather
        """

        explored_nodes = explored_nodes or []

        def create_messages(*args, **kwargs):
            return [
                {"role": "system", "content": self.system_prompt},
                {
                    "role": "user",
                    "content": self.user_prompt.format(
                        goal=kwargs.get("goal"),
                        context=kwargs.get("context"),
                        known_facts=self._format_dict(kwargs.get("known_facts", {})),
                        explored_nodes=self._format_explored_nodes(
                            kwargs.get("explored_nodes", [])
                        ),
                    ),
                },
            ]

        return self._generate_sequential_graphs(
            messages_func=create_messages,
            goal=goal,
            context=context,
            known_facts=known_facts,
            explored_nodes=explored_nodes,
        )

    def _format_dict(self, d: Dict[str, str]) -> str:
        """Format dictionary for prompt."""

        if not d:
            return "No information gathered yet."
        return "\n".join(f"- {k}: {v}" for k, v in d.items())

    def _format_explored_nodes(self, nodes: List[ProcessingNode]) -> str:
        """Format explored nodes for prompt."""

        if not nodes:
            return "No nodes explored yet."

        formatted = []
        for node in nodes:
            formatted.append(f"- Question: {node.question}")
            formatted.append(f"  Rationale for question: {node.rationale}")
            formatted.append(f"  Node Type: {node.node_type}")
            if node.depends_on_ids:
                formatted.append(
                    f"  Depends on nodes: {', '.join(node.depends_on_ids)}"
                )
            if node.value:
                formatted.append(f"  Value: {node.value}")

            formatted.append("")  # Empty line between nodes

        return "\n".join(formatted)
