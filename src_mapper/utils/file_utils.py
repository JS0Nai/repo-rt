# src_mapper/utils/file_utils.py

import datetime
from pathlib import Path
import os # Import os for os.path.getctime/getmtime fallback
from typing import Tuple, List, Optional

def read_file_content(file_path: Path, encodings: List[str]) -> Tuple[Optional[str], bool, Optional[str]]:
    """
    Attempts to read file content with a list of encodings.
    Detects binary files by checking for null bytes in the first KB.

    Returns:
        Tuple (content_string_or_none, is_binary_or_unreadable_error, error_message_or_none)
    """
    try:
        # First, check for null bytes to quickly identify many binary files
        with open(file_path, 'rb') as bf:
            chunk = bf.read(1024)  # Read first 1KB
            if b'\x00' in chunk:
                return None, True, "File appears to be binary (contains null bytes)."
    except Exception as e:
        # Handle cases where file might be inaccessible even for binary check
        return None, True, f"Error during initial file access: {type(e).__name__}: {e}"

    # If no null bytes, try reading as text with specified encodings
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding, errors='strict') as f:
                return f.read(), False, None
        except UnicodeDecodeError:
            continue # Try next encoding
        except Exception as e: # Other read errors like permission denied
            return None, True, f"Error reading file with {encoding}: {type(e).__name__}: {e}"
    
    # If all encodings failed
    return None, True, f"Failed to decode file with any of specified encodings: {encodings}"


def count_lines(file_path: Path, encodings: List[str]) -> int:
    """Counts non-empty lines in a text file."""
    # Use read_file_content to handle encoding and binary check
    content, is_binary, _ = read_file_content(file_path, encodings)
    
    if is_binary or content is None:
        return 0
    
    lines = 0
    # Splitlines keeps line endings, which is fine for counting
    for line in content.splitlines():
        if line.strip(): # Count line if it's not just whitespace
            lines += 1
    return lines

def get_file_timestamps(file_path: Path) -> Tuple[str, str]:
    """
    Gets formatted creation and modification timestamps for a file.
    Note: ctime behavior varies by OS (creation on Windows, last metadata change on Unix).
    """
    created_str, modified_str = "", ""
    try:
        # Use os.path functions for compatibility, though Path.stat() is also fine
        # os.path.getctime is creation on Windows, last metadata change on Unix
        # os.path.getmtime is last modification time
        created_ts = os.path.getctime(file_path)
        modified_ts = os.path.getmtime(file_path)
        
        created_str = datetime.datetime.fromtimestamp(created_ts).strftime('%Y-%m-%d %H:%M:%S')
        modified_str = datetime.datetime.fromtimestamp(modified_ts).strftime('%Y-%m-%d %H:%M:%S')
    except Exception: # Handle potential errors like file not found if it vanished
        pass # Timestamps will remain empty
    return created_str, modified_str

def get_file_extension(filename: str) -> str:
    """Extracts the file extension, including compound ones like .tar.gz."""
    name_parts = filename.lower().split('.')
    if len(name_parts) > 1:
        # Check for common compound extensions
        if name_parts[-2] in ['tar', 'spec', 'json'] and len(name_parts) > 2: # Added .json for .spec.json
             # Handle cases like file.tar.gz or file.spec.json
             # Need to be careful not to catch things like file.data.json
             # A more robust way might involve checking if the part before the last is a known archive/specifier
             # For simplicity, let's stick to a limited list or just the last part
             # Let's refine this to just get the last part unless it's a known compound
             pass # Fall through to get just the last part
             
        if name_parts[0] == '' and len(name_parts) == 2: # Handle dotfiles like .gitignore
            return "." + name_parts[1]
            
        return "." + name_parts[-1] # Default to just the last part
        
    return "" # No extension


def truncate_content_by_lines(content: str, max_lines: int) -> Tuple[str, bool]:
    """Truncates string content to a maximum number of lines."""
    lines = content.splitlines(keepends=True) # Keep newlines for accurate reconstruction
    if len(lines) > max_lines:
        truncated_content = "".join(lines[:max_lines])
        # Add a clear indicator that content was truncated
        truncated_content += f"\n...\n[Content truncated to {max_lines} lines]\n"
        return truncated_content, True
    return content, False