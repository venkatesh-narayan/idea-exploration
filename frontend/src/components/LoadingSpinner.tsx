import React from 'react';
import { Loader2 } from 'lucide-react';

interface LoadingSpinnerProps {
    message?: string;
    className?: string;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
    message = 'Processing...',
    className = ''
}) => {
    return (
        <div className={`flex flex-col items-center justify-center space-y-2 ${className}`}>
            <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
            <p className="text-sm text-gray-600">{message}</p>
        </div>
    );
};