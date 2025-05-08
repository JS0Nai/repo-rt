# src_mapper/utils/__init__.py

from .file_utils import (
    read_file_content,
    count_lines,
    get_file_timestamps,
    get_file_extension,
    truncate_content_by_lines
)
from .ignore_utils import (
    load_gitignore_patterns,
    should_ignore_by_gitignore,
    is_excluded_entirely
)
# from .git_utils import is_git_repository, get_last_commit_info # Uncomment when implemented

__all__ = [
    "read_file_content",
    "count_lines",
    "get_file_timestamps",
    "get_file_extension",
    "truncate_content_by_lines",
    "load_gitignore_patterns",
    "should_ignore_by_gitignore",
    "is_excluded_entirely",
    # "is_git_repository", # Uncomment when implemented
    # "get_last_commit_info", # Uncomment when implemented
]