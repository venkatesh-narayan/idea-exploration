from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class NodeType(str, Enum):
    """The type of operation this node performs"""

    GATHER = "gather"  # Leaf node that gathers raw information
    CALCULATE = "calculate"  # Performs calculation using inputs


class GatheringMethod(str, Enum):
    """How to gather information at a GATHER node"""

    WEB_SEARCH = "web_search"
    ASK_USER = "ask_user"


class SearchQuery(BaseModel):
    """A specific search query"""

    query: str = Field(description="The search query")
    context: str = Field(description="Why we're searching this")


# Models for OpenAI API Response
class InfoNodeSpec(BaseModel):
    """LLM's specification for an info node"""

    id: str = Field(description="Unique identifier for this node")
    question: str = Field(description="What we need to know")
    rationale: str = Field(description="Why we need this")
    node_type: NodeType = Field(description="What type of node this is")
    depends_on_ids: List[str] = Field(
        default_factory=list, description="IDs of nodes we need input from"
    )

    # For GATHER nodes
    gathering_method: Optional[GatheringMethod] = None
    search_queries: Optional[List[SearchQuery]] = None

    # For CALCULATE nodes
    calculation_code: Optional[str] = None
    calculation_explanation: Optional[str] = None
    input_node_ids: Optional[List[str]] = None


class InitialInfoGraph(BaseModel):
    """Complete LLM response for information gathering plan"""

    nodes: List[InfoNodeSpec] = Field(description="All nodes in the graph")


class InitialInfoGraphWithGoal(BaseModel):
    """Complete LLM response for information gathering plan"""

    goal: str = Field(description="Original user goal")
    graph: InitialInfoGraph = Field(description="All nodes in the graph")


# Models for Internal Processing
class SearchResult(BaseModel):
    """Result of a web search"""

    fact: str = Field(description="Found information")
    quote: str = Field(description="Supporting quote")


class SearchResultList(BaseModel):
    results: List[SearchResult] = Field(description="List of search results")


class SearchResultWithURL(BaseModel):
    """Result of a web search, with the URL."""

    search_result: SearchResult = Field(description="Search result")
    source_url: str = Field(description="Source URL")


class Estimate(BaseModel):
    """A ballpark estimate with reasoning"""

    value: str = Field(description="Estimated value")
    reasoning: str = Field(description="How we arrived at this")
    assumptions: List[str] = Field(description="Key assumptions made")


class NodeState(str, Enum):
    """Current state of a node"""

    PENDING = "pending"
    SEARCHING = "searching"
    NEEDS_BREAKDOWN = "needs_breakdown"  # Search failed, try breaking down
    NEEDS_ESTIMATE = "needs_estimate"  # Breakdown failed, need estimate
    CALCULATING = "calculating"
    COMPLETE = "complete"
    BLOCKED = "blocked"  # Waiting on dependencies


class BreakdownAttempt(BaseModel):
    """Single attempt to break down a failed search into more specific queries"""

    original_question: str = Field(description="Question that failed initial search")
    rationale: str = Field(description="Why this breakdown might help")
    new_nodes: List[InfoNodeSpec] = Field(description="More specific nodes to try")
    was_successful: bool = Field(description="Whether breakdown helped")


class FailedSearchAttempt(BaseModel):
    """
    If the search attempt failed, we try breaking it down again. If it still doesn't
    work, we use ballpark estimates.
    """

    breakdown_attempt: BreakdownAttempt
    search_results: List[SearchResultWithURL] = Field(default_factory=list)
    estimate: Optional[Estimate] = None


class ProcessingNode(BaseModel):
    """Internal representation of a node being processed"""

    # Basic info
    id: str = Field(description="Unique identifier")
    question: str = Field(description="What we need to know")
    rationale: str = Field(description="Why we need this")
    node_type: NodeType = Field(description="What type of node this is")
    state: NodeState = Field(default=NodeState.PENDING)

    # Dependencies
    depends_on_ids: List[str] = Field(default_factory=list)

    # For GATHER nodes
    gathering_method: Optional[GatheringMethod] = None
    search_queries: Optional[List[SearchQuery]] = None
    search_results: Optional[List[SearchResultWithURL]] = None
    estimate: Optional[Estimate] = None
    user_input: Optional[str] = None

    # For CALCULATE nodes
    calculation_code: Optional[str] = None
    calculation_explanation: Optional[str] = None
    input_node_ids: Optional[List[str]] = None
    calculation_result: Optional[str] = None

    # The final value at this node
    value: Optional[str] = None
    value_source: Optional[str] = None  # "search", "estimate", "calculation", "user"

    # Breakdown tracking
    breakdown_attempt: Optional[BreakdownAttempt] = None  # Only one attempt allowed

    # For UI
    display_order: int = Field(0)
    is_expanded: bool = Field(True)


class ProcessingGraph(BaseModel):
    """Internal graph for processing and tracking state"""

    goal: str = Field(description="Original user goal")
    nodes: List[ProcessingNode] = Field(description="All nodes being processed")
