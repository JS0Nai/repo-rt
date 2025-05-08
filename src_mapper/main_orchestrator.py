#!/usr/bin/env python3
# src_mapper/main_orchestrator.py

import argparse
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

# Adjust import paths
# This allows importing src_mapper as a package even if not installed
sys.path.insert(0, str(Path(__file__).parent.parent))

# Local imports using custom config loader
from src_mapper.custom_config_loader import get_config
cfg = get_config()
from src_mapper.utils import (
    count_lines,
    get_file_extension,
    get_file_timestamps,
    load_gitignore_patterns,
    should_ignore_by_gitignore,
    is_excluded_entirely
)
# Import git_utils functions here if include_git_info is possible
try:
    from src_mapper.utils import is_git_repository, get_last_commit_info
    _GIT_UTILS_AVAILABLE = True
except ImportError:
    _GIT_UTILS_AVAILABLE = False
    # Define dummy functions if git_utils is not available
    def is_git_repository(repo_root_path: Path) -> bool: return False
    def get_last_commit_info(relative_file_path: Path, repo_root_path: Path, timeout: int = 10) -> None: return None


from src_mapper.generators import (
    generate_html_map,
    generate_json_structure,
    generate_text_tree,
    generate_selective_map_and_report
)

def _setup_arg_parser() -> argparse.ArgumentParser:
    """Sets up the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Repo Mapper: Generate various representations of a repository's structure and content.",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "repo_path",
        help="Path to the repository to map. Use '..' to map the parent directory, '.' for the current directory."
    )
    
    # Generator options
    parser.add_argument(
        "--html", 
        action="store_true",
        help="Generate the interactive HTML map."
    )
    parser.add_argument(
        "--json-structure", 
        action="store_true",
        help="Generate the structure-only JSON file."
    )
    parser.add_argument(
        "--text-tree", 
        action="store_true",
        help="Generate the structure-only text tree file."
    )
    parser.add_argument(
        "--selective", 
        action="store_true",
        help="Generate the selective content JSON map AND its companion CSV scan report."
    )
    parser.add_argument(
        "--all", 
        action="store_true",
        help="Generate all available artifact types."
    )
    
    # Additional options
    parser.add_argument(
        "--output-dir", 
        type=str,
        help=f"Specify a custom output directory (defaults to {cfg.DEFAULT_OUTPUT_DIR_NAME}/ subdirectory)."\
             " Path is relative to the script's directory (repo-mapper/)."
    )
    
    # Add include-git-info only if git_utils is available
    if _GIT_UTILS_AVAILABLE:
        parser.add_argument(
            "--include-git-info", 
            action="store_true",
            help="Attempt to include last Git commit information in the CSV report. Requires git command."
        )
    else:
        # Add a dummy argument that does nothing if git_utils is not available
        parser.add_argument(
            "--include-git-info",
            action="store_true",
            help="Git utilities not available, this flag will be ignored.",
            dest="_include_git_info_ignored" # Use a different destination
        )

    return parser

def _create_output_directory(output_dir_path: Path) -> Path:
    """Creates the output directory if it doesn't exist."""
    try:
        output_dir_path.mkdir(parents=True, exist_ok=True)
        # Create .gitkeep if it doesn't exist
        gitkeep_path = output_dir_path / ".gitkeep"
        if not gitkeep_path.exists():
            try:
                gitkeep_path.touch()
            except Exception as e:
                 print(f"Warning: Could not create .gitkeep in output directory: {e}", file=sys.stderr)

        return output_dir_path
    except Exception as e:
        print(f"Error creating output directory {output_dir_path}: {e}", file=sys.stderr)
        sys.exit(1)

def _collect_all_file_info(target_repo_path: Path, gitignore_patterns: List[str], include_git_info: bool) -> List[Dict[str, Any]]:
    """Collects information about all files in the repository."""
    file_info_list = []
    
    # Validate the repository path
    if not target_repo_path.is_dir():
        print(f"Error: {target_repo_path} is not a valid directory", file=sys.stderr)
        sys.exit(1)
    
    # Check if it's a git repo if git info is requested
    is_git_repo = include_git_info and is_git_repository(target_repo_path)
    if include_git_info and not is_git_repo:
         print("Info: --include-git-info specified, but target is not a Git repository. Git info will be skipped.", file=sys.stderr)


    # Walk through the directory structure
    for root, dirs, files in os.walk(target_repo_path):
        root_path = Path(root)
        
        # Filter out directories that should be excluded entirely
        # Need to create relative path for exclusion check
        dirs_to_process = []
        for d in dirs:
            relative_dir_path = Path(os.path.relpath(root_path / d, target_repo_path))
            if not is_excluded_entirely(
                relative_dir_path,
                cfg.EXCLUDE_ENTIRELY_FOLDERS,
                gitignore_patterns
            ):
                dirs_to_process.append(d)
            # else:
                # print(f"Debug: Excluding directory {relative_dir_path}", file=sys.stderr) # Optional debug
        dirs[:] = dirs_to_process # Modify dirs in place for os.walk

        # Process each file
        for filename in files:
            absolute_path = root_path / filename
            relative_path = Path(os.path.relpath(absolute_path, target_repo_path))
            relative_path_posix = relative_path.as_posix()
            
            # Skip files that match gitignore patterns
            if should_ignore_by_gitignore(relative_path, gitignore_patterns):
                # print(f"Debug: Ignoring file {relative_path} by gitignore", file=sys.stderr) # Optional debug
                continue
            
            # Get file extension
            extension = get_file_extension(filename)
            
            # Get file size
            try:
                size_bytes = absolute_path.stat().st_size
            except Exception:
                size_bytes = 0 # File might have vanished or permission error
            
            # Count lines of code (only attempt for non-binary extensions)
            loc = 0
            if extension.lower() not in cfg.BINARY_FILE_EXTENSIONS:
                 loc = count_lines(absolute_path, cfg.ENCODINGS_TO_TRY)
            
            # Get file timestamps
            timestamp_created, timestamp_modified = get_file_timestamps(absolute_path)
            
            # Get Git info if requested and it's a git repo
            git_info = None
            if include_git_info and is_git_repo:
                 git_info = get_last_commit_info(relative_path, target_repo_path, cfg.GIT_COMMAND_TIMEOUT_SECONDS)

            # Collect all info in a dictionary
            file_info = {
                'name': filename,
                'absolute_path': absolute_path,
                'relative_path': relative_path, # Keep Path object
                'relative_path_posix': relative_path_posix, # Keep posix string
                'parent_dir_relative_posix': str(relative_path.parent),
                'extension': extension,
                'size_bytes': size_bytes,
                'loc': loc,
                'timestamp_created': timestamp_created,
                'timestamp_modified': timestamp_modified,
                'git_info': git_info # Add git info here
            }
            
            file_info_list.append(file_info)
    
    return file_info_list

def run_mapper(args: argparse.Namespace) -> None:
    """Main function to run the mapper with the given arguments."""
    # Resolve repository path
    repo_path_str = args.repo_path
    repo_root_path = Path(repo_path_str).resolve()
    
    # Determine the repository name (last part of the path)
    repo_name = repo_root_path.name
    
    # Create or use specified output directory
    if args.output_dir:
        output_dir = Path(args.output_dir).resolve()
    else:
        # Default: Create 'output' subdirectory in the current script's directory
        script_dir = Path(__file__).parent.parent  # repo-mapper/
        output_dir = script_dir / cfg.DEFAULT_OUTPUT_DIR_NAME
    
    output_dir = _create_output_directory(output_dir)
    
    # Load gitignore patterns
    gitignore_patterns = load_gitignore_patterns(repo_root_path)
    
    print(f"Scanning repository: {repo_root_path}")
    print(f"Output directory: {output_dir}")
    
    # Check if git info is requested and possible
    include_git_info = getattr(args, 'include_git_info', False) # Handle case where git_utils is not available
    if include_git_info and not _GIT_UTILS_AVAILABLE:
        print("Warning: --include-git-info requires git utilities to be available. Flag ignored.", file=sys.stderr)
        include_git_info = False # Disable if not possible

    # Collect file information (do this once for all generators)
    # Pass include_git_info down to collect git info during the walk
    file_info_list = _collect_all_file_info(repo_root_path, gitignore_patterns, include_git_info)
    
    print(f"Found {len(file_info_list)} files to process.")
    
    # Determine which artifacts to generate
    generate_html = args.html or args.all
    generate_json = args.json_structure or args.all
    generate_tree = args.text_tree or args.all
    generate_selective = args.selective or args.all
    
    # Check if nothing was selected
    if not any([generate_html, generate_json, generate_tree, generate_selective]):
        print("Error: No output format selected. Use --html, --json-structure, --text-tree, --selective, or --all.", file=sys.stderr)
        sys.exit(1)
    
    # Generate HTML map
    if generate_html:
        print("Generating HTML map...")
        html_output_path = output_dir / f"{repo_name}-mapper.html"
        generate_html_map(file_info_list, repo_root_path, repo_name, html_output_path, cfg)
        print(f"  HTML map saved to: {html_output_path}")
    
    # Generate JSON structure
    if generate_json:
        print("Generating JSON structure...")
        json_output_path = output_dir / f"{repo_name}-structure.json"
        generate_json_structure(file_info_list, repo_root_path, repo_name, json_output_path, cfg)
        print(f"  JSON structure saved to: {json_output_path}")
    
    # Generate text tree
    if generate_tree:
        print("Generating text tree...")
        tree_output_path = output_dir / f"{repo_name}-structure.txt"
        generate_text_tree(file_info_list, repo_root_path, repo_name, tree_output_path, cfg)
        print(f"  Text tree saved to: {tree_output_path}")
    
    # Generate selective map and scan report
    if generate_selective:
        print("Generating selective map and scan report...")
        json_map_path = output_dir / f"{repo_name}-selective_map.json"
        csv_report_path = output_dir / f"{repo_name}-scan_report.csv"
        
        # Pass include_git_info down to the generator
        generate_selective_map_and_report(
            file_info_list, 
            repo_root_path, 
            repo_name, 
            json_map_path, 
            csv_report_path, 
            cfg,
            include_git_info # Pass the flag
        )
        
        print(f"  Selective map saved to: {json_map_path}")
        print(f"  Scan report saved to: {csv_report_path}")
    
    print("\nRepo mapping complete!")

if __name__ == "__main__":
    parser = _setup_arg_parser()
    arguments = parser.parse_args()
    run_mapper(arguments)