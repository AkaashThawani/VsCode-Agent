# AgentDev-VSCode: An Autonomous AI Developer Agent for VS Code

AgentDev-VSCode is an experimental, proof-of-concept Visual Studio Code extension that integrates a powerful, autonomous AI agent directly into your development workflow. The agent is designed to understand high-level software development tasks, reason about an existing codebase, and execute the necessary steps to implement features, fix bugs, or perform refactoring.

The agent operates on any cloned project within VS Code, acting as an AI-powered pair programmer that you can delegate tasks to.

## Core Philosophy

This project is built on a client-server architecture to leverage the best of two ecosystems:

1.  **Python Backend:** For state-of-the-art AI, LLM orchestration, and robust logic, leveraging the extensive Python AI/ML ecosystem.
2.  **VS Code Extension Frontend (TypeScript):** For a seamless, native user experience, deep integration with the developer's workspace, and real-time feedback.

---

## High-Level Architecture

![Architecture Diagram](https://i.imgur.com/your-architecture-diagram.png)  <!-- We will create this diagram later -->

1.  **VS Code Extension (Client):**
    *   Provides the User Interface (UI) via the command palette and a custom Webview panel.
    *   Gathers context from the user's workspace (active project path, current goal).
    *   Communicates with the backend via a REST API.
    *   Streams the agent's progress back to the user in real-time.

2.  **Python Agent Server (Backend):**
    *   A FastAPI server that exposes endpoints for the agent's capabilities.
    *   Contains the core "Think -> Act -> Observe" loop.
    *   Manages the interaction with the Large Language Model (e.g., Google Gemini).
    *   Provides a "Toolkit" of functions the agent can use to interact with the file system and execute commands within the specified project directory.

---

## Development Roadmap & Feature Plan

This project will be built in phases. Each phase represents a testable, functional milestone.

### Phase 1: The Core Backend Engine (Standalone Python)

The goal of this phase is to create a functional command-line version of the agent that can operate on a local directory. This validates the core AI logic before any UI is built.

*   **[ ] Task 1.1: Environment Setup:**
    *   Initialize Python project with a virtual environment (`venv`).
    *   Create `requirements.txt` (dependencies: `fastapi`, `uvicorn`, `python-dotenv`, `google-generativeai`).
*   **[ ] Task 1.2: The Agent Toolkit:**
    *   Implement foundational Python functions for file system interaction:
        *   `list_files(directory_path)`
        *   `read_file(file_path)`
        *   `write_file(file_path, content)`
    *   Ensure all tools operate safely within a designated "sandbox" directory.
*   **[ ] Task 1.3: The Agent Orchestrator:**
    *   Develop the main "Think -> Act -> Observe" loop.
    *   Craft the master agent prompt for the LLM (Gemini), defining its persona, goal, and available tools.
    *   Implement logic to send requests to the Gemini API.
*   **[ ] Task 1.4: FastAPI Server Wrapper:**
    *   Create a simple FastAPI server.
    *   Expose a single POST endpoint: `/execute-task`.
    *   This endpoint should accept `{ "goal": "...", "project_path": "..." }` and kick off the agent's orchestrator loop.
    *   The agent's output for now will be logged to the console.

**Milestone for Phase 1:** We can successfully send a request to the local server via a tool like `curl` or Postman, providing a goal and a path to a test project, and see the agent's thought process in the server console.

---

### Phase 2: The Basic VS Code Extension (The "Client")

The goal of this phase is to create the user-facing part of the extension and connect it to the backend server.

*   **[ ] Task 2.1: Extension Scaffolding:**
    *   Generate a new "TypeScript" VS Code extension project.
    *   Clean up boilerplate files.
*   **[ ] Task 2.2: User Input Command:**
    *   Register a command in `package.json` (e.g., `agentdev.startTask`).
    *   Implement the command in `extension.ts` to show a VS Code input box to get the user's goal.
*   **[ ] Task 2.3: Backend Communication:**
    *   Get the active workspace's root path using the `vscode.workspace` API.
    *   Write the TypeScript `fetch` call to send the goal and project path to the Phase 1 backend server.
*   **[ ] Task 2.4: Simple Notification Feedback:**
    *   On receiving a successful response from the server, display a native VS Code information message (e.g., "Agent task completed!").
    *   On error, display an error message.

**Milestone for Phase 2:** We can trigger the agent from the VS Code command palette, type a goal, and have it successfully run the task in the backend. Feedback is minimal, but the end-to-end connection is working.

---

### Phase 3: Real-Time UI and Advanced Features (Full Integration)

This phase focuses on creating a rich user experience and making the agent more powerful.

*   **[ ] Task 3.1: The Agent Status Webview:**
    *   Create a VS Code Webview panel.
    *   Implement a logging mechanism in the Python agent that writes status updates to a `agent.log` file in the target project.
    *   The Webview will monitor this log file for changes and display the agent's thought process in real-time.
*   **[ ] Task 3.2: Adding a Shell/Bash Tool:**
    *   Implement an `execute_bash(command)` tool in the Python toolkit.
    *   **Crucially:** Implement safety guardrails. The agent should ask for user permission before executing potentially destructive commands.
*   **[ ] Task 3.3: Self-Correction Loop:**
    *   Enhance the agent orchestrator to capture `stderr` from the bash tool.
    *   Feed the error message back to the LLM in the next loop, enabling it to debug and correct its own mistakes.
*   **[ ] Task 3.4: (Stretch Goal) Git Integration:**
    *   Add `git_create_branch`, `git_add`, and `git_commit` tools to the agent's toolkit.
    *   Allow the agent to automatically create a new branch for its work and commit it when done.

**Milestone for Phase 3:** A user can give the agent a complex task. A new panel opens in VS Code showing the agent's thoughts and actions live. The agent can run commands, recover from errors, and the user can see the resulting file changes directly in the VS Code editor.