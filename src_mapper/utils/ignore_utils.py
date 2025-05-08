# src_mapper/utils/ignore_utils.py

import fnmatch
import sys
from pathlib import Path
from typing import List

# Import from config to avoid circular dependency if config needs utils
# from .. import config as cfg # This would be if config.py was in src_mapper/

def load_gitignore_patterns(repo_root_path: Path) -> List[str]:
    """Loads and cleans patterns from .gitignore file in the repo root."""
    patterns: List[str] = []
    gitignore_file = repo_root_path / '.gitignore'
    if gitignore_file.is_file():
        try:
            with open(gitignore_file, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    stripped_line = line.strip()
                    # Ignore comments and empty lines
                    if stripped_line and not stripped_line.startswith('#'):
                        patterns.append(stripped_line)
        except Exception as e:
            print(f"Warning: Could not read .gitignore from {gitignore_file}: {e}", file=sys.stderr)
    return patterns

def _is_path_match(path_str: str, pattern: str) -> bool:
    """
    Enhanced fnmatch considering directory patterns.
    path_str should be a POSIX-style path string.
    """
    if pattern.endswith('/'):
        # 'build/' should match 'build' or 'build/foo.txt'
        # To match 'build' itself, we check if path_str is pattern.rstrip('/')
        # To match 'build/foo.txt', we check if path_str starts with pattern
        return path_str == pattern.rstrip('/') or path_str.startswith(pattern)
    return fnmatch.fnmatch(path_str, pattern) or fnmatch.fnmatch(Path(path_str).name, pattern)


def should_ignore_by_gitignore(relative_path: Path, gitignore_patterns: List[str]) -> bool:
    """
    Checks if a relative path should be ignored based on .gitignore patterns.
    This is a simplified implementation and may not cover all .gitignore nuances.
    """
    path_str_posix = relative_path.as_posix() # Use POSIX separators for matching

    for pattern_str in gitignore_patterns:
        pattern = pattern_str
        # Handle negation (basic support)
        negate = False
        if pattern.startswith('!'):
            negate = True
            pattern = pattern[1:]

        # Handle patterns starting with / (anchored to root)
        if pattern.startswith('/'):
            if _is_path_match(path_str_posix, pattern.lstrip('/')):
                return not negate # Apply negation
            continue # Anchored patterns only match at root

        # Handle non-anchored patterns (can match anywhere)
        # Check against full path and individual path components
        if _is_path_match(path_str_posix, pattern):
            return not negate
        
        # Check if pattern matches any directory component in the path
        # e.g. pattern 'node_modules/' should ignore 'src/node_modules/file.js'
        if pattern.endswith('/'):
            dir_pattern_name = pattern.rstrip('/')
            if dir_pattern_name in relative_path.parts:
                # Further check: if 'node_modules/' is pattern, ensure 'node_modules' part is a directory
                # This is implicitly handled if the path component matches the dir_pattern_name
                return not negate
        
        # Check against just the filename/dirname if pattern has no slashes
        if '/' not in pattern and fnmatch.fnmatch(relative_path.name, pattern):
            return not negate
            
    return False


def is_excluded_entirely(relative_path: Path, config_exclude_folders: List[str], gitignore_patterns: List[str]) -> bool:
    """
    Checks if a directory path matches EXCLUDE_ENTIRELY_FOLDERS from config.py
    or a gitignore pattern that implies full directory exclusion.
    Assumes relative_path is a directory.
    """
    if not relative_path.name: # Should not happen for valid relative paths
        return False

    # Check against config_exclude_folders (these are usually simple names)
    if relative_path.name in config_exclude_folders:
        return True
    if str(relative_path) in config_exclude_folders: # For paths like "docs/_build"
        return True

    # Check against gitignore patterns that are directory-specific
    # A pattern like "build/" or "node_modules/" from .gitignore should exclude the directory
    path_str_posix = relative_path.as_posix()
    for pattern_str in gitignore_patterns:
        pattern = pattern_str
        negate = False
        if pattern.startswith('!'):
            negate = True
            pattern = pattern[1:]

        if pattern.endswith('/'):
            # If pattern is 'build/', it should match the directory 'build'
            if path_str_posix == pattern.rstrip('/'):
                return not negate
            # If pattern is 'some/path/build/', it should match 'some/path/build'
            if path_str_posix == pattern.rstrip('/'):
                 return not negate
            # If pattern is 'node_modules/', and relative_path is 'src/node_modules', it should match
            if pattern.rstrip('/') in relative_path.parts:
                 # This is a bit broad, but often intended for .gitignore
                 # A more precise check would ensure the pattern matches the full path segment
                 # For example, if pattern is 'foo/', path 'a/foo/b' should be ignored.
                 # If path is 'a/bfoo/c', it should not.
                 # The current check `pattern.rstrip('/') in relative_path.parts` is simple.
                 return not negate


    return False