import asyncio
import logging
from typing import Dict, List, Optional, Tuple

from app.core.graphs.exploration_generator import ExplorationGraphGenerator
from app.core.graphs.key_info_generator import KeyInfoGraphGenerator
from app.core.handlers.calculation_handler import CalculationHandler
from app.core.handlers.estimation_handler import EstimateHandler
from app.core.handlers.failed_search_breakdown_handler import (
    FailedSearchBreakdownHandler,
)
from app.core.handlers.search_handler import SearchHandler
from app.models.tree import (
    BreakdownAttempt,
    Estimate,
    InitialInfoGraphWithGoal,
    NodeState,
    ProcessingGraph,
    ProcessingNode,
)
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class IdeaAgent:
    """
    Main orchestrator that:
    1. Generates and processes key information needs
    2. Explores and analyzes potential solutions

    For backend testing.
    """

    def __init__(
        self,
        reasoning_model_dict: Dict[str, List[str]],
        normal_model_dict: Dict[str, List[str]],
        max_depth: int = 1,
    ):
        """Initialize all components needed for processing."""

        # Handlers
        self.search_handler = SearchHandler(normal_model_dict)
        self.estimate_handler = EstimateHandler(reasoning_model_dict)
        self.calculation_handler = CalculationHandler(normal_model_dict)
        self.failed_search_handler = FailedSearchBreakdownHandler(
            model_dict=reasoning_model_dict,
            search_handler=self.search_handler,
            estimate_handler=self.estimate_handler,
        )

        # Graph generators
        self.key_info_generator = KeyInfoGraphGenerator(reasoning_model_dict)
        self.exploration_generator = ExplorationGraphGenerator(reasoning_model_dict)

        # Configuration
        self.max_depth = max_depth

        # State tracking
        self.gathered_facts: Dict[str, str] = dict()
        self.key_info_graph: Optional[ProcessingGraph] = None
        self.exploration_graph: Optional[ProcessingGraph] = None

    def process_goal(
        self, goal: str, context: str
    ) -> Tuple[ProcessingGraph, ProcessingGraph]:
        """
        Process a user's goal from start to finish.

        Args:
            goal: The user's goal
            context: Additional context about the goal

        Returns:
            Tuple of:
            - Key info processing graph
            - Exploration processing graph
        """

        # Phase 1: Generate and process key information needs
        self.key_info_graph = self._gather_key_info(goal, context)

        # Phase 2: Explore potential solutions
        self.exploration_graph = self._explore_solutions(goal, context)

        return self.key_info_graph, self.exploration_graph

    def _gather_key_info(
        self, goal: str, context: str, verbose: bool = False
    ) -> ProcessingGraph:
        """Gather key information through multiple rounds."""

        all_processed_nodes: List[ProcessingNode] = []

        for depth in range(self.max_depth):
            # Generate graph for this depth
            info_graph = self.key_info_generator.generate_graph(
                goal=goal,
                context=self._create_depth_context(context, depth),
                known_facts=self.gathered_facts,
                explored_nodes=all_processed_nodes,
            )

            # Convert to processing graph
            processing_graph = self._create_processing_graph(info_graph)

            # Process all nodes at this depth
            self._process_graph(processing_graph)

            # Store processed nodes for next depth
            all_processed_nodes.extend(processing_graph.nodes)

            # If no new nodes were generated, we can stop
            if not processing_graph.nodes:
                break

            # Print verbose information if flag is set
            if verbose:
                self._print_processing_graph(processing_graph, depth)

        # Combine all nodes into final graph
        return ProcessingGraph(goal=goal, nodes=all_processed_nodes)

    def _explore_solutions(
        self, goal: str, context: str, verbose: bool = False
    ) -> ProcessingGraph:
        """Explore solutions through multiple rounds."""

        all_processed_nodes: List[ProcessingNode] = []

        for depth in range(self.max_depth):
            # Generate graph for this depth
            exploration_graph = self.exploration_generator.generate_graph(
                goal=goal,
                context=self._create_depth_context(context, depth),
                key_info=self.gathered_facts,
                explored_nodes=all_processed_nodes,
            )

            # Convert to processing graph
            processing_graph = self._create_processing_graph(exploration_graph)

            # Process all nodes at this depth
            self._process_graph(processing_graph)

            # Store processed nodes for next depth
            all_processed_nodes.extend(processing_graph.nodes)

            # If no new nodes were generated, we can stop
            if not processing_graph.nodes:
                break

            # Print verbose information if flag is set
            if verbose:
                self._print_processing_graph(processing_graph, depth)

        # Combine all nodes into final graph
        return ProcessingGraph(goal=goal, nodes=all_processed_nodes)

    def _print_processing_graph(self, graph: ProcessingGraph, depth: int) -> None:
        """Print the main information in the processing graph."""
        print(f"\nDepth {depth}: Processing Graph for goal '{graph.goal}'")
        for node in graph.nodes:
            print(f"Node ID: {node.id}")
            print(f"  Question: {node.question}")
            print(f"  Rationale: {node.rationale}")
            print(f"  Node Type: {node.node_type}")
            print(f"  State: {node.state}")
            print(f"  Value: {node.value}")
            print(f"  Value Source: {node.value_source}")
            print(f"  Depends On: {node.depends_on_ids}")
            print(f"  Gathering Method: {node.gathering_method}")
            print(f"  Search Queries: {node.search_queries}")
            print(f"  Calculation Code: {node.calculation_code}")
            print(f"  Calculation Explanation: {node.calculation_explanation}")
            print(f"  Input Node IDs: {node.input_node_ids}")
            print(f"  Calculation Result: {node.calculation_result}")
            print(f"  Breakdown Attempt: {node.breakdown_attempt}")
            print(f"  Estimate: {node.estimate}")
            print(f"  Search Results: {node.search_results}")
            print()

    def _create_depth_context(self, base_context: str, depth: int) -> str:
        """Create context string appropriate for the current depth."""

        context_parts = [base_context]

        # Add information about current depth
        context_parts.append(f"\nCurrent exploration depth: {depth}")

        # Add gathered information
        if self.gathered_facts:
            context_parts.append("\nInformation gathered so far:")
            for key, value in self.gathered_facts.items():
                context_parts.append(f"- {key}: {value}")

        return "\n".join(context_parts)

    def _create_processing_graph(
        self, info_graph: InitialInfoGraphWithGoal
    ) -> ProcessingGraph:
        """Convert info graph to processing graph."""

        processing_nodes = []
        for node in info_graph.graph.nodes:
            processing_nodes.append(
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
            )

        return ProcessingGraph(
            goal=info_graph.goal,
            nodes=processing_nodes,
        )

    def _process_graph(self, graph: ProcessingGraph) -> None:
        """
        Process all nodes in a graph.

        Handles:
        - Dependencies between nodes
        - Different node types (gather, calculate)
        - Failed searches
        - Updating gathered facts
        """

        while True:
            # Find nodes that are ready to process
            ready_nodes = self._get_ready_nodes(graph)
            if not ready_nodes:
                # If no nodes are ready and none are in progress,
                # we're done
                if not self._has_in_progress_nodes(graph):
                    break
                continue

            # Process ready nodes
            for node in ready_nodes:
                self._process_node(node, graph)

    def _get_ready_nodes(self, graph: ProcessingGraph) -> List[ProcessingNode]:
        """Get nodes that are ready to be processed."""

        ready_nodes = []
        for node in graph.nodes:
            if node.state != NodeState.PENDING:
                continue

            # Check if dependencies are complete
            deps_complete = True
            for dep_id in node.depends_on_ids:
                dep_node = next(n for n in graph.nodes if n.id == dep_id)
                if dep_node.state != NodeState.COMPLETE:
                    deps_complete = False
                    break

            if deps_complete:
                ready_nodes.append(node)

        return ready_nodes

    def _has_in_progress_nodes(self, graph: ProcessingGraph) -> bool:
        """Check if any nodes are still in progress."""

        in_progress_states = {
            NodeState.SEARCHING,
            NodeState.CALCULATING,
            NodeState.NEEDS_BREAKDOWN,
        }
        return any(node.state in in_progress_states for node in graph.nodes)

    def _process_node(self, node: ProcessingNode, graph: ProcessingGraph) -> None:
        """
        Process a single node based on its type.

        Updates node state and gathered facts.
        """

        try:
            if node.node_type == "gather":
                self._process_gather_node(node)
            elif node.node_type == "calculate":
                self._process_calculate_node(node, graph)

            # If we got a value, update gathered facts
            if node.value is not None:
                self.gathered_facts[node.question] = node.value

            node.state = NodeState.COMPLETE

        except Exception as e:
            print(f"Error processing node {node.id}: {str(e)}")
            node.state = NodeState.BLOCKED

    def _process_gather_node(self, node: ProcessingNode) -> None:
        """Process a gather node (search or user input)."""

        if node.gathering_method == "web_search":
            node.state = NodeState.SEARCHING
            results = self.search_handler.search_and_analyze(
                node.question, node.search_queries
            )

            if not results:
                # Try breaking down the search
                node.state = NodeState.NEEDS_BREAKDOWN
                failed_attempt = self.failed_search_handler.handle_failed_search(
                    question=node.question,
                    context=self._get_context_for_node(node),
                    failed_searches=[q.query for q in node.search_queries],
                    known_facts=self.gathered_facts,
                )

                node.breakdown_attempt = failed_attempt.breakdown_attempt

                if failed_attempt.search_results:
                    # Use results from breakdown
                    results = failed_attempt.search_results
                else:
                    # Use estimate
                    node.estimate = failed_attempt.estimate
                    node.value = failed_attempt.estimate.value
                    node.value_source = "estimate"

            # Extract value from search results
            facts = [r.search_result.fact for r in results]
            node.value = "; ".join(facts)
            node.value_source = "search"
            node.search_results = results

        elif node.gathering_method == "ask_user":
            # Set state to blocked until we get user input
            node.state = NodeState.BLOCKED
            # Wait for user to provide input through set_user_input
            # The orchestrator above will continue processing other nodes

    def _process_calculate_node(
        self, node: ProcessingNode, graph: ProcessingGraph
    ) -> None:
        """Process a calculate node."""

        node.state = NodeState.CALCULATING

        # Get input values from dependencies
        input_values = {}
        for input_id in node.input_node_ids:
            input_node = next(n for n in graph.nodes if n.id == input_id)
            input_values[input_id] = input_node.value

        # Generate and run calculation
        calculation = self.calculation_handler.generate_calculation(
            node.question, input_values
        )

        result = self.calculation_handler.execute_calculation(
            calculation, input_values
        )

        node.value = str(result.result)
        node.value_source = "calculation"
        node.calculation_result = result.result

    def _get_context_for_node(self, node: ProcessingNode) -> str:
        """Generate context string for a node."""
        return f"Attempting to answer: {node.question}\nRationale: {node.rationale}"

    def set_user_input(self, node_id: str, user_input: str) -> None:
        """
        Provide user input for a blocked node.

        Args:
            node_id: ID of the node waiting for input
            user_input: The user's response

        Raises:
            ValueError: If node doesn't exist or isn't waiting for input
        """

        for graph in [self.key_info_graph, self.exploration_graph]:
            if not graph:
                continue

            for node in graph.nodes:
                if node.id == node_id:
                    if (
                        node.state != NodeState.BLOCKED
                        or node.gathering_method != "ask_user"
                    ):
                        raise ValueError(
                            f"Node {node_id} is not waiting for user input"
                        )
                    node.value = user_input
                    node.value_source = "user"
                    node.state = NodeState.COMPLETE
                    self.gathered_facts[node.question] = user_input
                    return

        raise ValueError(f"Node {node_id} not found")


#######################################################################################


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = dict()

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket

    def disconnect(self, session_id: str):
        self.active_connections.pop(session_id, None)

    async def send_update(self, session_id: str, data: dict):
        if websocket := self.active_connections.get(session_id):
            await websocket.send_json(data)


class WebSocketIdeaAgent(IdeaAgent):
    def __init__(self, session_id: str, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.manager = ConnectionManager()
        self.session_id = session_id

    async def process_goal(self, goal: str, context: str):
        """Override to send initial graphs after generation."""

        # Generate initial graphs
        key_info_graph = self.key_info_generator.generate_graph(
            goal=goal,
            context=context,
            known_facts=self.gathered_facts,
            explored_nodes=[],
        )

        key_info_processing_graph = self._create_processing_graph(key_info_graph)

        # Send initial key info graph
        await self.manager.send_update(
            self.session_id,
            {
                "type": "initial_key_info_graph",
                "graph": key_info_processing_graph.model_dump(),
            },
        )

        # Generate exploration graph
        exploration_graph = self.exploration_generator.generate_graph(
            goal=goal, context=context, key_info=self.gathered_facts, explored_nodes=[]
        )

        exploration_processing_graph = self._create_processing_graph(exploration_graph)

        # Send initial exploration graph
        await self.manager.send_update(
            self.session_id,
            {
                "type": "initial_exploration_graph",
                "graph": exploration_processing_graph.model_dump(),
            },
        )

        # Process graphs (with updates for each node)
        # await self._process_graph(key_info_graph)
        await self._process_graph(exploration_graph)

        return key_info_graph, exploration_graph

    async def _process_node(self, node: ProcessingNode, graph: ProcessingGraph):
        """Override to send updates at each step of node processing."""

        try:
            # Send state update before processing
            await self._send_node_state_update(node)

            if node.node_type == "gather":
                if node.gathering_method == "web_search":
                    node.state = NodeState.SEARCHING
                    await self._send_node_state_update(node)

                    results = self.search_handler.search_and_analyze(
                        node.question, node.search_queries
                    )

                    if not results:
                        # Try breaking down the search
                        node.state = NodeState.NEEDS_BREAKDOWN
                        await self._send_node_state_update(node)

                        failed_attempt = (
                            self.failed_search_handler.handle_failed_search(
                                question=node.question,
                                context=self._get_context_for_node(node),
                                failed_searches=[q.query for q in node.search_queries],
                                known_facts=self.gathered_facts,
                            )
                        )

                        # Send breakdown nodes
                        await self._send_breakdown_update(
                            failed_attempt.breakdown_attempt, node.id
                        )

                        if failed_attempt.search_results:
                            results = failed_attempt.search_results
                        else:
                            # Send estimate node
                            await self._send_estimate_update(
                                failed_attempt.estimate, node.id
                            )
                            node.estimate = failed_attempt.estimate
                            node.value = failed_attempt.estimate.value
                            node.value_source = "estimate"
                            await self._send_node_value_update(node)
                            return

                    # Update with search results
                    node.value = "; ".join(r.search_result.fact for r in results)
                    node.value_source = "search"
                    node.search_results = results
                    await self._send_node_value_update(node)

            elif node.gathering_method == "ask_user":
                # Set state to blocked until we get user input
                node.state = NodeState.BLOCKED
                await self._send_node_state_update(node)

                # The process will pause here until set_user_input is called
                # The frontend will show a prompt for user input
                return

            elif node.node_type == "calculate":
                node.state = NodeState.CALCULATING
                await self._send_node_state_update(node)

                # Get input values from dependencies
                input_values = {}
                for input_id in node.input_node_ids:
                    input_node = next(n for n in graph.nodes if n.id == input_id)
                    input_values[input_id] = input_node.value

                # Generate and run calculation
                calculation = self.calculation_handler.generate_calculation(
                    node.question, input_values
                )

                result = self.calculation_handler.execute_calculation(
                    calculation, input_values
                )

                node.value = str(result.result)
                node.value_source = "calculation"
                node.calculation_result = result.result

                # Send updates for calculation results
                await self._send_node_value_update(node)

            node.state = NodeState.COMPLETE
            await self._send_node_state_update(node)

        except Exception as e:
            logger.error(f"Error processing node {node.id}: {str(e)}")
            node.state = NodeState.BLOCKED
            await self._send_node_state_update(node)

    async def _send_node_state_update(self, node: ProcessingNode):
        """Send update when node state changes."""

        await self.manager.send_update(
            self.session_id,
            {"type": "node_state_update", "node_id": node.id, "state": node.state},
        )

    async def _send_node_value_update(self, node: ProcessingNode):
        """Send update when node gets a value."""

        await self.manager.send_update(
            self.session_id,
            {
                "type": "node_value_update",
                "node_id": node.id,
                "value": node.value,
                "value_source": node.value_source,
                "search_results": [res.model_dump() for res in node.search_results],
                "calculation_result": node.calculation_result,
            },
        )

    async def _send_breakdown_update(
        self, breakdown: BreakdownAttempt, parent_id: str
    ):
        """Send update when new breakdown nodes are created."""

        update = {
            "type": "breakdown_nodes",
            "parent_id": parent_id,
            "question": breakdown.original_question,
            "rationale": breakdown.rationale,
        }
        if breakdown.new_nodes:
            update["nodes"] = [n.model_dump() for n in breakdown.new_nodes]

        await self.manager.send_update(self.session_id, update)

    async def _send_estimate_update(self, estimate: Estimate, parent_id: str):
        """Send update when estimation node is created."""

        await self.manager.send_update(
            self.session_id,
            {
                "type": "estimate_node",
                "parent_id": parent_id,
                "estimate": estimate.model_dump(),
            },
        )

    async def set_user_input(self, node_id: str, user_input: str):
        """Handle user input for a blocked node."""

        # Find the node in either graph
        node = None
        graph = None

        if self.key_info_graph:
            for n in self.key_info_graph.nodes:
                if n.id == node_id:
                    node = n
                    graph = self.key_info_graph
                    break

        if not node and self.exploration_graph:
            for n in self.exploration_graph.nodes:
                if n.id == node_id:
                    node = n
                    graph = self.exploration_graph
                    break

        if not node:
            raise ValueError(f"Node {node_id} not found")

        if node.state != NodeState.BLOCKED or node.gathering_method != "ask_user":
            raise ValueError(f"Node {node_id} is not waiting for user input")

        # Set the value
        node.value = user_input
        node.value_source = "user"

        # Send value update
        await self._send_node_value_update(node)

        # Update state to complete
        node.state = NodeState.COMPLETE
        await self._send_node_state_update(node)

        # Add to gathered facts
        self.gathered_facts[node.question] = user_input

        # Continue processing the graph
        # Find nodes that were waiting on this one
        if graph:
            dependent_nodes = [
                n
                for n in graph.nodes
                if node_id in n.depends_on_ids and n.state == NodeState.PENDING
            ]

            # Process them
            for dep_node in dependent_nodes:
                await self._process_node(dep_node, graph)

    async def _process_graph(self, graph: InitialInfoGraphWithGoal):
        """Process all nodes in a graph with user input handling."""

        # Convert to processing graph
        processing_graph = self._create_processing_graph(graph)

        while True:
            # Find nodes that are ready to process
            ready_nodes = self._get_ready_nodes(processing_graph)
            if not ready_nodes:
                # If no nodes are ready and none are blocked or in progress,
                # we're done
                if not self._has_active_nodes(processing_graph):
                    break
                await asyncio.sleep(0.1)  # Small delay to prevent busy waiting
                continue

            # Process ready nodes
            for node in ready_nodes:
                await self._process_node(node, processing_graph)

                # If node is blocked (waiting for user input), pause processing
                if node.state == NodeState.BLOCKED:
                    break

    def _has_active_nodes(self, graph: ProcessingGraph) -> bool:
        """Check if any nodes are still active (in progress or blocked)."""

        active_states = {
            NodeState.SEARCHING,
            NodeState.CALCULATING,
            NodeState.NEEDS_BREAKDOWN,
            NodeState.BLOCKED,
        }
        return any(node.state in active_states for node in graph.nodes)
