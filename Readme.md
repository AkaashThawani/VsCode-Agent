# AgentDev-VSCode: An Autonomous AI Developer Agent for VS Code

# Description

An experimental VS Code extension that integrates an autonomous AI agent into your development workflow, allowing you to delegate coding tasks to an AI-powered pair programmer that analyzes codebases and executes changes.

## Overview

AgentDev is an experimental, proof-of-concept Visual Studio Code extension that integrates a powerful, autonomous AI agent directly into your development workflow. The agent is designed to understand high-level software development tasks, reason about an existing codebase, and execute the necessary steps to implement features, fix bugs, or perform refactoring.

The agent operates on any cloned project within VS Code, acting as an AI-powered pair programmer that you can delegate tasks to.

## Core Features

-   **🤖 Autonomous Task Execution:** Give the agent a high-level goal (e.g., "double the speed of the paddle in my game"), and it will formulate and execute a plan to achieve it.
-   **🧠 Code Analysis & Understanding:** The agent doesn't just guess; it reads files, analyzes their structure to find relevant classes and functions, and bases its actions on the actual code.
-   **🔍 Self-Correction:** If an action fails (e.g., it tries to modify a variable that doesn't exist), the agent can analyze the error, re-read the code, and attempt a new, more accurate solution.
-   **📄 File System Operations:** The agent can list, read, and write files, allowing it to understand and modify your entire project.
-   **💬 Real-Time Thought Streaming:** See the agent's complete internal monologue—its plans, actions, and analysis—streamed live into a dedicated panel in VS Code.

## Core Philosophy

This project is built on a client-server architecture to leverage the best of two ecosystems:

1.  **Python Backend:** For state-of-the-art AI, LLM orchestration, and robust logic, leveraging the extensive Python AI/ML ecosystem.
2.  **VS Code Extension Frontend (TypeScript):** For a seamless, native user experience, deep integration with the developer's workspace, and real-time feedback.

---

## Quick Start

### Prerequisites

- Node.js and npm (for the VS Code extension)
- Python 3.8+ (for the backend)
- Ollama running with a supported model (e.g., llama3.2)

### Installation

1. Clone this repository:
   ```
   git clone https://github.com/AkaashThawani/VsCode-Agent.git
   cd VsCode-Agent
   ```

2. Install backend dependencies:
   ```
   cd backend
   pip install -r requirements.txt
   ```

3. Install frontend dependencies:
   ```
   cd ../frontend/agentdev
   npm install
   ```

4. Build the VS Code extension:
   ```
   npm run compile
   ```

5. Run the backend:
   ```
   cd ../../backend
   python main.py
   ```

6. Open the extension in VS Code (press F5 for development).

## High-Level Architecture

1.  **VS Code Extension (Client):**
    *   Provides the User Interface (UI) via a custom Webview panel.
    *   Gathers context from the user's workspace (active project path, current goal).
    *   Communicates with the backend via a REST API.
    *   Streams the agent's progress back to the user in real-time.

2.  **Python Agent Server (Backend):**
    *   A FastAPI server that exposes endpoints for the agent's capabilities.
    *   Contains the core "Think -> Act -> Observe" reasoning loop.
    *   Manages the interaction with a Large Language Model via Ollama.
    *   Provides a "Toolkit" of functions the agent can use to interact with the file system within a sandboxed project directory.

---

## Future Roadmap

-   **[ ] Shell/Bash Tool:** Implement an `execute_bash(command)` tool with safety guardrails to allow the agent to run build scripts.
-   **[ ] Test Execution:** Add tools to run a project's test suite, allowing the agent to validate its changes.
-   **[ ] Git Integration:** Add `git_...` tools to allow the agent to automatically create a new branch for its work and commit when done.
-   **[ ] VS Code Settings UI:** Create a dedicated section in the VS Code settings for easier configuration of the API key and other parameters.
