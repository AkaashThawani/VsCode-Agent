# backend/toolkit.py

import os
import inspect
from pathlib import Path

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
            raise PermissionError("Error: Attempted to access a file outside the sandboxed project directory.")
        
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
                return f.read()
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
            safe_path = self._get_safe_path(file_path)
            
            parent_dir = os.path.dirname(safe_path)
            os.makedirs(parent_dir, exist_ok=True)
            
            with open(safe_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"Successfully wrote to {file_path}."
        except Exception as e:
            return f"Error writing to file: {e}"

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
        }