import React, { useState } from 'react';
import { ProcessingNode } from '../types/nodes';
import { ProcessingGraph } from '../types/graphs';
import { DynamicGraph } from './DynamicGraph';
import { ProcessingStatus } from './ProcessingStatus';

interface IdeaMapProps {
    goal: string;
    keyInfoGraph: ProcessingGraph | null;
    explorationGraph: ProcessingGraph | null;
    isProcessing: boolean;
}

export const IdeaMap: React.FC<IdeaMapProps> = ({
    goal,
    keyInfoGraph,
    explorationGraph,
    isProcessing
}) => {
    const [selectedNode, setSelectedNode] = useState<ProcessingNode | null>(null);

    const handleNodeClick = (node: ProcessingNode) => {
        setSelectedNode(node);
    };

    return (
        <div className="space-y-8">
            <div className="h-[800px] w-full">  {/* Fixed height container for graph */}
                <DynamicGraph
                    rootGoal={goal}
                    keyInfoNodes={keyInfoGraph?.nodes || []}
                    explorationNodes={explorationGraph?.nodes || []}
                    onNodeClick={handleNodeClick}
                    isProcessing={isProcessing}
                />
            </div>

            {selectedNode && (
                <ProcessingStatus
                    node={selectedNode}
                    onClose={() => setSelectedNode(null)}
                />
            )}
        </div>
    );
};