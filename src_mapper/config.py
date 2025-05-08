# src_mapper/config.py

"""
Centralized configuration for the Repo Mapper toolkit.
Modify these values to tune the behavior of the mappers.
"""

from pathlib import Path

# --- General Configuration ---
DEFAULT_OUTPUT_DIR_NAME: str = "output" # Default name for the output subdirectory
ENCODINGS_TO_TRY: list[str] = ["utf-8", "latin-1"] # Order matters

# --- Directory and File Exclusion/Inclusion Rules (for Selective Mapper & general filtering) ---

# Folders to exclude entirely from scanning (structure and content)
# These are checked against directory names.
EXCLUDE_ENTIRELY_FOLDERS: list[str] = [
    ".git", ".hg", ".svn",                             # Version control systems
    "node_modules", "bower_components",                # JS package managers
    "venv", "env", ".venv", "ENV", "virtualenv",       # Python virtual environments
    "__pycache__", "*.pyc", "*.pyo",                   # Python bytecode
    "dist", "build", "target", "out", "bin", "obj",    # Build artifacts
    "coverage", ".coverage", "htmlcov",                # Coverage reports
    ".pytest_cache", ".mypy_cache", ".tox", ".nox",    # Testing/tooling caches
    "docs/_build", "site",                             # Generated documentation
    "site-packages", "jspm_packages", "web_modules",   # Other package managers
    "vendor", "third_party",                           # Vendored dependencies
    "tmp", "temp", "logs",                             # Temporary files and logs
    ".DS_Store", "Thumbs.db",                         # OS-specific metadata
    ".idea", ".vscode", ".project", ".settings",       # IDE/editor specific
    "*.egg-info", "*.dist-info",                       # Python packaging metadata
]

# Files whose content should ALWAYS be attempted to be included in selective_map.json (if text)
# Uses fnmatch patterns against filenames.
ALWAYS_INCLUDE_CONTENT_PATTERNS: list[str] = [
    "README.md", "README.rst", "README.txt", "README", "CONTRIBUTING.md", "LICENSE", "LICENSE.txt",
    "Dockerfile", "docker-compose.yml", "docker-compose.yaml", "Vagrantfile",
    "requirements.txt", "Pipfile", "poetry.lock", "Pipfile.lock", # poetry.lock can be large
    "package.json", "yarn.lock", "pnpm-lock.yaml", "package-lock.json", # JS deps (lock files can be large)
    "pyproject.toml", "setup.py", "setup.cfg", "MANIFEST.in",
    "Makefile", "makefile", "GNUmakefile", "build.gradle", "pom.xml", "CMakeLists.txt",
    "main.py", "app.py", "index.js", "server.js", "manage.py", # Common entry points
    "settings.py", "config.py", "settings.json", "config.json", "settings.yaml", "config.yaml",
    ".env.sample", ".env.example", ".flaskenv",
    "*.conf", "*.ini", "*.cfg", "*.toml", "*.yaml", "*.yml", "*.json", # Common config extensions
    "*.sh", "*.bash", "*.ps1", # Common script files
    ".babelrc", ".eslintrc.*", ".prettierrc.*", ".stylelintrc.*", # Linters & formatters
    ".editorconfig",
    "Procfile",
    "go.mod", "go.sum", # Go modules
    "Cargo.toml", "Cargo.lock", # Rust cargo
    "*.tf", "*.tfvars", # Terraform
    "*.sql", # SQL schema or important queries
    "*.graphql", "*.gql", # GraphQL schemas
    "*.proto", # Protocol Buffers
]

# Folders where content of files within should generally be prioritized for selective_map.json
# Uses startswith check on relative paths (e.g., "src/", "app/"). Ensure trailing slash.
INCLUDE_CONTENT_IN_FOLDERS_PATTERNS: list[str] = [
    "src/", "app/", "lib/", "cmd/", "pkg/", "core/", "internal/", "cmd/", "bin/",
    "config/", "settings/", "conf/", "scripts/", "examples/", "samples/",
    "terraform/", "ansible/", "kubernetes/", "k8s/", "helm/",
    "migrations/", "db/migrations/",
    "workflows/", ".github/workflows/", ".gitlab-ci.yml",
    "tests/fixtures/", # Fixtures can be insightful
    "api/", "schemas/", "models/", "controllers/", "handlers/", "services/", "utils/",
]

# File extensions whose content is generally NOT useful for AI understanding or is too verbose
# These files will still be listed in the structure, but their content omitted in selective_map.json.
EXCLUDE_CONTENT_FILE_EXTENSIONS: list[str] = [
    ".log", ".tmp", ".swp", ".bak", ".map", ".lock", ".sum", # .lock for generic, .sum for go.sum (already in always_include)
    ".min.js", ".min.css", # Minified assets
    ".prof", ".profraw", ".pstats", # Profiling data
    ".csv", ".tsv", ".parquet", ".feather", ".hdf5", # Large data files (unless small and in examples/)
    ".tfstate", ".tfstate.backup", # Terraform state
]

# File extensions considered binary or not useful to embed as text in any map
# These files will be listed, but content always marked as [Binary File] or similar.
BINARY_FILE_EXTENSIONS: list[str] = [
    # Images
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".webp", ".bmp", ".tiff", ".tif",
    ".svg", # Can be text, but often complex/large for raw embedding
    # Documents
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".odt", ".ods", ".odp",
    # Archives
    ".zip", ".tar", ".gz", ".bz2", ".rar", ".7z", ".tgz", ".xz",
    # Executables & Libraries
    ".exe", ".dll", ".so", ".o", ".a", ".lib", ".dylib", ".bundle",
    # Compiled Code / Packages
    ".class", ".jar", ".war", ".ear", ".pyc", ".pyo", ".pyd", ".whl", ".gem", ".phar",
    # Media
    ".mp4", ".mov", ".avi", ".mkv", ".webm", ".flv", ".wmv",
    ".mp3", ".wav", ".ogg", ".flac", ".aac", ".m4a",
    # Fonts
    ".woff", ".woff2", ".ttf", ".otf", ".eot",
    # ML Models & Data
    ".ipynb", # Jupyter notebooks: JSON, but often large with outputs
    ".pth", ".pt", ".h5", ".onnx", ".pb", ".tflite", ".ckpt", ".safetensors",
    # Databases & Data
    ".sqlite", ".sqlite3", ".db", ".mdb", ".dat", ".idx",
    # Design & 3D
    ".psd", ".ai", ".fig", ".sketch", ".blend", ".fbx", ".obj", ".stl",
    # Other
    ".key", ".pem", ".p12", ".pfx", # Certificates/Keys (sensitive, treat as binary)
    ".iso", ".img", ".vmdk", ".ova", # Disk images
    ".swf", # Flash
]

# --- Thresholds for Selective Content Generation ---
LARGE_FILE_THRESHOLD_LINES: int = 500     # Files over this LOC are "large"
TRUNCATE_LINES_DEFAULT: int = 150         # Default truncation for "uncertain" files
TRUNCATE_LINES_FOR_INCLUDED: int = 300    # Truncation for high-priority files if they exceed LARGE_FILE_THRESHOLD_LINES
MAX_TOTAL_EMBEDDED_CONTENT_KB: int = 1024 # 1MB budget for all embedded content in selective_map.json

# --- Git Utility Configuration (if git_utils is used) ---
GIT_COMMAND_TIMEOUT_SECONDS: int = 10 # Timeout for git commands