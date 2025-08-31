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

# --- The Master Prompt (Simplified and Stricter) ---
AGENT_PROMPT = """
You are AgentDev, an expert AI software developer. Your goal is to complete the user's request by using the tools available to you.

**CRITICAL RULES:**
1. You are operating within a sandboxed project directory.
2. **ALL file and directory paths MUST be relative to the project root.** Do NOT use absolute paths. Do NOT include the project's root folder name in the path.
   - CORRECT: `src/main.py`
   - INCORRECT: `my-project/src/main.py`
   - INCORRECT: `/abs/path/to/src/main.py`
3. When you have fully completed the goal and verified your work, you MUST call the `finish` tool.

**TOOLS:**
{tool_definitions}

**RESPONSE FORMAT:**
You must respond with a single, valid JSON object containing "thought" and "action".
Example:
{{
  "thought": "I need to read the main file.",
  "action": {{
    "tool_name": "read_file",
    "arguments": {{
      "file_path": "src/main.py"
    }}
  }}
}}

**CURRENT GOAL:**
{goal}

**HISTORY OF ACTIONS:**
{history}

Begin.
"""

def get_tool_definitions(tools: dict):
    definitions = ""
    for name, func in tools.items():
        sig = inspect.signature(func)
        sig_str = f"{name}{sig}"
        definitions += f"- Function: {sig_str}\n"
        definitions += f"  - Description: {func.__doc__.strip()}\n"
    return definitions

def run_agent(goal: str, project_path: str):
    print(f"--- AGENT STARTING ---")
    print(f"Goal: {goal}")
    
    # Initialize the new Toolkit class for this specific task
    toolkit = Toolkit(project_path)
    available_tools = toolkit.get_tools()

    history = []
    max_loops = 10
    loop_count = 0

    while loop_count < max_loops:
        loop_count += 1
        print(f"\n--- LOOP {loop_count} ---")

        tool_defs = get_tool_definitions(available_tools)
        history_str = "\n".join(history)
        prompt = AGENT_PROMPT.format(tool_definitions=tool_defs, goal=goal, history=history_str)

        print("🤔 Agent is thinking...")
        response = MODEL.generate_content(prompt)
        
        try:
            response_text = response.text.strip()
            print(f"RAW Response:\n{response_text}")
            
            json_str_match = response_text[response_text.find('{'):response_text.rfind('}')+1]
            parsed_response = json.loads(json_str_match)
            
            thought = parsed_response.get("thought", "")
            action = parsed_response.get("action", {})
            tool_name = action.get("tool_name")
            arguments = action.get("arguments", {})

            print(f"💡 Thought: {thought}")
            history.append(f"Thought: {thought}")

            if not tool_name:
                print("ERROR: No tool name found.")
                history.append("Result: Error - No tool name found.")
                continue

            print(f"🎬 Action: {tool_name} with args {arguments}")
            tool_function = available_tools.get(tool_name)

            if not tool_function:
                result = f"Error: Tool '{tool_name}' not found."
            elif tool_name == "finish":
                print("✅ Agent has decided to finish the task.")
                history.append(f"Action: finish({arguments})")
                break 
            else:
                # The orchestrator is now "dumb" - it just calls the tool.
                # All path logic is handled inside the toolkit's methods.
                result = tool_function(**arguments)

            print(f"📊 Result: {result}")
            history.append(f"Action: {tool_name}({arguments})")
            history.append(f"Result: {result}")

        except Exception as e:
            print(f"An unexpected error occurred in the agent loop: {e}")
            history.append(f"Result: Error - {e}")

    print("\n--- AGENT FINISHED ---")

# Local testing block remains the same
if __name__ == "__main__":
    test_project_path = "tests" 
    os.makedirs(test_project_path, exist_ok=True)

    # Re-create the buggy file each time for a clean test
    with open(os.path.join(test_project_path, "calculator.py"), "w") as f:
        f.write("def add(a, b):\n  return a - b\n\ndef multiply(a, b):\n  return a % b")

    test_goal = "The `add` and `multiply` functions in `calculator.py` are buggy. Fix them. The add function should use '+' and the multiply function should use '*'. Verify your fix by reading the file after writing to it, then finish."
    run_agent(goal=test_goal, project_path=test_project_path)