import functools
from pathlib import Path
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.tools import Tool
import os

# Import the raw tool functions from our toolkit
from toolkit import (
    get_project_summary,
    read_file,
    write_file,
    search_and_replace,
    talk_to_user
)
# We also need the helper function to be available here for configuration
from toolkit import _get_safe_path

# The prompt from the last step is still the best one, as it teaches the agent
# the correct JSON format for multi-argument tools.
# ### START of DEFINITIVE PROMPT ###
AGENT_PROMPT_TEMPLATE = """
You are AgentDev, an expert AI engineer. Your only job is to achieve the user's goal.

You have access to these tools:
{tools}

Use this format:

Thought: The user's goal is X. I need to use a tool to achieve it.
Action: the name of the tool to use, from [{tool_names}]
Action Input: the input to the tool.

(the Thought/Action/Action Input/Observation loop can repeat)

Thought: I have successfully achieved the user's goal.
Final Answer: A summary of what I did.

**### VERY IMPORTANT RULES ###**

1.  **IF THE USER SAYS "hi" or "hello":** You MUST use the `talk_to_user` tool once, and then you MUST immediately use `Final Answer:`.

2.  **FOR ALL OTHER GOALS:** You MUST use `get_project_summary` first.

Begin!

User Goal: {input}
Thought:
{agent_scratchpad}
"""



def create_agent_executor(project_path: str, model_name: str, callbacks: list):
    """
    Factory function to create and configure the LangChain agent and its executor.
    """
    print(f"Creating LangChain agent with callbacks and model: {model_name}")

    llm = ChatOllama(model=model_name, temperature=0)

    # --- Tool Configuration ---
    # Here, we create the actual, runnable versions of our tools by "injecting"
    # the sandbox_path dependency into the raw functions from toolkit.py.

    def configured_get_project_summary(tool_input: any = None) -> str: # type: ignore
        # The logic inside the function remains the same.
        safe_path = _get_safe_path(project_path, '.')
        paths = sorted(Path(safe_path).rglob('*'))
        file_list = "\n".join([str(p.relative_to(project_path)).replace('\\', '/') for p in paths])
        return f"Project File Structure:\n```\n{file_list}\n```"

    def configured_read_file(file_path: str) -> str:
        safe_path = _get_safe_path(project_path, file_path)
        with open(safe_path, 'r', encoding='utf-8') as f:
            return f.read()

    def configured_write_file(file_path: str, content: str) -> str:
        safe_path = _get_safe_path(project_path, file_path)
        os.makedirs(os.path.dirname(safe_path), exist_ok=True)
        with open(safe_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully wrote to {file_path}."

    def configured_search_and_replace(file_path: str, search_string: str, replace_string: str) -> str:
        safe_path = _get_safe_path(project_path, file_path)
        with open(safe_path, 'r', encoding='utf-8') as f:
            content = f.read()
        if search_string not in content:
            return f"Error: The search string was not found in {file_path}."
        new_content = content.replace(search_string, replace_string)
        with open(safe_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return f"Successfully performed search and replace in {file_path}."

    # Now, we wrap our configured functions in the original Tool objects
    # so LangChain can use them.
    tools = [
        Tool(
            name="get_project_summary",
            func=configured_get_project_summary,
            description=get_project_summary.description
        ),
        Tool(
            name="read_file",
            func=configured_read_file,
            description=read_file.description,
            args_schema=read_file.args_schema
        ),
        Tool(
            name="write_file",
            func=configured_write_file,
            description=write_file.description,
            args_schema=write_file.args_schema
        ),
        Tool(
            name="search_and_replace",
            func=configured_search_and_replace,
            description=search_and_replace.description,
            args_schema=search_and_replace.args_schema
        ),
        talk_to_user,
    ]

    prompt = PromptTemplate.from_template(AGENT_PROMPT_TEMPLATE)
    agent = create_react_agent(llm=llm, tools=tools, prompt=prompt)

    executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
        callbacks=callbacks
    )

    return executor