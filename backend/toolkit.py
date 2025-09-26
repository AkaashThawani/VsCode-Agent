import os
from pathlib import Path
from langchain_core.tools import tool
from pydantic import BaseModel, Field


def _get_safe_path(sandbox_path: str, relative_path: str) -> str:
    """A helper function to ensure file paths are safe."""
    base_path = Path(sandbox_path)
    file_path = base_path.joinpath(relative_path).resolve()
    if base_path not in file_path.parents and file_path != base_path:
        raise PermissionError("Security Error: Attempted to access a file outside the sandboxed project directory.")
    return str(file_path)

# --- Input Schemas for Tools ---
# This is the professional way to define arguments for LangChain tools.
# It provides automatic validation and clear schemas for the LLM.

class ReadFileInput(BaseModel):
    file_path: str = Field(description="The relative path to the file that needs to be read.")

class WriteFileInput(BaseModel):
    file_path: str = Field(description="The relative path for the file to be written.")
    content: str = Field(description="The complete content to be written to the file.")

class SearchReplaceInput(BaseModel):
    file_path: str = Field(description="The relative path to the file that needs to be modified.")
    search_string: str = Field(description="The exact string to search for in the file.")
    replace_string: str = Field(description="The string that will replace the search_string.")

class FinishTaskInput(BaseModel):
    final_answer: str = Field(description="A summary of the work that was done to complete the user's goal.")

class TalkToUserInput(BaseModel):
    response: str = Field(description="The message to be sent directly to the user.")

# --- Standalone LangChain Tools ---

@tool
def get_project_summary() -> str:
    """
    Analyzes the project structure. This should be the VERY FIRST tool called
    for any complex user request to gain context.
    """
    # NOTE: This tool will be configured with its sandbox_path in the agent factory.
    # This is a placeholder that will be replaced by a configured function.
    return "Error: This tool was not configured correctly. The sandbox_path is missing."

@tool(args_schema=ReadFileInput)
def read_file(file_path: str) -> str:
    """Reads and returns the ENTIRE content of a single specified file."""
    # This tool will also be configured with its sandbox_path.
    return "Error: This tool was not configured correctly. The sandbox_path is missing."

@tool(args_schema=WriteFileInput)
def write_file(file_path: str, content: str) -> str:
    """Writes content to a file, completely overwriting it if it exists."""
    return "Error: This tool was not configured correctly. The sandbox_path is missing."

@tool(args_schema=SearchReplaceInput)
def search_and_replace(file_path: str, search_string: str, replace_string: str) -> str:
    """Performs a targeted search for a string in a file and replaces all occurrences."""
    return "Error: This tool was not configured correctly. The sandbox_path is missing."

@tool(args_schema=FinishTaskInput)
def finish_task(final_answer: str) -> str:
    """
    Call this function ONLY when the user's entire goal has been successfully and
    completely achieved. Use it for both coding and conversational tasks.
    """
    return f"Task finished. {final_answer}"

@tool(args_schema=TalkToUserInput)
def talk_to_user(response: str) -> str:
    """
    Use this tool to communicate directly with the user. This is for greetings,
    clarifications, or when no code changes are needed.
    """
    return f"Agent says: {response}"