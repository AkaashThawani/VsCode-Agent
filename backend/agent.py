# backend/agent.py

import os
import json
import inspect
import google.generativeai as genai
from dotenv import load_dotenv

# Import our Toolkit class
from toolkit import Toolkit

# --- Configuration ---
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
MODEL = genai.GenerativeModel('gemini-1.5-pro-latest')

AGENT_PROMPT = """
You are AgentDev, a senior AI software architect. Your purpose is to be a methodical, self-correcting, and communicative partner. You always explain your reasoning and adapt to new information.

**RESPONSE FORMAT:**
- Your response MUST be a single, valid JSON object with a 'thought' and an 'action'.
- Your 'thought' is your internal monologue, explaining your analysis and the reasoning for your action.

---
**AVAILABLE TOOLS:**
{tool_definitions}
---

**CORE REASONING DIRECTIVE: The Strategic Development Loop**

**[Step 1: Goal Triage & Strategic Planning]**
Your very first thought upon receiving a goal MUST classify it and outline a high-level plan.

*   **If the goal is actionable (coding or exploring):**
    -   **Classification:** Code Modification or Project Summarization.
    -   **Plan:** State your multi-step plan (e.g., "1. List files. 2. Analyze relevant files. 3. Read file content. 4. Act/Summarize.").
    -   **Action:** Execute the *first step* of your plan.

*   **If the goal is ambiguous or conversational:**
    -   **Classification:** Ambiguous Goal.
    -   **Plan:** State that you need to ask the user for clarification.
    -   **Action:** You MUST use the `finish` tool. Your clarifying question MUST be placed in the `reason` argument. This is your primary method for communicating with the user.

**[Step 2: Plan Execution & Analysis]**
For each subsequent step, your thought MUST analyze the result of the previous action and state the next step you are taking.

**[Step 3: Self-Correction & Plan Adaptation (Situational Awareness)]**
If a tool fails or the result is unexpected, you MUST NOT blindly retry. Your thought MUST diagnose the failure and explicitly adapt your plan.

*   **Failure Scenario: `analyze_code_structure` Fails**
    -   **Diagnosis:** "The `analyze_code_structure` tool failed, likely because the target is not a Python file. The tool is not appropriate for this language."
    -   **Adapted Plan:** "My new plan is to switch to using `read_file` to analyze the file's raw content directly."
    -   **Action:** Your next action MUST be to use `read_file` on the problematic file.

**[Step 4: Conclusion & Summarization]**
-   For **Code Modification**, your final action is the `finish` tool, stating what you successfully changed.
-   For **Project Summarization**, after reading all files, your final thought MUST be to synthesize the information. Your final action MUST be the `finish` tool, and the `reason` argument MUST contain your complete, multi-file summary.

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


def run_agent(goal: str, project_path: str):
    toolkit = Toolkit(project_path)
    available_tools = toolkit.get_tools()
    tool_defs = get_tool_definitions(available_tools)
    history = []
    max_loops = 10
    loop_count = 0

    while loop_count < max_loops:
        loop_count += 1
        history_str = "\n".join(history)
        prompt = AGENT_PROMPT.format(
            goal=goal, history=history_str, tool_definitions=tool_defs)

        response = MODEL.generate_content(prompt)

        try:
            response_text = response.text.strip()

            # Robustly find and extract the JSON object from the model's response
            json_start_index = response_text.find('{')
            json_end_index = response_text.rfind('}') + 1

            if json_start_index == -1 or json_end_index == 0:
                yield {"type": "thought", "content": f"Agent responded with non-JSON: {response_text}"}
                history.append(
                    f"Result: Agent returned a non-actionable response: {response_text}")
                continue

            json_str = response_text[json_start_index:json_end_index]
            parsed_response = json.loads(json_str)

            thought = parsed_response.get("thought", "")
            action = parsed_response.get("action", {})
            tool_name = action.get("tool_name")
            arguments = action.get("arguments", {})
            if thought.lower().startswith("classification:"):
                yield {"type": "classification", "content": thought}
            else:
                yield {"type": "thought", "content": thought}

            yield {"type": "thought", "content": thought}
            history.append(f"Thought: {thought}")

            if not tool_name:
                yield {"type": "status", "content": "Agent did not specify a tool."}
                continue

            tool_function = available_tools.get(tool_name)
            if not tool_function:
                result = f"Error: Tool '{tool_name}' not found."
                yield {"type": "error", "content": result}
                history.append(f"Result: {result}")
                continue

            # --- MODIFIED TOOL HANDLING LOGIC ---

            history.append(f"Action: {tool_name}({arguments})")

            if tool_name == "finish":
                finish_reason = arguments.get("reason", "Task completed.")
                yield {"type": "status", "content": f"Agent has finished the task. {finish_reason}"}
                break  # Exit the loop

            elif tool_name == "ask_user_for_clarification":
                # Special handling: This tool asks the user and then STOPS the agent's turn.
                question = tool_function(**arguments)
                yield {"type": "result", "content": question}
                # We don't append its result to history to avoid self-confusion.
                # The agent's turn is now over.
                break  # IMPORTANT: Exit the loop to prevent looping

            else:
                # This is the normal execution path for all other tools.
                action_summary = f"Running tool: {tool_name} with arguments: {arguments}"
                yield {"type": "action", "content": action_summary}

                result = tool_function(**arguments)
                yield {"type": "result", "content": str(result)}
                # Append the result for the next loop
                history.append(f"Result: {result}")

        except json.JSONDecodeError as e:
            # type: ignore
            # type: ignore
            # pyright: ignore[reportPossiblyUnboundVariable]
            # pyright: ignore[reportPossiblyUnboundVariable]
            yield {"type": "error", "content": f"Failed to decode JSON from model response: {e}\nResponse was:\n{response_text}"}
            history.append(f"Result: Error - Invalid JSON in response.")
        except Exception as e:
            yield {"type": "error", "content": f"An unexpected error occurred: {e}"}
            history.append(f"Result: Error - {e}")
