import json
from langchain_core.callbacks.base import BaseCallbackHandler
from typing import Any, Dict, List

# A callback handler is a class that can listen to events from LangChain.
# We are creating one that is specifically designed to stream JSON responses.
class StreamingCallbackHandler(BaseCallbackHandler):
    def __init__(self, queue):
        self.queue = queue

    # This method is called whenever the LLM starts thinking
    def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any) -> None:
        # We put a "thinking" message into the queue to send to the frontend
        self.queue.put(json.dumps({'type': 'thought', 'content': '🧠 Thinking...'}))

    # This method is called whenever a tool starts running
    def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs: Any) -> None:
        tool_name = serialized.get("name", "Unknown Tool")
        # We put an "action" message into the queue
        self.queue.put(json.dumps({'type': 'action', 'content': f'Running tool: {tool_name}'}))

    # This method is called whenever a tool ends
    def on_tool_end(self, output: str, **kwargs: Any) -> None:
        # We put the result of the tool into the queue
        self.queue.put(json.dumps({'type': 'result', 'content': output}))