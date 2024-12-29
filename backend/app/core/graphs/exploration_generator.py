from typing import Dict, List, Optional

from app.core.graphs.base import GraphGenerator
from app.models.tree import InitialInfoGraphWithGoal, ProcessingNode


class ExplorationGraphGenerator(GraphGenerator):
    """
    Generates graph of solution approaches to explore, analyzing their viability
    using gathered key information.
    """

    def __init__(self, model_dict: Dict[str, List[str]]):
        """Initialize exploration graph generator components."""
        super().__init__(model_dict=model_dict, prompt_name="exploration_generation")

    def generate_graph(
        self,
        goal: str,
        context: str,
        key_info: Dict[str, str],
        explored_nodes: Optional[List[ProcessingNode]] = None,
    ) -> InitialInfoGraphWithGoal:
        """
        Generate graph of solution approaches to explore.

        Args:
            goal: The user's original goal
            context: Additional context about the goal
            key_info: Essential information we've gathered (affects viability)
            explored_nodes: Nodes we've already explored (from previous depths)

        Returns:
            Graph of nodes exploring different solution approaches
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
                        key_info=self._format_dict(kwargs.get("key_info", {})),
                        explored_approaches=self._format_explored_approaches(
                            kwargs.get("explored_nodes", [])
                        ),
                    ),
                },
            ]

        return self._generate_sequential_graphs(
            messages_func=create_messages,
            goal=goal,
            context=context,
            key_info=key_info,
            explored_nodes=explored_nodes,
        )

    def _format_dict(self, d: Dict[str, str]) -> str:
        """Format dictionary for prompt."""

        if not d:
            return "No key information gathered yet."
        return "\n".join(f"- {k}: {v}" for k, v in d.items())

    def _format_explored_approaches(self, nodes: List[ProcessingNode]) -> str:
        """Format explored approaches for prompt, including what we've learned."""

        if not nodes:
            return "No approaches explored yet."

        approaches = []

        # Create a mapping from node ID to node
        node_map = {node.id: node for node in nodes}

        # Function to recursively gather all nodes in a line of reasoning
        def gather_line_of_reasoning(node_id, visited, level=0):
            if node_id in visited:
                return []
            visited.add(node_id)
            node = node_map.get(node_id)
            if not node:
                return []
            line = [(node, level)]
            for dep_id in node.depends_on_ids:
                line.extend(gather_line_of_reasoning(dep_id, visited, level + 1))
            return line

        # Find all main nodes (nodes with no dependencies)
        main_nodes = [node for node in nodes if not node.depends_on_ids]

        # Gather lines of reasoning starting from each main node
        for main_node in main_nodes:
            visited = set()
            line_of_reasoning = gather_line_of_reasoning(main_node.id, visited)
            approach_info = [f"Approach: {main_node.question}"]
            approach_info.append(f"Rationale for approach: {main_node.rationale}")

            # Add what we've learned
            findings = ["Findings:"]
            for node, level in line_of_reasoning:
                indent = "  " * level
                formatted_node = (
                    f"{indent}- ID: {node.id}\n{indent}  Question: {node.question}"
                )
                if node.value:  # If we've learned something
                    formatted_node += f": {node.value}"
                if node.depends_on_ids:  # Include dependencies if they exist
                    dependencies = ", ".join(node.depends_on_ids)
                    formatted_node += f" (depends on: {dependencies})"

                findings.append(formatted_node)

            if findings:
                approach_info.extend(findings)

            approach_info.append("")  # Empty line between approaches
            approaches.extend(approach_info)

        return "\n".join(approaches)
