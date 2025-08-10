import os
from pathlib import Path

def list_files(directory_path:str) -> str:
    """
    Lists all files and directories in a given path relative to the project root.
    Returns a string with the directory tree.
    """
    try:
        if ".." in directory_path.split(os.path.sep):
            return "Access to parent directories is not allowed."
        
        path = Path(directory_path)
        if not path.is_dir():
            return "Invalid directory path."
        
        tree_str = f"Directory listing for: {directory_path}\n"
        for p in sorted(path.rglob('*')):
            depth = len(p.relative_to(path).parts)
            indent =  '  ' * depth
            tree_str += f"{indent}|-- {p.name}\n"
        return tree_str

    except Exception as e:
        return f"Error occurred: {e}"
    

def read_file(file_path:str) -> str:
    """
    Reads the contents of a file and returns it as a string.
    """
    try:
        if ".." in file_path.split(os.path.sep):
            return "Access to parent directories is not allowed."
        
        path = Path(file_path)
        if not path.is_file():
            return "Invalid file path."
        
        with path.open('r', encoding='utf-8') as file:
            content = file.read()
        return content

    except Exception as e:
        return f"Error occurred: {e}"
    

def write_file(file_name:str, content:str) -> str:
    """
    Writes the given content to a file.
    """
    try:
        if ".." in file_name.split(os.path.sep):
            return "Access to parent directories is not allowed."
        os.makedirs(os.path.dirname(file_name), exist_ok=True)
        path = Path(file_name)
        with path.open('w', encoding='utf-8') as file:
            file.write(content)
        return "File written successfully."

    except Exception as e:
        return f"Error occurred: {e}"


AVAILABLE_TOOLS = {
    "list_files": list_files,
    "read_file": read_file,
    "write_file": write_file
}