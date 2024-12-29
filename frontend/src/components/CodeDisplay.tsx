import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { ChevronDown, ChevronRight, Copy, Check } from 'lucide-react';

interface CodeDisplayProps {
    code: string;
    language: string;
    explanation?: string;
}

export const CodeDisplay: React.FC<CodeDisplayProps> = ({
    code,
    language,
    explanation,
}) => {
    const [isExpanded, setIsExpanded] = useState(false);
    const [copied, setCopied] = useState(false);

    const handleCopy = async () => {
        await navigator.clipboard.writeText(code);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    return (
        <Card className="overflow-hidden">
            <div className="flex items-center justify-between p-2 bg-gray-50 border-b">
                <Button
                    variant="ghost"
                    size="sm"
                    className="flex items-center gap-2"
                    onClick={() => setIsExpanded(!isExpanded)}
                >
                    {isExpanded ? (
                        <ChevronDown className="h-4 w-4" />
                    ) : (
                        <ChevronRight className="h-4 w-4" />
                    )}
                    <span className="text-sm font-medium">
                        {language.charAt(0).toUpperCase() + language.slice(1)} Code
                    </span>
                </Button>
                <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleCopy}
                    className="flex items-center gap-2"
                >
                    {copied ? (
                        <Check className="h-4 w-4 text-green-600" />
                    ) : (
                        <Copy className="h-4 w-4" />
                    )}
                </Button>
            </div>

            {isExpanded && (
                <>
                    {explanation && (
                        <div className="p-3 bg-gray-50 border-b text-sm text-gray-700">
                            {explanation}
                        </div>
                    )}
                    <pre className="p-4 text-sm overflow-x-auto bg-gray-900 text-gray-100">
                        <code>{code}</code>
                    </pre>
                </>
            )}
        </Card>
    );
};