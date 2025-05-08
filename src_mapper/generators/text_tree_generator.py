# src_mapper/generators/text_tree_generator.py

from pathlib import Path
from typing import Dict, Any, List

def _build_text_tree_structure(file_info_list: List[Dict[str, Any]], repo_root_path: Path) -> Dict[str, Any]:
    """
    Builds a nested dictionary representing the file tree structure (no content).
    Identical to _build_json_structure_tree in json_structure_generator.py.
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

def _generate_tree_lines_recursive(tree_level_data: Dict[str, Any], prefix: str = "", is_last_item: bool = True) -> List[str]:
    """
    Recursively generates lines for the text tree representation.
    Uses box-drawing characters for formatting.
    """
    # Sort items: directories first, then files, both alphabetically
    sorted_items = sorted(
        tree_level_data.items(),
        key=lambda x: (not isinstance(x[1], dict), x[0].lower())
    )
    
    lines = []
    
    for i, (name, content_or_dir) in enumerate(sorted_items):
        is_last = (i == len(sorted_items) - 1)
        is_directory = isinstance(content_or_dir, dict)
        
        # Determine current line's connector
        connector = "└── " if is_last else "├── "
        
        # Add directory indicator for directories
        display_name = f"{name}/" if is_directory else name
        
        # Build current line
        current_line = f"{prefix}{connector}{display_name}"
        lines.append(current_line)
        
        # Process subdirectories recursively
        if is_directory:
            # Determine the prefix for children
            child_prefix = prefix + ("    " if is_last else "│   ")
            
            # Get lines for children and add them
            child_lines = _generate_tree_lines_recursive(content_or_dir, child_prefix, is_last)
            lines.extend(child_lines)
    
    return lines

def generate_text_tree(
    file_info_list: List[Dict[str, Any]],
    repo_root_path: Path,
    repo_name: str,
    output_file_path: Path,
    config_module
) -> None:
    """
    Generates a text-based tree view representation of the repository's structure.
    
    Args:
        file_info_list: List of dictionaries containing file metadata
        repo_root_path: Path to repository root
        repo_name: Name of the repository
        output_file_path: Path to write the text tree output file
        config_module: Configuration module with constants
    """
    # Build the structure tree
    structure_tree = _build_text_tree_structure(file_info_list, repo_root_path)
    
    # Generate the tree lines
    tree_lines = _generate_tree_lines_recursive(structure_tree)
    
    # Add the root directory line
    full_tree_lines = [f"{repo_name}/"] + tree_lines
    
    # Join the lines and write to the output file
    tree_content = "\n".join(full_tree_lines)
    
    with open(output_file_path, 'w', encoding='utf-8') as f:
        f.write(tree_content)