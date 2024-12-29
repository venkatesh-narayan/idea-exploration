import { ProcessingGraph } from '../types/graphs';

interface ProcessGoalResponse {
    key_info_graph: ProcessingGraph;
    exploration_graph: ProcessingGraph;
}

interface UserInputResponse {
    key_info_graph: ProcessingGraph;
    exploration_graph: ProcessingGraph;
}

class IdeaApi {
    private baseUrl: string;

    constructor(baseUrl: string = '') {
        this.baseUrl = baseUrl;
    }

    private async handleResponse<T>(response: Response): Promise<T> {
        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.message || 'An error occurred');
        }
        return response.json();
    }

    async processGoal(goal: string, context: string): Promise<ProcessGoalResponse> {
        const response = await fetch(`${this.baseUrl}/api/process-goal`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ goal, context }),
        });

        return this.handleResponse<ProcessGoalResponse>(response);
    }

    async submitUserInput(nodeId: string, input: string): Promise<UserInputResponse> {
        const response = await fetch(`${this.baseUrl}/api/user-input`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ nodeId, input }),
        });

        return this.handleResponse<UserInputResponse>(response);
    }

    async pollProcessingStatus(jobId: string): Promise<ProcessingGraph> {
        const response = await fetch(`${this.baseUrl}/api/status/${jobId}`, {
            method: 'GET',
        });

        return this.handleResponse<ProcessingGraph>(response);
    }
}

// Create a singleton instance
export const ideaApi = new IdeaApi(process.env.REACT_APP_API_BASE_URL);