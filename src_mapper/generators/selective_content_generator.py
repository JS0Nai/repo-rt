# src_mapper/generators/selective_content_generator.py

import csv
import fnmatch
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

# Import necessary utils functions
from ..utils import (
    read_file_content,
    truncate_content_by_lines,
    get_file_extension,
    get_file_timestamps # Import get_file_timestamps
)
# Import git_utils functions conditionally based on include_git_info flag
# from ..utils import get_last_commit_info, is_git_repository # Will import inside the function


def _determine_file_processing_action(
    file_info: Dict[str, Any], 
    config_module, 
    current_total_embedded_bytes: int
) -> Dict[str, Any]:
    """
    Determines how to process a file for the selective map based on heuristics.
    
    Args:
        file_info: Dictionary with file metadata (must include 'absolute_path', 'relative_path_posix', 'name', 'extension', 'loc', 'size_bytes')
        config_module: Configuration module with constants
        current_total_embedded_bytes: Current total bytes embedded so far
        
    Returns:
        Dictionary with:
            - content_status_detail: Status string with details on why/how content was processed
            - content_to_embed: Content string or None
            - processing_notes: Notes on processing decisions
            - embedded_chars_count: Length of content_to_embed if any
            - bytes_added_to_budget: Size of content_to_embed in bytes
    """
    result = {
        'content_status_detail': "",
        'content_to_embed': None,
        'processing_notes': "",
        'embedded_chars_count': 0,
        'bytes_added_to_budget': 0,
    }
    
    # Get file path info from file_info dict
    file_path = file_info['absolute_path']
    relative_path_posix = file_info['relative_path_posix']
    filename = file_info['name']
    extension = file_info.get('extension', '')
    loc = file_info.get('loc', 0)
    size_bytes = file_info.get('size_bytes', 0)
    
    # Check if this is a binary file extension
    if extension.lower() in config_module.BINARY_FILE_EXTENSIONS:
        result['content_status_detail'] = "Omitted (Binary)"
        result['processing_notes'] = f"Binary extension: {extension}"
        return result
    
    # Check if this is an extension whose content we generally exclude
    if extension.lower() in config_module.EXCLUDE_CONTENT_FILE_EXTENSIONS:
        # Check if it's *also* in the always include list (override exclusion)
        is_in_always_include = False
        for pattern in config_module.ALWAYS_INCLUDE_CONTENT_PATTERNS:
            if fnmatch.fnmatch(filename, pattern):
                is_in_always_include = True
                break
        
        if not is_in_always_include:
            result['content_status_detail'] = "Omitted (Excluded Type)"
            result['processing_notes'] = f"Excluded extension: {extension}"
            return result
    
    # Determine if this file is high priority based on patterns
    is_high_priority = False
    
    # Check against ALWAYS_INCLUDE_CONTENT_PATTERNS
    for pattern in config_module.ALWAYS_INCLUDE_CONTENT_PATTERNS:
        if fnmatch.fnmatch(filename, pattern):
            is_high_priority = True
            # Add note about why it's high priority, but don't overwrite existing notes if any
            if not result['processing_notes']:
                 result['processing_notes'] = f"High priority file (matched pattern: {pattern})"
            break
    
    # Check against INCLUDE_CONTENT_IN_FOLDERS_PATTERNS
    if not is_high_priority:
        for folder_pattern in config_module.INCLUDE_CONTENT_IN_FOLDERS_PATTERNS:
            if relative_path_posix.startswith(folder_pattern):
                is_high_priority = True
                if not result['processing_notes']:
                    result['processing_notes'] = f"High priority directory (matched: {folder_pattern})"
                break
    
    # Read file content (only if it's not already marked as omitted for binary/error)
    content, is_binary_read_error, error_msg = read_file_content(file_path, config_module.ENCODINGS_TO_TRY)
    
    # Handle binary or unreadable files detected during read
    if is_binary_read_error or content is None:
        result['content_status_detail'] = "Omitted (Binary/Read Error)"
        if error_msg:
            result['processing_notes'] = error_msg
        return result
    
    # Check for budget constraints *before* deciding on truncation/full inclusion
    max_budget_bytes = config_module.MAX_TOTAL_EMBEDDED_CONTENT_KB * 1024
    content_bytes = len(content.encode('utf-8'))
    
    if current_total_embedded_bytes + content_bytes > max_budget_bytes:
        result['content_status_detail'] = "Omitted (Budget Exceeded)"
        result['processing_notes'] = f"Budget limit reached ({max_budget_bytes / 1024:.1f}KB max)"
        # No content embedded
        return result
    
    # Determine if we need to truncate based on file size (LOC)
    if loc > config_module.LARGE_FILE_THRESHOLD_LINES:
        if is_high_priority:
            # Truncate high priority files to the high priority truncation length
            truncate_lines = config_module.TRUNCATE_LINES_FOR_INCLUDED
            truncated_content, was_truncated = truncate_content_by_lines(content, truncate_lines)
            
            result['content_to_embed'] = truncated_content
            if was_truncated:
                result['content_status_detail'] = "Truncated (High Priority/Large)"
                result['processing_notes'] += f" Truncated to {truncate_lines} lines (from {loc} total)"
            else:
                 # Should only happen if LOC count is > threshold but actual lines <= truncate_lines
                 result['content_status_detail'] = "Full (High Priority)" # Still full content
                 # No truncation note needed
            
        else:
            # Truncate non-priority large files to the default truncation length
            truncate_lines = config_module.TRUNCATE_LINES_DEFAULT
            truncated_content, was_truncated = truncate_content_by_lines(content, truncate_lines)
            
            result['content_to_embed'] = truncated_content
            if was_truncated:
                result['content_status_detail'] = "Truncated (Uncertain/Large)"
                result['processing_notes'] += f" Truncated to {truncate_lines} lines (from {loc} total)"
            else:
                 # Should only happen if LOC count is > threshold but actual lines <= truncate_lines
                 result['content_status_detail'] = "Full (Uncertain/Small)" # Still full content
                 # No truncation note needed

    else:
        # File is below the large threshold - include full content
        result['content_to_embed'] = content
        if is_high_priority:
            result['content_status_detail'] = "Full (High Priority)"
        else:
            result['content_status_detail'] = "Full (Uncertain/Small)"
        # No truncation note needed

    # Clean up processing notes if it only contains the high priority reason and no truncation/error
    if result['processing_notes'].startswith("High priority") and "Truncated" not in result['processing_notes'] and "Error" not in result['processing_notes']:
         result['processing_notes'] = result['processing_notes'].strip() # Keep the high priority note
    else:
         result['processing_notes'] = result['processing_notes'].strip() # Clean up any leading/trailing space


    # Calculate embedded content statistics *after* potential truncation
    if result['content_to_embed'] is not None:
        result['embedded_chars_count'] = len(result['content_to_embed'])
        result['bytes_added_to_budget'] = len(result['content_to_embed'].encode('utf-8'))
    
    return result


def _build_selective_map_structure(
    file_info_list: List[Dict[str, Any]], 
    config_module, 
    include_git_info: bool, 
    repo_root_path: Path # Need repo_root_path here for git_utils
) -> Tuple[Dict[str, Any], List[Dict[str, Any]], int, List[str]]:
    """
    Builds the selective map structure and the scan report entries.
    
    Returns:
        Tuple of (map_structure, scan_report_rows, total_embedded_bytes, csv_fields)
    """
    selective_map_data = {}
    scan_report_rows = []
    total_embedded_bytes = 0
    
    # Define CSV headers here to ensure correct order and inclusion of Git columns
    csv_fields = [
        "File Name", "Location", "Size (KB)", "Lines of Code (LOC)",
        "Date Created", "Date Modified", "Extension",
        "Included", "Truncated", "Omitted", "Content Status Detail",
        "Embedded Chars", "Processing Notes"
    ]
    
    if include_git_info:
        # Import git_utils only if needed
        try:
            from ..utils import get_last_commit_info, is_git_repository
            if is_git_repository(repo_root_path):
                 csv_fields.extend(["Last Commit Hash", "Last Commit Author", "Last Commit Date", "Last Commit Subject"])
            else:
                 print("Info: --include-git-info specified, but not a Git repository. Skipping Git info.", file=sys.stderr)
                 include_git_info = False # Turn off the flag if not a git repo
        except ImportError:
            print("Warning: Git utilities not available, skipping git info in report.", file=sys.stderr)
            include_git_info = False # Turn off the flag if git_utils is not implemented/accessible
        except Exception as e:
             print(f"Warning: Error checking git repository status: {e}. Skipping git info.", file=sys.stderr)
             include_git_info = False


    for file_info in file_info_list:
        relative_path_posix = file_info['relative_path_posix']
        relative_path = file_info['relative_path'] # Path object
        filename = file_info['name']
        
        # Determine how to process this file
        processing_result = _determine_file_processing_action(
            file_info, 
            config_module, 
            total_embedded_bytes
        )
        
        # Update the total embedded bytes
        total_embedded_bytes += processing_result['bytes_added_to_budget']
        
        # Navigate to the right spot in the map
        current_level = selective_map_data
        # Handle root directory case
        if relative_path_posix != filename: # If it's not a file directly in the root
            relative_dir_path_parts = relative_path_posix.split('/')[:-1]
            for part in relative_dir_path_parts:
                if part not in current_level:
                    current_level[part] = {}  # Create directory node if it doesn't exist
                current_level = current_level[part]
        
        # Add the file with metadata
        # Prepare file entry with metadata
        file_entry = {
            "_status": processing_result['content_status_detail'],
            "_loc": file_info.get('loc', 0),
        }
        
        # Add notes if any
        if processing_result['processing_notes']:
            file_entry["_notes"] = processing_result['processing_notes']
            
        # Add content if available
        if processing_result['content_to_embed'] is not None:
            file_entry["_content"] = processing_result['content_to_embed']
        
        # Add the file entry to the tree
        current_level[filename] = file_entry
        
        # Create a scan report row
        status_detail = processing_result['content_status_detail']
        included = "Yes" if "Full" in status_detail else "No"
        truncated = "Yes" if "Truncated" in status_detail else "No"
        omitted = "Yes" if "Omitted" in status_detail or "Excluded" in status_detail else "No" # Omitted includes Excluded (.gitignore)
        
        location_str = file_info['parent_dir_relative_posix']
        if location_str == ".": location_str = "/" # Represent root location as "/"

        scan_report_row = {
            "File Name": filename,
            "Location": location_str,
            "Size (KB)": f"{file_info.get('size_bytes', 0) / 1024:.2f}",
            "Lines of Code (LOC)": file_info.get('loc', 0),
            "Date Created": file_info.get('timestamp_created', ''),
            "Date Modified": file_info.get('timestamp_modified', ''),
            "Extension": file_info.get('extension', ''),
            "Included": included,
            "Truncated": truncated,
            "Omitted": omitted,
            "Content Status Detail": status_detail,
            "Embedded Chars": processing_result['embedded_chars_count'],
            "Processing Notes": processing_result['processing_notes']
        }
        
        # Add Git info if requested and available
        if include_git_info:
             # Git info was collected in _collect_all_file_info if requested there
             # We need to ensure _collect_all_file_info *also* collects git info if the flag is passed to main_orchestrator
             # For now, let's assume git info is added to file_info dict if requested
             # A better design would be to collect git info *here* if needed, or ensure it's in file_info
             # Let's modify _collect_all_file_info to add git_info if include_git_info is true
             # And then access it here
             git_info = file_info.get('git_info') # Assume git_info is added by _collect_all_file_info
             if git_info:
                 scan_report_row["Last Commit Hash"] = git_info.get("hash", "")
                 scan_report_row["Last Commit Author"] = git_info.get("author_name", "")
                 scan_report_row["Last Commit Date"] = git_info.get("date_iso", "")
                 scan_report_row["Last Commit Subject"] = git_info.get("subject", "")
             else:
                 scan_report_row["Last Commit Hash"] = ""
                 scan_report_row["Last Commit Author"] = ""
                 scan_report_row["Last Commit Date"] = ""
                 scan_report_row["Last Commit Subject"] = ""


        scan_report_rows.append(scan_report_row)
    
    return selective_map_data, scan_report_rows, total_embedded_bytes, csv_fields # Return csv_fields too


def generate_selective_map_and_report(
    file_info_list: List[Dict[str, Any]],
    repo_root_path: Path,
    repo_name: str,
    json_output_path: Path, 
    csv_output_path: Path,
    config_module,
    include_git_info: bool = False
) -> None:
    """
    Generates a selective content JSON map and CSV scan report.
    
    Args:
        file_info_list: List of dictionaries containing file metadata (should include git_info if include_git_info is True)
        repo_root_path: Path to repository root
        repo_name: Name of the repository
        json_output_path: Path to write the JSON map output file
        csv_output_path: Path to write the CSV report output file
        config_module: Configuration module with constants
        include_git_info: Whether to include Git commit information (assumes it's in file_info_list if True)
    """
    # Build the selective map structure and scan report entries
    # Pass include_git_info and repo_root_path down
    selective_map_data, scan_report_rows, total_embedded_bytes, csv_fields = _build_selective_map_structure(
        file_info_list, 
        config_module,
        include_git_info, # Pass include_git_info
        repo_root_path # Pass repo_root_path
    )
    
    # Create the final JSON map with repo name as the root key
    json_data = {repo_name: selective_map_data}
    
    # Write the JSON map to the output file
    try:
        with open(json_output_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2)
        print(f"Successfully generated JSON map: {json_output_path} ({json_output_path.stat().st_size / 1024:.2f} KB)")
    except Exception as e:
        print(f"Error writing JSON map: {e}", file=sys.stderr)

    # Write the CSV report
    try:
        if scan_report_rows:
            with open(csv_output_path, 'w', encoding='utf-8', newline='') as csvfile:
                # Use the determined fields based on git info inclusion
                writer = csv.DictWriter(csvfile, fieldnames=csv_fields)
                writer.writeheader()
                writer.writerows(scan_report_rows)
            print(f"Successfully generated CSV report: {csv_output_path} ({csv_output_path.stat().st_size / 1024:.2f} KB)")
        else:
            print("No files processed for CSV report.")
    except Exception as e:
        print(f"Error writing CSV report: {e}", file=sys.stderr)

    # Print summary
    print(f"Selective mapping complete. Total embedded content: {total_embedded_bytes / 1024:.2f} KB")
    print(f"Processed {len(file_info_list)} files, with detailed breakdown in {csv_output_path}")