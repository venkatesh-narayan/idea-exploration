import React, { useState, useEffect, useRef } from 'react';
import { IdeaMap } from '../components/IdeaMap';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { ProcessingGraph } from '../types/graphs';
import { ProcessingNode, NodeState } from '../types/nodes';
import { AlertCircle } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { UserInputModal } from '../components/UserInputModal';

export const IdeaPage: React.FC = () => {
    const [goal, setGoal] = useState('');
    const [context, setContext] = useState('');
    const [isProcessing, setIsProcessing] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [keyInfoGraph, setKeyInfoGraph] = useState<ProcessingGraph | null>(null);
    const [explorationGraph, setExplorationGraph] = useState<ProcessingGraph | null>(null);
    const [userInputNode, setUserInputNode] = useState<ProcessingNode | null>(null);
    const wsRef = useRef<WebSocket | null>(null);
    const sessionIdRef = useRef<string | null>(null);

    const handleWebSocketMessage = (data: any) => {
        console.log('WebSocket message received:', data); // Debug log

        switch (data.type) {
            case 'initial_key_info_graph':
                console.log('Setting initial key info graph:', data.graph);
                setKeyInfoGraph(data.graph);
                break;

            case 'initial_exploration_graph':
                console.log('Setting initial exploration graph:', data.graph);
                setExplorationGraph(data.graph);
                break;

            case 'node_state_update':
                console.log('Node state update:', data);
                updateNodeState(data.node_id, data.state);
                if (data.state === NodeState.BLOCKED) {
                    checkForUserInputNode(data.node_id);
                }
                break;

            case 'node_value_update':
                console.log('Node value update:', data);
                updateNodeValue(data.node_id, data);
                break;

            case 'breakdown_nodes':
                console.log('Adding breakdown nodes:', data);
                addBreakdownNodes(data.parent_id, data.nodes);
                break;

            case 'estimate_node':
                console.log('Adding estimate node:', data);
                addEstimateNode(data.parent_id, data.estimate);
                break;

            default:
                console.log('Unknown message type:', data.type);
        }
    };

    const updateNodeState = (nodeId: string, state: NodeState) => {
        console.log(`Updating node ${nodeId} state to ${state}`);

        setKeyInfoGraph(prev => {
            if (!prev || !prev.nodes) {
                console.log('No previous key info graph or nodes');
                return prev;
            }
            const updated = {
                ...prev,
                nodes: prev.nodes.map(node => {
                    if (node.id === nodeId) {
                        console.log(`Updating key info node ${nodeId} from state ${node.state} to ${state}`);
                        return { ...node, state };
                    }
                    return node;
                })
            };
            console.log('Updated key info graph:', updated);
            return updated;
        });

        setExplorationGraph(prev => {
            if (!prev || !prev.nodes) {
                console.log('No previous exploration graph or nodes');
                return prev;
            }
            const updated = {
                ...prev,
                nodes: prev.nodes.map(node => {
                    if (node.id === nodeId) {
                        console.log(`Updating exploration node ${nodeId} from state ${node.state} to ${state}`);
                        return { ...node, state };
                    }
                    return node;
                })
            };
            console.log('Updated exploration graph:', updated);
            return updated;
        });
    };

    const updateNodeValue = (nodeId: string, update: any) => {
        console.log(`Updating node ${nodeId} value:`, update);

        const updateNode = (node: ProcessingNode) => {
            console.log(`Updating node ${node.id} with values:`, update);
            return {
                ...node,
                value: update.value,
                value_source: update.value_source,
                search_results: update.search_results,
                calculation_result: update.calculation_result
            };
        };

        setKeyInfoGraph(prev => {
            if (!prev || !prev.nodes) {
                console.log('No previous key info graph or nodes');
                return prev;
            }
            const updated = {
                ...prev,
                nodes: prev.nodes.map(node =>
                    node.id === nodeId ? updateNode(node) : node
                )
            };
            console.log('Updated key info graph:', updated);
            return updated;
        });

        setExplorationGraph(prev => {
            if (!prev || !prev.nodes) {
                console.log('No previous exploration graph or nodes');
                return prev;
            }
            const updated = {
                ...prev,
                nodes: prev.nodes.map(node =>
                    node.id === nodeId ? updateNode(node) : node
                )
            };
            console.log('Updated exploration graph:', updated);
            return updated;
        });
    };

    const addBreakdownNodes = (parentId: string, newNodes: ProcessingNode[]) => {
        console.log(`Adding breakdown nodes for parent ${parentId}:`, newNodes);

        setKeyInfoGraph(prev => {
            if (!prev) return prev;
            const updated = {
                ...prev,
                nodes: [...prev.nodes, ...newNodes]
            };
            console.log('Updated key info graph:', updated);
            return updated;
        });

        setExplorationGraph(prev => {
            if (!prev) return prev;
            const updated = {
                ...prev,
                nodes: [...prev.nodes, ...newNodes]
            };
            console.log('Updated exploration graph:', updated);
            return updated;
        });
    };

    const addEstimateNode = (parentId: string, estimate: any) => {
        console.log(`Adding estimate node for parent ${parentId}:`, estimate);

        const estimateNode: ProcessingNode = {
            id: `estimate-${parentId}`,
            question: `Estimate for ${parentId}`,
            rationale: estimate.reasoning,
            node_type: 'gather',
            state: NodeState.COMPLETE,
            depends_on_ids: [parentId],
            value: estimate.value,
            value_source: 'estimate',
            display_order: 0,
            is_expanded: true,
        };

        addBreakdownNodes(parentId, [estimateNode]);
    };

    const checkForUserInputNode = (nodeId: string) => {
        const findNode = (graph: ProcessingGraph | null) => {
            return graph?.nodes.find(node =>
                node.id === nodeId &&
                node.state === NodeState.BLOCKED &&
                node.gathering_method === 'ask_user'
            );
        };

        const node = findNode(keyInfoGraph) || findNode(explorationGraph);
        if (node) {
            setUserInputNode(node);
        }
    };

    const setupWebSocket = (sessionId: string): Promise<WebSocket> => {
        return new Promise((resolve, reject) => {
            const wsUrl = `ws://localhost:8000/ws/${sessionId}`;
            console.log('Attempting to connect to:', wsUrl);

            const ws = new WebSocket(wsUrl);
            wsRef.current = ws;
            sessionIdRef.current = sessionId;

            // Log state changes
            ws.onopen = () => {
                console.log('WebSocket connection established');
                console.log('WebSocket state:', ws.readyState);
                resolve(ws);
            };

            ws.onclose = (event) => {
                console.log('WebSocket closed:', {
                    code: event.code,
                    reason: event.reason,
                    wasClean: event.wasClean
                });
                wsRef.current = null;
            };

            ws.onmessage = (event) => {
                console.log('WebSocket message received:', event.data);
                const data = JSON.parse(event.data);
                handleWebSocketMessage(data);
            };

            ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                console.log('WebSocket state at error:', ws.readyState);
                setError('Connection error occurred. Please ensure the backend server is running.');
                setIsProcessing(false);
                reject(error);
            };

            // Log initial state
            console.log('Initial WebSocket state:', ws.readyState);

            // Set a timeout for the connection with more detailed logging
            const timeoutId = setTimeout(() => {
                if (ws.readyState !== WebSocket.OPEN) {
                    console.log('Connection timeout. Final WebSocket state:', ws.readyState);
                    reject(new Error(`WebSocket connection timeout. State: ${ws.readyState}`));
                    ws.close();
                }
            }, 5000);

            // Clear timeout if connection succeeds
            ws.onopen = () => {
                clearTimeout(timeoutId);
                console.log('WebSocket connection established');
                resolve(ws);
            };
        });
    };

    const handleSubmit = async () => {
        if (!goal.trim()) return;

        console.log('Submitting goal:', { goal, context });
        setIsProcessing(true);
        setError(null);
        setKeyInfoGraph(null);
        setExplorationGraph(null);

        const sessionId = Math.random().toString(36).substring(7);

        try {
            const ws = await setupWebSocket(sessionId);
            console.log('Sending goal to backend');
            ws.send(JSON.stringify({
                type: 'process_goal',
                goal,
                context
            }));
        } catch (err) {
            console.error('Connection error:', err);
            setError('Could not establish connection');
            setIsProcessing(false);
        }
    };

    const handleUserInput = (input: string) => {
        if (!wsRef.current || !userInputNode) {
            console.error('Cannot send user input: no websocket or node');
            return;
        }

        console.log('Sending user input:', { nodeId: userInputNode.id, input });
        wsRef.current.send(JSON.stringify({
            type: 'user_input',
            node_id: userInputNode.id,
            input
        }));

        setUserInputNode(null);
    };

    // Cleanup WebSocket on unmount
    useEffect(() => {
        return () => {
            if (wsRef.current) {
                console.log('Cleaning up WebSocket connection');
                wsRef.current.close();
            }
        };
    }, []);

    return (
        <div className="container mx-auto py-6">
            <h1 className="text-3xl font-bold mb-6 text-gray-800">Idea Explorer</h1>

            <div className="space-y-4 mb-8">
                <div>
                    <label htmlFor="goal" className="block text-sm font-medium text-gray-700 mb-1">
                        What's your goal?
                    </label>
                    <Textarea
                        id="goal"
                        value={goal}
                        onChange={(e) => setGoal(e.target.value)}
                        placeholder="Enter your goal here..."
                        className="h-24"
                    />
                </div>

                <div>
                    <label htmlFor="context" className="block text-sm font-medium text-gray-700 mb-1">
                        Additional Context (optional)
                    </label>
                    <Textarea
                        id="context"
                        value={context}
                        onChange={(e) => setContext(e.target.value)}
                        placeholder="Add any relevant context..."
                        className="h-24"
                    />
                </div>

                <Button
                    onClick={handleSubmit}
                    disabled={!goal.trim() || isProcessing}
                    className="w-full"
                >
                    {isProcessing ? 'Processing...' : 'Explore Goal'}
                </Button>
            </div>

            {error && (
                <Alert variant="destructive" className="mb-6">
                    <AlertCircle className="h-4 w-4" />
                    <AlertTitle>Error</AlertTitle>
                    <AlertDescription>{error}</AlertDescription>
                </Alert>
            )}

            {isProcessing && !keyInfoGraph && (
                <LoadingSpinner
                    message="Analyzing goal..."
                    className="my-8"
                />
            )}

            {(keyInfoGraph || explorationGraph) && (
                <IdeaMap
                    goal={goal}
                    keyInfoGraph={keyInfoGraph}
                    explorationGraph={explorationGraph}
                />
            )}

            {userInputNode && (
                <UserInputModal
                    node={userInputNode}
                    onSubmit={handleUserInput}
                    onClose={() => setUserInputNode(null)}
                />
            )}
        </div>
    );
};