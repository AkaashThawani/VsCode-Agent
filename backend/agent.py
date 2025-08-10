import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
import inspect


from toolkit import AVAILABLE_TOOLS

# configurations
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
MODEL = genai.GenerativeModel("gemini-1.5-pro")


AGENT_PROMPT = """

You are AgentDev , an expert AI software Developer.
Your goal is to complete user requests by utilizing the available tools.

You are operating within a sandboxed environment with limited access to external resources. You must use the tools available to you.Do not assume you have direct access.

**Tools**
Here is a list of tools you can use.You must respond in a JSON format that describes the tool call you want to make.

{tool_definitions}

**RESPONSE FORMAT:**
You must respond with a single, valid JSON object containing two keys: "thought" and "action".
- "thought": A string explaining your reasoning for the chosen action.
- "action": A JSON object representing the tool call, with "tool_name" and "arguments".

Example of a valid response:
{{
  "thought": "I need to see what files are in the current project to understand the structure.",
  "action": {{
    "tool_name": "list_files",
    "arguments": {{
      "directory_path": "."
    }}
  }}
}}

**CURRENT GOAL:**
{goal}

**HISTORY OF ACTIONS:**
This is the history of actions you have taken so far, and their results.
Use this to inform your next step.
{history}

Begin.

"""


def get_tool_definitions():
    """Formats the tool functions into a string for the prompt."""
    definitions = ""
    for name, func in AVAILABLE_TOOLS.items():
         # Get the function signature
        sig = inspect.signature(func)
        # Format the function signature string (e.g., "list_files(path: str)")
        sig_str = f"{name}{sig}"
        
        definitions += f"- Function: {sig_str}\n"
        definitions += f"  - Description: {func.__doc__.strip()}\n"
    return definitions


def run_agent(goal: str, project_path: str):
    """The main loop for the autonomous agent."""
    print(f"--- AGENT STARTING ---")
    print(f"Goal: {goal}")
    print(f"Project Path: {project_path}")

    history = []
    # Safety break to prevent infinite loops during development
    max_loops = 10
    loop_count = 0

    while loop_count < max_loops:
        loop_count += 1
        print(f"\n--- LOOP {loop_count} ---")

        # 1. CONSTRUCT THE PROMPT
        tool_defs = get_tool_definitions()
        history_str = "\n".join(history)
        prompt = AGENT_PROMPT.format(
            tool_definitions=tool_defs,
            goal=goal,
            history=history_str
        )

        # 2. CALL THE "THINKER" (LLM)
        print("🤔 Agent is thinking...")
        response = MODEL.generate_content(prompt)

        try:
            # 3. PARSE THE RESPONSE
            response_text = response.text.strip()
            print(f"RAW Response:\n{response_text}")

            # Clean the response to be valid JSON
            json_str_match = response_text[response_text.find(
                '{'):response_text.rfind('}')+1]
            parsed_response = json.loads(json_str_match)

            thought = parsed_response.get("thought", "")
            action = parsed_response.get("action", {})
            tool_name = action.get("tool_name")
            arguments = action.get("arguments", {})

            print(f"💡 Thought: {thought}")
            history.append(f"Thought: {thought}")

            # 4. EXECUTE THE ACTION
            if not tool_name:
                print("ERROR: No tool name found in response.")
                history.append("Result: No tool name found.")
                continue

            print(f"🎬 Action: {tool_name} with args {arguments}")

            tool_function = AVAILABLE_TOOLS.get(tool_name)
            if not tool_function:
                print(f"ERROR: Tool '{tool_name}' not found.")
                result = f"Error: Tool '{tool_name}' not found."
            else:
               # Security: Prepend the project path to any file/directory paths
                for key, value in arguments.items():
                    # Check if the key contains 'path' and the value is a string
                    if isinstance(value, str) and ("path" in key or "file" in key or "directory" in key):
                        # Do not prepend if the path is already absolute
                        if not os.path.isabs(value):
                            arguments[key] = os.path.join(project_path, value)

                result = tool_function(**arguments)

            print(f"📊 Result: {result}")
            history.append(f"Action: {tool_name}({arguments})")
            history.append(f"Result: {result}")

        except (json.JSONDecodeError, AttributeError) as e:
            print(f"ERROR: Could not parse LLM response. Error: {e}")
            print(f"Response text was: {response.text}")
            history.append(f"Result: Error parsing response - {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            history.append(f"Result: An unexpected error occurred - {e}")

    print("\n--- AGENT FINISHED ---")


if __name__ == "__main__":
    # This block allows us to test the agent directly without the web server.

    # 1. Create a dummy project for the agent to work on
    test_project_path = "test_project"
    os.makedirs(test_project_path, exist_ok=True)
    with open(os.path.join(test_project_path, "main.py"), "w") as f:
        f.write("print('Hello, World!')\n")
    with open(os.path.join(test_project_path, "README.md"), "w") as f:
        f.write("# My Test Project\n")

    # 2. Define the goal for the agent
    # A simple goal to start:
    # test_goal = "List all the files in the project."

    # A more complex goal:
    test_goal = "Read the README.md file, then write a new file called 'summary.txt' containing the text 'This is a test summary.'"

    # 3. Run the agent
    run_agent(goal=test_goal, project_path=test_project_path)
