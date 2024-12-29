import React from 'react';
import { ProcessingNode } from '../types/nodes';
import { NodeStatusBadge } from './NodeStatusBadge';
import { Card, CardContent } from '@/components/ui/card';

interface TreeNodeProps {
    node: ProcessingNode & { children?: ProcessingNode[] };
    onNodeClick: (node: ProcessingNode) => void;
    level?: number;
}

export const TreeNode: React.FC<TreeNodeProps> = ({
    node,
    onNodeClick,
    level = 0,
}) => {
    const hasChildren = node.children && node.children.length > 0;
    const indentClass = `ml-${Math.min(level * 8, 32)}`;

    return (
        <div className={`${indentClass} mb-4`}>
            <Card
                className={`
          transition-all duration-200 ease-in-out
          hover:shadow-md cursor-pointer
          ${level === 0 ? 'border-l-4 border-blue-500' : ''}
        `}
                onClick={() => onNodeClick(node)}
            >
                <CardContent className="p-4">
                    <div className="flex items-start justify-between gap-4">
                        <div className="flex-1">
                            <h3 className="font-medium text-gray-800 mb-1">{node.question}</h3>
                            {node.rationale && (
                                <p className="text-sm text-gray-600 mb-2">{node.rationale}</p>
                            )}
                            {node.value && (
                                <div className="mt-2 p-2 bg-gray-50 rounded-md">
                                    <p className="text-sm font-medium text-gray-700">
                                        Result: {node.value}
                                    </p>
                                </div>
                            )}
                        </div>
                        <NodeStatusBadge state={node.state} nodeType={node.node_type} />
                    </div>
                </CardContent>
            </Card>

            {hasChildren && (
                <div className="mt-2 pl-4 border-l-2 border-gray-200">
                    {node.children.map((child) => (
                        <TreeNode
                            key={child.id}
                            node={child}
                            onNodeClick={onNodeClick}
                            level={level + 1}
                        />
                    ))}
                </div>
            )}
        </div>
    );
};