export enum NodeType {
    GATHER = 'gather',
    CALCULATE = 'calculate',
}

export enum NodeState {
    PENDING = 'pending',
    SEARCHING = 'searching',
    NEEDS_BREAKDOWN = 'needs_breakdown',
    NEEDS_ESTIMATE = 'needs_estimate',
    CALCULATING = 'calculating',
    COMPLETE = 'complete',
    BLOCKED = 'blocked',
}

export enum GatheringMethod {
    WEB_SEARCH = 'web_search',
    ASK_USER = 'ask_user',
}

export interface SearchQuery {
    query: string;
    context: string;
}

export interface SearchResult {
    fact: string;
    quote: string;
}

export interface SearchResultWithURL {
    search_result: SearchResult;
    source_url: string;
}

export interface Estimate {
    value: string;
    reasoning: string;
    assumptions: string[];
}

export interface BreakdownNode {
    question: string;
    gathering_method?: GatheringMethod;
    search_queries?: SearchQuery[];
}

export interface BreakdownAttempt {
    original_question: string;
    rationale: string;
    new_nodes: BreakdownNode[];
    was_successful: boolean;
}

// Add children to ProcessingNode interface
export interface ProcessingNode {
    id: string;
    question: string;
    rationale: string;
    node_type: 'gather' | 'calculate';
    state: NodeState;
    display_order: number;
    is_expanded: boolean;
    depends_on_ids: string[];
    children?: ProcessingNode[];  // Added for tree structure

    // For GATHER nodes
    gathering_method?: 'web_search' | 'ask_user';
    search_queries?: SearchQuery[];
    search_results?: SearchResultWithURL[];
    estimate?: Estimate;
    user_input?: string;

    // For CALCULATE nodes
    calculation_code?: string;
    calculation_explanation?: string;
    input_node_ids?: string[];
    calculation_result?: string;

    // Final value
    value?: string;
    value_source?: 'search' | 'estimate' | 'calculation' | 'user';

    // Breakdown tracking
    breakdown_attempt?: BreakdownAttempt;
}