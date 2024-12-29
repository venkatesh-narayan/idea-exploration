import React, { useState } from 'react';
import { ProcessingNode, SearchResultWithURL } from '../types/nodes';
import { Card, CardHeader, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { X } from 'lucide-react';
import { CodeDisplay } from './CodeDisplay';

interface ProcessingStatusProps {
    node: ProcessingNode;
    onClose: () => void;
}

export const ProcessingStatus: React.FC<ProcessingStatusProps> = ({
    node,
    onClose,
}) => {
    const [selectedResult, setSelectedResult] = useState<SearchResultWithURL | null>(
        null
    );

    return (
        <Card className="fixed bottom-0 right-0 w-1/3 max-h-[60vh] overflow-y-auto m-4 shadow-xl">
            <CardHeader className="flex flex-row items-center justify-between p-4 bg-gray-50">
                <h3 className="font-semibold text-lg">{node.question}</h3>
                <Button variant="ghost" size="icon" onClick={onClose}>
                    <X className="h-4 w-4" />
                </Button>
            </CardHeader>

            <CardContent className="p-4">
                {/* Search Queries */}
                {node.search_queries && node.search_queries.length > 0 && (
                    <div className="mb-4">
                        <h4 className="font-medium mb-2">Search Queries</h4>
                        <ul className="space-y-2">
                            {node.search_queries.map((query, idx) => (
                                <li
                                    key={idx}
                                    className="p-2 bg-blue-50 rounded-md text-sm text-blue-800"
                                >
                                    {query.query}
                                </li>
                            ))}
                        </ul>
                    </div>
                )}

                {/* Search Results */}
                {node.search_results && node.search_results.length > 0 && (
                    <div className="mb-4">
                        <h4 className="font-medium mb-2">Search Results</h4>
                        <div className="space-y-2">
                            {node.search_results.map((result, idx) => (
                                <div
                                    key={idx}
                                    className="p-3 border rounded-md hover:bg-gray-50 cursor-pointer"
                                    onClick={() => setSelectedResult(result)}
                                >
                                    <p className="text-sm">{result.search_result.fact}</p>
                                    <a
                                        href={result.source_url}
                                        className="text-xs text-blue-600 hover:underline mt-1 block"
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        onClick={(e) => e.stopPropagation()}
                                    >
                                        Source
                                    </a>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Calculation Code */}
                {node.calculation_code && (
                    <div className="mb-4">
                        <h4 className="font-medium mb-2">Calculation</h4>
                        <CodeDisplay
                            code={node.calculation_code}
                            language="python"
                            explanation={node.calculation_explanation}
                        />
                        {node.calculation_result && (
                            <div className="mt-2 p-2 bg-green-50 rounded-md">
                                <p className="text-sm font-medium text-green-800">
                                    Result: {node.calculation_result}
                                </p>
                            </div>
                        )}
                    </div>
                )}

                {/* Estimate Details */}
                {node.estimate && (
                    <div className="mb-4">
                        <h4 className="font-medium mb-2">Estimate</h4>
                        <div className="p-3 bg-orange-50 rounded-md">
                            <p className="text-sm mb-2">{node.estimate.reasoning}</p>
                            <div className="text-sm">
                                <strong>Assumptions:</strong>
                                <ul className="list-disc list-inside mt-1">
                                    {node.estimate.assumptions.map((assumption, idx) => (
                                        <li key={idx} className="text-sm text-gray-700">{assumption}</li>
                                    ))}
                                </ul>
                            </div>
                        </div>
                    </div>
                )}

                {/* Breakdown Attempt */}
                {node.breakdown_attempt && (
                    <div className="mb-4">
                        <h4 className="font-medium mb-2">Search Breakdown</h4>
                        <div className="p-3 bg-yellow-50 rounded-md">
                            <p className="text-sm mb-2">{node.breakdown_attempt.rationale}</p>
                            <div className="mt-2">
                                <strong className="text-sm">New Approaches:</strong>
                                <ul className="list-disc list-inside mt-1">
                                    {node.breakdown_attempt.new_nodes.map((n, idx) => (
                                        <li key={idx} className="text-sm text-gray-700">{n.question}</li>
                                    ))}
                                </ul>
                            </div>
                        </div>
                    </div>
                )}
            </CardContent>
        </Card>
    );
};