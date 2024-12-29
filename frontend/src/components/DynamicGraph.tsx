import React, { useEffect } from 'react';
import ReactFlow, {
    Node,
    Edge,
    useNodesState,
    useEdgesState,
    MarkerType,
    Handle,
    Position,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { ProcessingNode } from '../types/nodes';

interface DynamicGraphProps {
    rootGoal: string;
    keyInfoNodes: ProcessingNode[];
    explorationNodes: ProcessingNode[];
    onNodeClick: (node: ProcessingNode) => void;
    isProcessing: boolean;
}

const NODE_WIDTH = 200;
const LEVEL_VERTICAL_SPACING = 160;  // Increased vertical gap
const HORIZONTAL_SPACING = 250;      // Increased horizontal gap
const BRANCH_HORIZONTAL_OFFSET = 600; // Distance between the two main branches

const CustomNode = ({ data }: { data: any }) => {
    return (
        <div className="relative">
            <Handle type="target" position={Position.Top} />
            <Handle type="source" position={Position.Bottom} />
            <div style={{ width: `${NODE_WIDTH}px` }} className={`
                rounded-lg shadow-sm border
                ${data.state === 'needs_breakdown' ? 'border-2 border-yellow-400' :
                    data.state === 'complete' ? 'border-2 border-green-400' :
                        data.state === 'blocked' ? 'border-2 border-red-400' :
                            'border-gray-200'} 
                bg-white overflow-hidden
            `}>
                <div className="p-2">
                    <div className="flex justify-between items-start gap-1">
                        <span className="text-xs font-medium text-gray-900 line-clamp-3 flex-1">
                            {data.label}
                        </span>
                        {data.state && (
                            <span className={`
                                text-xs px-1 py-0.5 rounded-full whitespace-nowrap shrink-0
                                ${data.state === 'complete' ? 'bg-green-100 text-green-800' :
                                    data.state === 'needs_breakdown' ? 'bg-yellow-100 text-yellow-800' :
                                        'bg-gray-100 text-gray-800'}
                            `}>
                                {data.state}
                            </span>
                        )}
                    </div>
                    {data.rationale && (
                        <p className="text-xs text-gray-500 mt-1 line-clamp-2">
                            {data.rationale}
                        </p>
                    )}
                </div>
            </div>
        </div>
    );
};

const nodeTypes = { custom: CustomNode };

// Find the level of each node (distance from root)
function getNodeLevels(nodes: ProcessingNode[]): Map<string, number> {
    const levels = new Map<string, number>();

    function findLevel(nodeId: string, visited = new Set<string>()): number {
        if (visited.has(nodeId)) return 0;
        if (levels.has(nodeId)) return levels.get(nodeId)!;

        visited.add(nodeId);
        const node = nodes.find(n => n.id === nodeId)!;

        if (node.depends_on_ids.length === 0) {
            levels.set(nodeId, 0);
            return 0;
        }

        const parentLevels = node.depends_on_ids.map(pid => findLevel(pid, visited));
        const level = Math.max(...parentLevels) + 1;
        levels.set(nodeId, level);
        return level;
    }

    nodes.forEach(node => findLevel(node.id));
    return levels;
}

// Layout a single subgraph
function layoutSubgraph(nodes: ProcessingNode[], baseX: number = 0): { nodes: Node[], edges: Edge[] } {
    const layoutNodes: Node[] = [];
    const edges: Edge[] = [];
    const levels = getNodeLevels(nodes);

    // Group nodes by level
    const nodesByLevel = new Map<number, ProcessingNode[]>();
    nodes.forEach(node => {
        const level = levels.get(node.id)!;
        if (!nodesByLevel.has(level)) {
            nodesByLevel.set(level, []);
        }
        nodesByLevel.get(level)!.push(node);
    });

    // Layout each level
    const maxLevel = Math.max(...nodesByLevel.keys());

    nodesByLevel.forEach((levelNodes, level) => {
        // Center nodes at this level
        const totalWidth = (levelNodes.length - 1) * HORIZONTAL_SPACING;
        const startX = baseX - totalWidth / 2;

        levelNodes.forEach((node, index) => {
            const x = startX + index * HORIZONTAL_SPACING;
            const y = level * LEVEL_VERTICAL_SPACING;

            layoutNodes.push({
                id: node.id,
                type: 'custom',
                position: { x, y },
                data: {
                    label: node.question,
                    rationale: node.rationale,
                    state: node.state
                }
            });

            // Add edges to parents
            node.depends_on_ids.forEach(parentId => {
                edges.push({
                    id: `${parentId}-to-${node.id}`,
                    source: parentId,
                    target: node.id,
                    type: 'smoothstep',
                    style: { stroke: '#94a3b8', strokeWidth: 1 },
                    markerEnd: { type: MarkerType.ArrowClosed }
                });
            });
        });
    });

    return { nodes: layoutNodes, edges };
}

function generateLayout(
    rootGoal: string,
    keyInfoNodes: ProcessingNode[],
    explorationNodes: ProcessingNode[]
): { nodes: Node[], edges: Edge[] } {
    // Layout both subgraphs
    const leftOffset = -BRANCH_HORIZONTAL_OFFSET;
    const rightOffset = BRANCH_HORIZONTAL_OFFSET;

    const keyInfoLayout = layoutSubgraph(keyInfoNodes, leftOffset);
    const explorationLayout = layoutSubgraph(explorationNodes, rightOffset);

    // Calculate positions for branch nodes and root
    const keyInfoCenter = keyInfoLayout.nodes.length > 0
        ? keyInfoLayout.nodes.reduce((sum, n) => sum + n.position.x, 0) / keyInfoLayout.nodes.length
        : leftOffset;

    const explorationCenter = explorationLayout.nodes.length > 0
        ? explorationLayout.nodes.reduce((sum, n) => sum + n.position.x, 0) / explorationLayout.nodes.length
        : rightOffset;

    const branchY = Math.min(
        ...keyInfoLayout.nodes.map(n => n.position.y),
        ...explorationLayout.nodes.map(n => n.position.y)
    ) - LEVEL_VERTICAL_SPACING;

    // Create branch nodes
    const keyInfoBranch: Node = {
        id: 'key-info',
        type: 'custom',
        position: { x: keyInfoCenter - NODE_WIDTH / 2, y: branchY },
        data: { label: 'Key Information Analysis', state: 'complete' }
    };

    const explorationBranch: Node = {
        id: 'solution-exploration',
        type: 'custom',
        position: { x: explorationCenter - NODE_WIDTH / 2, y: branchY },
        data: { label: 'Solution Exploration', state: 'complete' }
    };

    // Create root node
    const rootNode: Node = {
        id: 'root',
        type: 'custom',
        position: {
            x: (keyInfoCenter + explorationCenter) / 2 - NODE_WIDTH / 2,
            y: branchY - LEVEL_VERTICAL_SPACING
        },
        data: { label: rootGoal, state: 'complete' }
    };

    // Create top-level edges
    const topEdges: Edge[] = [
        {
            id: 'root-to-key-info',
            source: 'root',
            target: 'key-info',
            type: 'smoothstep',
            style: { stroke: '#94a3b8', strokeWidth: 1 },
            markerEnd: { type: MarkerType.ArrowClosed }
        },
        {
            id: 'root-to-exploration',
            source: 'root',
            target: 'solution-exploration',
            type: 'smoothstep',
            style: { stroke: '#94a3b8', strokeWidth: 1 },
            markerEnd: { type: MarkerType.ArrowClosed }
        }
    ];

    // Add edges from branch nodes to their direct children
    keyInfoNodes.filter(n => n.depends_on_ids.length === 0).forEach(node => {
        topEdges.push({
            id: `key-info-to-${node.id}`,
            source: 'key-info',
            target: node.id,
            type: 'smoothstep',
            style: { stroke: '#94a3b8', strokeWidth: 1 },
            markerEnd: { type: MarkerType.ArrowClosed }
        });
    });

    explorationNodes.filter(n => n.depends_on_ids.length === 0).forEach(node => {
        topEdges.push({
            id: `solution-exploration-to-${node.id}`,
            source: 'solution-exploration',
            target: node.id,
            type: 'smoothstep',
            style: { stroke: '#94a3b8', strokeWidth: 1 },
            markerEnd: { type: MarkerType.ArrowClosed }
        });
    });

    return {
        nodes: [
            ...keyInfoLayout.nodes,
            ...explorationLayout.nodes,
            keyInfoBranch,
            explorationBranch,
            rootNode
        ],
        edges: [
            ...keyInfoLayout.edges,
            ...explorationLayout.edges,
            ...topEdges
        ]
    };
}

const RecenterButton = ({ fitView }: { fitView: () => void }) => {
    return (
        <button
            onClick={fitView}
            className="fixed bottom-4 right-4 bg-white p-2 rounded-lg shadow-lg border border-gray-200 hover:bg-gray-50 transition-colors"
            title="Recenter View"
        >
            <svg
                xmlns="http://www.w3.org/2000/svg"
                width="24"
                height="24"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
            >
                <path d="M4 4h16v16H4z" />
                <path d="M9 9h6v6H9z" />
            </svg>
        </button>
    );
};

export const DynamicGraph: React.FC<DynamicGraphProps> = ({
    rootGoal,
    keyInfoNodes,
    explorationNodes,
    onNodeClick,
    isProcessing
}) => {
    const [nodes, setNodes, onNodesChange] = useNodesState([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState([]);

    useEffect(() => {
        const { nodes: layoutNodes, edges: layoutEdges } = generateLayout(
            rootGoal,
            keyInfoNodes,
            explorationNodes
        );
        setNodes(layoutNodes);
        setEdges(layoutEdges);
    }, [rootGoal, keyInfoNodes, explorationNodes]);

    return (
        <div style={{ width: '100%', height: '800px' }} className="bg-gray-50 rounded-lg relative">
            <ReactFlow
                nodes={nodes}
                edges={edges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                onNodeClick={(_, node) => {
                    const processNode = [...keyInfoNodes, ...explorationNodes].find(
                        n => n.id === node.id
                    );
                    if (processNode) onNodeClick(processNode);
                }}
                nodeTypes={nodeTypes}
                fitView
                fitViewOptions={{
                    padding: 0.2,
                    includeHiddenNodes: true,
                    maxZoom: 1.5
                }}
                nodesDraggable={false}
                zoomOnScroll={false}
                panOnScroll={true}
                preventScrolling={false}
                minZoom={0.5}
                maxZoom={1.5}
            />
            <RecenterButton fitView={() => {
                setTimeout(() => {
                    const fitViewOptions = {
                        padding: 0.2,
                        includeHiddenNodes: true,
                        maxZoom: 1.5
                    };
                    document.querySelector('.react-flow__renderer')
                        ?.dispatchEvent(new Event('fitview', { bubbles: true }));
                }, 0);
            }} />
        </div>
    );
};