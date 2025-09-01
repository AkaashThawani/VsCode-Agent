from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import json
from fastapi.responses import StreamingResponse
from agent import run_agent

app = FastAPI(title="AgentDev Backend", version="0.1.0")

class AgentTask(BaseModel):
    goal: str
    project_path: str

async def event_stream(task: AgentTask):
    # Use a generator that yields Server-Sent Events (SSE)
    for chunk in run_agent(goal=task.goal, project_path=task.project_path):
        # Format as SSE: "data: {json_string}\n\n"
        yield f"data: {json.dumps(chunk)}\n\n"

@app.post("/execute-task", tags=["Agent"])
def execute_task(task: AgentTask):
    return StreamingResponse(event_stream(task), media_type="text/event-stream")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)