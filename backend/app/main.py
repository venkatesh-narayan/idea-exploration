import asyncio
import logging
from typing import Dict

from app.agents.idea_agent import WebSocketIdeaAgent
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Idea Explorer API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure models
REASONING_MODEL_DICT = {
    "OPENAI": ["o1-preview"],
}

NORMAL_MODEL_DICT = {"OPENAI": ["gpt-4o"]}

# Store active agents
active_agents: Dict[str, WebSocketIdeaAgent] = {}


@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    try:
        # Create new agent for this session
        agent = WebSocketIdeaAgent(
            session_id=session_id,
            reasoning_model_dict=REASONING_MODEL_DICT,
            normal_model_dict=NORMAL_MODEL_DICT,
        )
        active_agents[session_id] = agent

        # Connect websocket
        await agent.manager.connect(websocket, session_id)

        try:
            while True:
                data = await websocket.receive_json()
                logger.info(f"Received message: {data}")

                if data["type"] == "process_goal":
                    asyncio.create_task(
                        agent.process_goal(data["goal"], data.get("context", ""))
                    )

                elif data["type"] == "user_input":
                    await agent.set_user_input(data["node_id"], data["input"])

        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for session {session_id}")
        finally:
            agent.manager.disconnect(session_id)
            active_agents.pop(session_id, None)

    except Exception as e:
        logger.error(f"Error in websocket endpoint: {str(e)}", exc_info=True)
        raise
    finally:
        # Cleanup
        if session_id in active_agents:
            del active_agents[session_id]
        logger.info(f"WebSocket connection closed: {session_id}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
