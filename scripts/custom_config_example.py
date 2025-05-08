# Example custom configuration for repo-mapper
# Copy this file to src_mapper/custom_config.py and modify to customize behavior
# Then modify src_mapper/main_orchestrator.py to import from custom_config if it exists

"""
Customized configuration for the Repo Mapper toolkit.
"""

from pathlib import Path

# --- General Configuration ---
DEFAULT_OUTPUT_DIR_NAME: str = "output"  # Default name for the output subdirectory
ENCODINGS_TO_TRY: list[str] = ["utf-8", "latin-1"]  # Order matters

# --- Directory and File Exclusion/Inclusion Rules (for Selective Mapper & general filtering) ---

# Add your project-specific directories to exclude
EXCLUDE_ENTIRELY_FOLDERS: list[str] = [
    # Default folders
    ".git", ".hg", ".svn",                             # Version control systems
    "node_modules", "bower_components",                # JS package managers
    "venv", "env", ".venv", "ENV", "virtualenv",       # Python virtual environments
    "__pycache__", "*.pyc", "*.pyo",                   # Python bytecode
    "dist", "build", "target", "out", "bin", "obj",    # Build artifacts
    
    # Project-specific folders to exclude
    "data",          # Large data files folder
    "logs",          # Log files
    "downloads",     # Downloaded content
    ".circleci",     # CI configuration
]

# Files whose content should ALWAYS be attempted to be included
ALWAYS_INCLUDE_CONTENT_PATTERNS: list[str] = [
    # Default important files
    "README.md", "README.rst", "README.txt", "README", "CONTRIBUTING.md", "LICENSE",
    "Dockerfile", "docker-compose.yml", "docker-compose.yaml",
    "requirements.txt", "pyproject.toml", "setup.py",
    
    # Project-specific important files
    "main.py",       # Main entry point
    "app.py",        # Application entry point
    "settings.py",   # Django settings
    "urls.py",       # Django URLs
    "models.py",     # Django/SQLAlchemy models
    "schema.graphql", # GraphQL schema
    "schema.sql",    # SQL schema
]

# Folders where content of files should be prioritized
INCLUDE_CONTENT_IN_FOLDERS_PATTERNS: list[str] = [
    # Default important folders
    "src/", "app/", "lib/", "core/",
    
    # Project-specific important folders
    "api/",          # API definitions
    "templates/",    # Template files
    "migrations/",   # Database migrations
    "config/",       # Configuration files
]

# File extensions to exclude from content
EXCLUDE_CONTENT_FILE_EXTENSIONS: list[str] = [
    ".log", ".tmp", ".swp", ".bak", ".map",
    ".min.js", ".min.css",
    ".csv", ".tsv", ".parquet",
]

# --- Thresholds for Selective Content Generation ---
LARGE_FILE_THRESHOLD_LINES: int = 500     # Files over this LOC are "large"
TRUNCATE_LINES_DEFAULT: int = 150         # Default truncation for "uncertain" files
TRUNCATE_LINES_FOR_INCLUDED: int = 300    # Truncation for high-priority files
MAX_TOTAL_EMBEDDED_CONTENT_KB: int = 2048 # 2MB budget (doubled from default)

# --- Git Utility Configuration (if git_utils is used) ---
GIT_COMMAND_TIMEOUT_SECONDS: int = 10  # Timeout for git commands