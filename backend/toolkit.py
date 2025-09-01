# backend/toolkit.py

import os
import inspect
from pathlib import Path
import ast

class Toolkit:
    def __init__(self, project_path: str):
        """
        Initializes the Toolkit with a specific project sandbox path.
        All tool operations will be relative to this path.
        """
        self.sandbox_path = os.path.abspath(project_path)
        print(f"Toolkit initialized with sandbox: {self.sandbox_path}")

    def _get_safe_path(self, relative_path: str) -> str:
        """
        Constructs a safe, absolute path within the sandbox.
        Prevents directory traversal attacks.
        """
        # Join the sandbox path with the relative path from the agent
        safe_path = os.path.join(self.sandbox_path, relative_path)
        # Get the absolute path to resolve any '..' etc.
        safe_path = os.path.abspath(safe_path)

        # CRITICAL SECURITY CHECK:
        # Ensure the resolved path is still inside the sandbox directory
        if not safe_path.startswith(self.sandbox_path):
            raise PermissionError(
                "Error: Attempted to access a file outside the sandboxed project directory.")

        return safe_path

    def list_files(self, path: str) -> str:
        """
        Lists all files and directories in a given path.
        The path should be relative to the project's root directory (e.g., '.' or 'src/').
        """
        try:
            safe_path = self._get_safe_path(path)

            if not os.path.isdir(safe_path):
                return f"Error: '{path}' is not a valid directory."

            paths = sorted(Path(safe_path).rglob('*'))
            if not paths:
                return "The directory is empty."

            tree_str = "Directory listing:\n"
            for p in paths:
                relative_p = p.relative_to(safe_path)
                tree_str += f" - {relative_p}\n"
            return tree_str
        except Exception as e:
            return f"Error listing files: {e}"

    def read_file(self, file_path: str) -> str:
        """
        Reads the content of a specified file.
        The file_path should be relative to the project's root directory.
        """
        try:
            safe_path = self._get_safe_path(file_path)
            with open(safe_path, 'r', encoding='utf-8') as f:
                content = f.read()
                return f"Successfully read {file_path}. Now analyzing its content."
        except FileNotFoundError:
            return f"Error: File not found at '{file_path}'."
        except Exception as e:
            return f"Error reading file: {e}"

    def write_file(self, file_path: str, content: str) -> str:
        """
        Writes content to a specified file, overwriting it if it exists.
        The file_path should be relative to the project's root directory.
        """
        try:
            if content.endswith("\n\nBegin."):
                content = content[:-8]
            elif content.endswith("\nBegin."):
                content = content[:-7]
            safe_path = self._get_safe_path(file_path)

            parent_dir = os.path.dirname(safe_path)
            os.makedirs(parent_dir, exist_ok=True)

            with open(safe_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"Successfully wrote to {file_path}."
        except Exception as e:
            return f"Error writing to file: {e}"

    def search_and_replace(self, file_path: str, search_string: str, replace_string: str) -> str:
        """
        Performs a surgical search and replace on a file. This is the preferred tool for editing existing files.
        """
        try:
            safe_path = self._get_safe_path(file_path)
            with open(safe_path, 'r', encoding='utf-8') as f:
                content = f.read()

            new_content = content.replace(search_string, replace_string)

            if new_content == content:
                return f"Warning: Search string was not found in {file_path}. No changes were made."

            with open(safe_path, 'w', encoding='utf-8') as f:
                f.write(new_content)

            return f"Successfully performed search and replace in {file_path}."
        except FileNotFoundError:
            return f"Error: File not found at '{file_path}'."
        except Exception as e:
            return f"Error during search and replace: {e}"

    def replace_code_block(self, file_path: str, original_code_block: str, new_code_block: str) -> str:
        """
        Surgically replaces a multi-line block of code in a file with a new one.
        This is the primary tool for all code editing.
        """
        try:
            safe_path = self._get_safe_path(file_path)
            with open(safe_path, 'r', encoding='utf-8') as f:
                content = f.read()

            new_content = content.replace(original_code_block, new_code_block)

            if new_content == content:
                return "Error: The 'original_code_block' was not found in the file. No changes were made. Please use read_file to get the exact block of code."

            with open(safe_path, 'w', encoding='utf-8') as f:
                f.write(new_content)

            return f"Successfully replaced code block in {file_path}."
        except FileNotFoundError:
            return f"Error: File not found at '{file_path}'."
        except Exception as e:
            return f"Error during code replacement: {e}"

    def ask_user_for_clarification(self, question: str) -> str:
        """
        Use this tool when the user's request is ambiguous, conversational,
        or not a clear coding task. Asks the user a clarifying question.
        """
        # This tool doesn't do anything on the backend, it just returns the question
        # to be displayed in the chat, giving the agent a valid conversational action.
        return question

    def get_tool_definitions(tools: dict):  # type: ignore
        """
        Generates a formatted string of tool definitions from a dictionary of functions.
        """
        definitions = ""
        for name, func in tools.items():
            sig = inspect.signature(func)
            # Format the signature, e.g., "read_file(file_path: str) -> str"
            sig_str = f"{name}{sig}"
            # Get the first line of the docstring
            doc = func.__doc__.strip().split('\n')[0]
            definitions += f"- Function: `{sig_str}`\n"
            definitions += f"  - Description: {doc}\n"
        return definitions

    def analyze_code_structure(self, file_path: str) -> str:
        """
        Analyzes a Python file to extract its structure (classes, functions, and global variables).
        This is the primary tool for understanding code before reading the full file.
        """
        try:
            safe_path = self._get_safe_path(file_path)
            with open(safe_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content)
            summary = f"Analysis of {file_path}:\n"

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    summary += f"- Contains Class: `{node.name}`\n"
                elif isinstance(node, ast.FunctionDef):
                    summary += f"- Contains Function: `{node.name}`\n"
                elif isinstance(node, ast.Assign):
                    # This is a simplification for global variables
                    if isinstance(node.targets[0], ast.Name):
                        summary += f"- Contains Global Variable: `{node.targets[0].id}`\n"

            if summary == f"Analysis of {file_path}:\n":
                return f"No classes, functions, or global variables found in {file_path}."

            return summary
        except Exception as e:
            return f"Error analyzing file {file_path}: {e}"

    def finish(self, reason: str) -> str:
        """
        Call this function when you have successfully completed the goal.
        """
        return f"Agent has finished the task. Reason: {reason}"

    def get_tools(self) -> dict:
        """Returns a dictionary of available tools."""
        return {
            "list_files": self.list_files,
            "read_file": self.read_file,
            "write_file": self.write_file,
            "finish": self.finish,
            "search_and_replace": self.search_and_replace,
            "replace_code_block": self.replace_code_block,
            "ask_user_for_clarification": self.ask_user_for_clarification,
            "analyze_code_structure": self.analyze_code_structure
        }
