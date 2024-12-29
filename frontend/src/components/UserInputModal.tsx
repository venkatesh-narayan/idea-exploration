import React, { useState } from 'react';
import { ProcessingNode } from '../types/nodes';
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
    DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';

interface UserInputModalProps {
    node: ProcessingNode;
    onSubmit: (input: string) => void;
    onClose: () => void;
}

export const UserInputModal: React.FC<UserInputModalProps> = ({
    node,
    onSubmit,
    onClose,
}) => {
    const [input, setInput] = useState('');

    const handleSubmit = () => {
        if (input.trim()) {
            onSubmit(input.trim());
        }
    };

    return (
        <Dialog open onOpenChange={() => onClose()}>
            <DialogContent className="sm:max-w-[500px]">
                <DialogHeader>
                    <DialogTitle>Input Needed</DialogTitle>
                    <DialogDescription>
                        {node.question}
                    </DialogDescription>
                    {node.rationale && (
                        <p className="text-sm text-gray-600 mt-2">{node.rationale}</p>
                    )}
                </DialogHeader>

                <div className="my-4">
                    <Textarea
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder="Enter your response..."
                        className="min-h-[100px]"
                    />
                </div>

                <DialogFooter>
                    <Button variant="outline" onClick={onClose}>
                        Cancel
                    </Button>
                    <Button onClick={handleSubmit} disabled={!input.trim()}>
                        Submit
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
};