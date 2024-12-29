import { ProcessingNode } from './nodes';

export interface ProcessingGraph {
    goal: string;
    nodes: ProcessingNode[];
}

export interface InitialInfoGraph {
    nodes: ProcessingNode[];
}

export interface InitialInfoGraphWithGoal {
    goal: string;
    graph: InitialInfoGraph;
}