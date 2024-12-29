from abc import ABC, abstractmethod
from typing import Callable, Dict, List, Set

from app.llm.ensemble import ReasoningLlmEnsembler
from app.models.tree import (
    InfoNodeSpec,
    InitialInfoGraph,
    InitialInfoGraphWithGoal,
    ProcessingNode,
)
from app.prompts import PROMPTS


class GraphGenerator(ABC):
    """
    Base class for graph generators. Handles validation and multiple LLM providers.
    Best to use the ReasoningLlmEnsembler for this.
    """

    def __init__(self, model_dict: Dict[str, List[str]], prompt_name: str):
        """Initialize with model configuration."""

        self.model_dict = model_dict

        self.system_prompt = PROMPTS["system"][prompt_name]
        self.user_prompt = PROMPTS["user"][prompt_name]

    @abstractmethod
    def generate_graph(self, *args, **kwargs) -> InitialInfoGraphWithGoal:
        """
        Generate a graph. Must be implemented by subclasses.

        Returns:
            Complete graph with original goal
        """
        pass

    def _validate_graph(self, graph: InitialInfoGraph) -> None:
        """
        Validate that the generated graph meets requirements.

        Args:
            graph: Graph to validate

        Raises:
            AssertionError if validation fails
        """

        assert graph.nodes, "Graph must have nodes"

        # Validate each node
        node_ids = set()
        for node in graph.nodes:
            self._validate_node(node, node_ids)
            node_ids.add(node.id)

    def _validate_node(self, node: InfoNodeSpec, existing_ids: Set[str]) -> None:
        """
        Validate a single node.

        Args:
            node: Node to validate
            existing_ids: Set of already seen node IDs

        Raises:
            AssertionError if validation fails
        """

        # Basic requirements
        assert node.id, "Node must have id"
        assert node.question, "Node must have question"
        assert node.rationale, "Node must have rationale"

        # Check for duplicate IDs
        assert node.id not in existing_ids, f"Duplicate node id: {node.id}"

        # Validate dependencies
        if node.depends_on_ids:
            for dep_id in node.depends_on_ids:
                assert dep_id in existing_ids, f"Dependency {dep_id} not found"

        # Validate by node type
        if node.node_type == "gather":
            assert node.gathering_method, "Gather node must have gathering method"
            if node.gathering_method == "web_search":
                assert node.search_queries, "Search node must have queries"

        elif node.node_type == "calculate":
            assert node.calculation_code, "Calculate node must have code"
            assert node.calculation_explanation, "Calculate node must have explanation"
            assert node.input_node_ids, "Calculate node must have input nodes"

    def _generate_sequential_graphs(
        self, messages_func: Callable, *args, **kwargs
    ) -> InitialInfoGraphWithGoal:
        """
        Generate graphs sequentially, with each LLM exploring new directions.

        Args:
            messages_func: Function that takes explored_nodes and returns messages
            *args, **kwargs: Additional arguments for messages_func

        Returns:
            Combined graph with all generated nodes
        """

        if not kwargs.get("goal"):
            raise ValueError("Goal is required for graph generation.")

        # Convert explored nodes from ProcessingNode to InfoNodeSpec
        # TODO: fairly sure I can do this with fewer conversions
        processed_nodes: List[ProcessingNode] = kwargs.pop("explored_nodes", [])
        all_nodes: List[InfoNodeSpec] = self._convert_processed_nodes(processed_nodes)

        # Process each provider
        # Each provider/model pair will handle a different part of the exploration
        for provider, models in self.model_dict.items():
            # Process each model
            for model in models:
                # For the graphs we're generating (key info and exploration), we're
                # looking to get a set of very useful and comprehensive directions
                # forward; we should use the best models to do this.
                llm_ensembler = ReasoningLlmEnsembler(
                    model_dict={provider: [model]}, response_format=InitialInfoGraph
                )

                # Convert InfoNodeSpec back to ProcessingNode for messages_func
                processing_nodes = self._convert_info_nodes(all_nodes)

                # Get messages for this model (may depend on previous results)
                messages = messages_func(
                    explored_nodes=processing_nodes, *args, **kwargs
                )

                # Generate graph from this model
                model_response = llm_ensembler.call_providers(messages)

                # Get the graph
                provider_graphs = list(model_response.values())
                if not provider_graphs:
                    continue

                model_graphs = provider_graphs[0]
                if not model_graphs:
                    continue

                graph = model_graphs[0]

                # Add nodes
                all_nodes.extend(graph.nodes)

        # Create final graph and validate it
        complete_graph = InitialInfoGraph(nodes=all_nodes)
        self._validate_graph(complete_graph)

        return InitialInfoGraphWithGoal(goal=kwargs.get("goal"), graph=complete_graph)

    def _convert_processed_nodes(
        self, processed_nodes: List[ProcessingNode]
    ) -> List[InfoNodeSpec]:
        """
        Convert a list of ProcessedNode to a list of InfoNodeSpec.

        Args:
            processed_nodes: List of ProcessedNode to convert

        Returns:
            List of InfoNodeSpec
        """

        return [
            InfoNodeSpec(
                id=node.id,
                question=node.question,
                rationale=node.rationale,
                node_type=node.node_type,
                depends_on_ids=node.depends_on_ids,
                gathering_method=node.gathering_method,
                search_queries=node.search_queries,
                calculation_code=node.calculation_code,
                calculation_explanation=node.calculation_explanation,
                input_node_ids=node.input_node_ids,
            )
            for node in processed_nodes
        ]

    def _convert_info_nodes(
        self, info_nodes: List[InfoNodeSpec]
    ) -> List[ProcessingNode]:
        """
        Convert a list of InfoNodeSpec to a list of ProcessingNode.

        Args:
            info_nodes: List of InfoNodeSpec to convert

        Returns:
            List of ProcessingNode
        """

        return [
            ProcessingNode(
                id=node.id,
                question=node.question,
                rationale=node.rationale,
                node_type=node.node_type,
                depends_on_ids=node.depends_on_ids,
                gathering_method=node.gathering_method,
                search_queries=node.search_queries,
                calculation_code=node.calculation_code,
                calculation_explanation=node.calculation_explanation,
                input_node_ids=node.input_node_ids,
            )
            for node in info_nodes
        ]
