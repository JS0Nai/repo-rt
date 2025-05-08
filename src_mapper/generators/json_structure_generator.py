# src_mapper/generators/json_structure_generator.py

import json
from pathlib import Path
from typing import Dict, Any, List

def _build_json_structure_tree(file_info_list: List[Dict[str, Any]], repo_root_path: Path) -> Dict[str, Any]:
    """
    Builds a nested dictionary representing the file tree structure (no content).
    File nodes are marked with None as value.
    """
    structure_tree = {}
    
    for file_info in file_info_list:
        relative_path_parts = file_info['relative_path_posix'].split('/')
        
        # Navigate to the right spot in the tree
        current_level = structure_tree
        for i, part in enumerate(relative_path_parts[:-1]):  # All parts except the filename
            if part not in current_level:
                current_level[part] = {}  # Create directory node if it doesn't exist
            current_level = current_level[part]
        
        # Add the file (last part) with None value to indicate it's a file
        filename = relative_path_parts[-1]
        current_level[filename] = None
    
    return structure_tree

def generate_json_structure(
    file_info_list: List[Dict[str, Any]],
    repo_root_path: Path,
    repo_name: str,
    output_file_path: Path,
    config_module
) -> None:
    """
    Generates a JSON file containing only the repository's structure (no file content).
    
    Args:
        file_info_list: List of dictionaries containing file metadata
        repo_root_path: Path to repository root
        repo_name: Name of the repository
        output_file_path: Path to write the JSON output file
        config_module: Configuration module with constants
    """
    # Build the structure tree
    structure_tree = _build_json_structure_tree(file_info_list, repo_root_path)
    
    # Create the final JSON object with repo name as the root key
    json_data = {repo_name: structure_tree}
    
    # Write the JSON to the output file
    with open(output_file_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2)