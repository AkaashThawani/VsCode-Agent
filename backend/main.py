from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

from agent import run_agent

app = FastAPI(
    title="AgentDev Backend",
    description="The server-side component for the Autonomous AI Developer Agent.",
    version="0.1.0",
)

# This ensures that requests have the required data and are validated.
class AgentTask(BaseModel):
    goal: str
    project_path: str

@app.get("/", tags=["General"])
def read_root():
    """A simple endpoint to check if the server is running."""
    return {"message": "Welcome to the AgentDev Backend Server!"}

@app.post("/execute-task", tags=["Agent"])
def execute_task(task: AgentTask):
    """
    The main endpoint to receive a task and run the AI agent.
    """
    # For now, we'll run the agent synchronously.
    # In a production system, you would run this as a background task.
    run_agent(goal=task.goal, project_path=task.project_path)
    
    # We can make the response more detailed later
    return {"status": "Agent finished task.", "goal": task.goal}



if __name__ == "__main__":
    # This allows you to run the server directly from the command line
    # for local development and testing.
    uvicorn.run(app, host="127.0.0.1", port=8000)