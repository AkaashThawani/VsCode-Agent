
from fastapi import FastAPI
from pydantic import BaseModel
from starlette.responses import StreamingResponse
import json
import queue
import threading
from agent_factory import create_agent_executor
from streaming_callbacks import StreamingCallbackHandler

app = FastAPI()
agent_executor = None

class AgentConfig(BaseModel):
    project_path: str
    model: str

class Task(BaseModel):
    goal: str

@app.post("/create-agent")
def create_agent(config: AgentConfig):
    """Creates the agent executor but does NOT pass callbacks yet."""
    global agent_executor
    try:
        # We can't create the full executor here because the callbacks
        # need to be new for each request. We just store the config.
        agent_executor = (config.project_path, config.model)
        return {"message": "LangChain agent config stored successfully."}
    except Exception as e:
        return {"error": f"Failed to store agent config: {e}"}

@app.post("/execute-turn")
def execute_turn(task: Task):
    if not agent_executor:
        return {"error": "Agent not configured. Please call /create-agent first."}

    # Create a queue for this specific request. This is how we will get
    # messages back from the agent's thread.
    message_queue = queue.Queue()

    # The event_stream generator is what FastAPI will send to the frontend
    def event_stream():
        # Start the agent in a separate thread.
        # This is critical to prevent the server from blocking.
        agent_thread = threading.Thread(
            target=run_agent_in_thread,
            args=(task.goal, message_queue)
        )
        agent_thread.start()

        # Now, we listen to the queue for messages from the agent's thread
        while True:
            # Get a message from the queue. This will block until a message is available.
            message = message_queue.get()
            
            # If the agent sends a "None" message, it means it's finished.
            if message is None:
                break
            
            # Yield the message to the frontend
            yield f"data: {message}\n\n"
        
        agent_thread.join() # Clean up the thread

    # This function is what will run in the background thread
    def run_agent_in_thread(goal, queue):
        try:
            # Create a new callback handler for this thread
            callback_handler = StreamingCallbackHandler(queue)
            
            # Get the stored config
            project_path, model_name = agent_executor # type: ignore
            
            # Create the actual agent executor, now WITH the callback handler
            executor = create_agent_executor(
                project_path=project_path,
                model_name=model_name,
                callbacks=[callback_handler]
            )

            # This is the blocking call that runs the agent.
            # As the agent runs, the callback handler will put messages into the queue.
            response = executor.invoke({"input": goal})
            
            # Send the final response to the queue
            queue.put(json.dumps({'type': 'status', 'content': f'Agent finished: {response["output"]}'}))

        except Exception as e:
            # If there's an error, send it to the queue
            error_message = f"An error occurred: {e}"
            queue.put(json.dumps({'type': 'error', 'content': error_message}))
        finally:
            # When the agent is done, put "None" in the queue to signal the end
            queue.put(None)

    return StreamingResponse(event_stream(), media_type="text/event-stream")