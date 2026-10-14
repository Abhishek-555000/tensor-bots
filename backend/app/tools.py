from pathlib import Path
from typing import List
from langchain_core.tools import tool
from app.events import emit


def _safe_resolve(root: Path, relative_path: str) -> Path:
    """
    Safely resolves a path and enforces that it stays strictly inside the root directory.
    Rejects directory traversal (..) and absolute path escapes.
    """
    clean_path = relative_path.strip().lstrip("/\\")
    target = (root / clean_path).resolve()
    resolved_root = root.resolve()
    
    if resolved_root != target and resolved_root not in target.parents:
        raise ValueError(f"Access denied: path '{relative_path}' resolves outside the workspace sandbox.")
    return target


def make_file_tools(root: Path):
    """
    Factory function returning LangChain tools bound to the specified sandbox root.
    """
    root.mkdir(parents=True, exist_ok=True)

    @tool
    def write_file(path: str, content: str) -> str:
        """
        Write text content to a file inside the sandboxed workspace.
        Creates any necessary parent directories.
        
        Args:
            path: Relative file path (e.g., 'index.html', 'css/style.css', 'app.py').
            content: Complete text content of the file.
        """
        try:
            target = _safe_resolve(root, path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            
            byte_count = len(content.encode("utf-8"))
            rel_str = str(target.relative_to(root.resolve()))
            
            # Emit telemetry event for the UI and flow diagram
            emit("file_written", agent="developer", path=rel_str, bytes=byte_count)
            return f"Successfully wrote {byte_count} bytes to {rel_str}"
        except Exception as e:
            return f"Error writing file '{path}': {str(e)}"

    @tool
    def read_file(path: str) -> str:
        """
        Read the contents of a file inside the sandboxed workspace.
        
        Args:
            path: Relative file path to read.
        """
        try:
            target = _safe_resolve(root, path)
            if not target.exists():
                return f"Error: File '{path}' does not exist."
            if not target.is_file():
                return f"Error: '{path}' is a directory, not a file."
            return target.read_text(encoding="utf-8")
        except Exception as e:
            return f"Error reading file '{path}': {str(e)}"

    @tool
    def list_files(directory: str = ".") -> str:
        """
        List all files and subdirectories inside the workspace directory.
        
        Args:
            directory: Relative directory path to list (defaults to root '.').
        """
        try:
            target_dir = _safe_resolve(root, directory)
            if not target_dir.exists():
                return f"Error: Directory '{directory}' does not exist."
            
            files: List[str] = []
            for item in sorted(target_dir.rglob("*")):
                if item.is_file():
                    files.append(str(item.relative_to(root.resolve())))
            
            if not files:
                return "Workspace is currently empty (no files found)."
            return "Files in workspace:\n" + "\n".join(f"- {f}" for f in files)
        except Exception as e:
            return f"Error listing files: {str(e)}"

    return [write_file, read_file, list_files]
