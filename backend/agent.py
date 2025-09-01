# backend/agent.py

import os
import json
import inspect
import google.generativeai as genai
from dotenv import load_dotenv

# Import our new Toolkit class
from toolkit import Toolkit

# --- Configuration ---
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
MODEL = genai.GenerativeModel('gemini-1.5-pro-latest')

AGENT_PROMPT = """
You are AgentDev, an efficient and precise AI software developer.

**CORE DIRECTIVE: Follow this workflow.**
1.  **Understand:** Use `read_file` to get the context of the code you need to change.
2.  **Choose Your Tool:**
    -   For **simple, single-line** changes (like changing `speed = 8` to `speed = 4`), use the `search_and_replace` "scalpel".
    -   For **complex, multi-line** changes (like refactoring a function), use the `replace_code_block` "power tool".
3.  **Be Precise:** Your `search_string` or `original_code_block` MUST be an exact, verbatim copy from the file. This is mandatory for safety.
4.  **Verify:** After editing, use `read_file` one last time to confirm the change is correct.
5.  **Finish:** Call the `finish` tool when the task is complete.

**CRITICAL SAFETY WARNINGS:**
-   **NO LOOPS:** Once you have read a file, you have the information. Do not read it again unless you are verifying a change. Plan and execute.
-   **`write_file` IS FOR NEW FILES ONLY.** Never use it to edit an existing file.

---
**CURRENT GOAL:** {goal}
**HISTORY OF ACTIONS:**
{history}
---
Begin.
"""

def get_tool_definitions(tools: dict):
    # This function remains unchanged
    definitions = ""
    for name, func in tools.items():
        sig = inspect.signature(func)
        sig_str = f"{name}{sig}"
        definitions += f"- Function: {sig_str}\n"
        definitions += f"  - Description: {func.__doc__.strip()}\n"
    return definitions

# --- THIS FUNCTION IS NOW A GENERATOR ---


def run_agent(goal: str, project_path: str):
    toolkit = Toolkit(project_path)
    available_tools = toolkit.get_tools()
    history = []
    max_loops = 10
    loop_count = 0

    while loop_count < max_loops:
        loop_count += 1
        tool_defs = get_tool_definitions(available_tools)
        history_str = "\n".join(history)
        prompt = AGENT_PROMPT.format(
            tool_definitions=tool_defs, goal=goal, history=history_str)

        response = MODEL.generate_content(prompt)

        try:
            response_text = response.text.strip()
            json_str_match = response_text[response_text.find(
                '{'):response_text.rfind('}')+1]
            parsed_response = json.loads(json_str_match)

            thought = parsed_response.get("thought", "")
            action = parsed_response.get("action", {})
            tool_name = action.get("tool_name")
            arguments = action.get("arguments", {})

            yield {"type": "thought", "content": thought}
            history.append(f"Thought: {thought}")

            if not tool_name:
                continue

            tool_function = available_tools.get(tool_name)
            if not tool_function:
                result = f"Error: Tool '{tool_name}' not found."
            elif tool_name == "finish":
                yield {"type": "status", "content": "Agent has finished the task."}
                break
            else:
                if tool_name == "write_file":
                    action_summary = f"Writing changes to {arguments.get('file_path', 'a file')}."
                else:
                    action_summary = f"Running tool: {tool_name}"
                yield {"type": "action", "content": action_summary}

                result = tool_function(**arguments)

            yield {"type": "result", "content": result}
            history.append(f"Action: {tool_name}({arguments})")
            history.append(f"Result: {result}")

        except Exception as e:
            yield {"type": "error", "content": f"An error occurred: {e}"}
            history.append(f"Result: Error - {e}")
