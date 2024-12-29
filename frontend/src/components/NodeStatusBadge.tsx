import React from 'react';
import { NodeState, NodeType } from '../types/nodes';
import { Badge } from '@/components/ui/badge';
import {
    Search,
    Calculator,
    AlertCircle,
    Clock,
    CheckCircle,
    Lock,
    HelpCircle,
    Brain
} from 'lucide-react';

interface NodeStatusBadgeProps {
    state: NodeState;
    nodeType: NodeType;
}

export const NodeStatusBadge: React.FC<NodeStatusBadgeProps> = ({
    state,
    nodeType
}) => {
    const getStatusConfig = () => {
        switch (state) {
            case NodeState.SEARCHING:
                return {
                    color: 'bg-blue-100 text-blue-800',
                    icon: <Search className="w-4 h-4" />,
                    text: 'Searching'
                };
            case NodeState.CALCULATING:
                return {
                    color: 'bg-purple-100 text-purple-800',
                    icon: <Calculator className="w-4 h-4" />,
                    text: 'Calculating'
                };
            case NodeState.NEEDS_BREAKDOWN:
                return {
                    color: 'bg-yellow-100 text-yellow-800',
                    icon: <Brain className="w-4 h-4" />,
                    text: 'Breaking Down'
                };
            case NodeState.NEEDS_ESTIMATE:
                return {
                    color: 'bg-orange-100 text-orange-800',
                    icon: <HelpCircle className="w-4 h-4" />,
                    text: 'Needs Estimate'
                };
            case NodeState.PENDING:
                return {
                    color: 'bg-gray-100 text-gray-800',
                    icon: <Clock className="w-4 h-4" />,
                    text: 'Pending'
                };
            case NodeState.COMPLETE:
                return {
                    color: 'bg-green-100 text-green-800',
                    icon: <CheckCircle className="w-4 h-4" />,
                    text: 'Complete'
                };
            case NodeState.BLOCKED:
                return {
                    color: 'bg-red-100 text-red-800',
                    icon: <Lock className="w-4 h-4" />,
                    text: 'Needs Input'
                };
            default:
                return {
                    color: 'bg-gray-100 text-gray-800',
                    icon: <AlertCircle className="w-4 h-4" />,
                    text: 'Unknown'
                };
        }
    };

    const config = getStatusConfig();

    return (
        <Badge
            variant="secondary"
            className={`flex items-center gap-1 ${config.color}`}
        >
            {config.icon}
            <span className="ml-1">{config.text}</span>
        </Badge>
    );
};