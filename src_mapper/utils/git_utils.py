# src_mapper/utils/git_utils.py

import subprocess
import sys # Import sys for stderr
from pathlib import Path
from typing import Optional, Dict, Any

def is_git_repository(repo_root_path: Path) -> bool:
    """Checks if the given path is the root of a Git repository."""
    return (repo_root_path / ".git").is_dir()

def get_last_commit_info(relative_file_path: Path, repo_root_path: Path, timeout: int = 10) -> Optional[Dict[str, str]]:
    """
    Gets the last commit information for a specific file using `git log`.
    Returns a dict with 'hash', 'author_name', 'author_email', 'date_iso', 'subject'
    or None if not found, not a git repo, or error.
    """
    if not is_git_repository(repo_root_path):
        # print("Debug: Not a Git repository, skipping git info.", file=sys.stderr) # Optional debug
        return None

    try:
        # Using null byte as delimiter for fields, and ISO8601 strict for date
        # %H: commit hash
        # %an: author name
        # %ae: author email
        # %aI: author date, strict ISO 8601 format
        # %s: subject line
        format_string = "%H%x00%an%x00%ae%x00%aI%x00%s"
        
        # Construct the git command
        command = [
            "git", "log", "-1", # Get only the last commit
            f"--pretty=format:{format_string}", # Specify output format
            "--", str(relative_file_path) # The file path (use -- to separate path from args)
        ]
        
        # Execute the command from the repository root
        result = subprocess.run(
            command,
            capture_output=True, # Capture stdout and stderr
            text=False, # Capture as bytes to handle potential encoding issues before decoding
            check=False, # Do not raise an exception for non-zero exit codes (e.g., file not tracked)
            cwd=str(repo_root_path), # Set the current working directory for the command
            timeout=timeout # Set a timeout
        )

        if result.returncode == 0 and result.stdout:
            # Decode stdout carefully, replacing errors
            output_str = result.stdout.decode('utf-8', errors='replace').strip()
            
            if not output_str: # Empty output means file likely not tracked or no commits yet
                # print(f"Debug: No git log output for {relative_file_path}", file=sys.stderr) # Optional debug
                return None
                
            parts = output_str.split('\x00')
            if len(parts) == 5:
                return {
                    "hash": parts[0],
                    "author_name": parts[1],
                    "author_email": parts[2],
                    "date_iso": parts[3],
                    "subject": parts[4]
                }
            else:
                # print(f"Warning: Unexpected git log output format for {relative_file_path}: {parts}", file=sys.stderr) # Optional warning
                return None # Indicate parsing failed
                
        elif result.returncode != 0:
             # print(f"Debug: Git log failed for {relative_file_path} (code {result.returncode}): {result.stderr.decode('utf-8', errors='replace').strip()}", file=sys.stderr) # Optional debug
             return None # Git command failed (e.g., file not found by git, untracked)

        return None # Should not be reached if returncode is 0 but stdout is empty

    except FileNotFoundError:
        # print("Warning: 'git' command not found. Git info will not be available.", file=sys.stderr) # Optional warning
        # Could set a global flag in main_orchestrator to avoid repeated warnings
        return None
    except subprocess.TimeoutExpired:
        # print(f"Warning: Git log command timed out for {relative_file_path}", file=sys.stderr) # Optional warning
        return None
    except Exception as e:
        # print(f"Warning: Unexpected error getting Git info for {relative_file_path}: {type(e).__name__}: {e}", file=sys.stderr) # Optional warning
        return None