# Scripts Directory

This directory contains utility scripts for the repo-mapper project.

## Available Scripts

### run_mapper.sh

A helper script that handles the `python` vs `python3` command difference issue. It automatically detects which Python command is available on your system and uses the appropriate one.

Usage:
```bash
# From the repo-mapper directory
./scripts/run_mapper.sh [target_path] [options]
```

Examples:
```bash
# Map the parent directory with default options (--selective --text-tree)
./scripts/run_mapper.sh

# Map a specific directory with custom options
./scripts/run_mapper.sh /path/to/repo --all --include-git-info

# Map the current directory with all output formats
./scripts/run_mapper.sh . --all
```

This script works around the "python: command not found" error that some users might encounter, especially on macOS where only `python3` may be available.

### map_repo.sh

A simple script to run the repo-mapper tool on the parent directory (i.e., your project repository).

Usage:
```bash
# From the repo-mapper directory
./scripts/map_repo.sh
```

The script will:
1. Create a virtual environment if it doesn't exist
2. Run the repo-mapper on the parent directory with all output formats
3. Display paths to the generated output files

### ai_analysis_example.py

A script that automatically formats repo-mapper outputs into LLM-ready instructions and sends them to an AI model for analysis. It uses the template from `LLM_Analysis_Prompt_Template.md` to construct a comprehensive prompt with all repository artifacts.

**Important Note**: This is a simulation only. The script formats the data and shows what would be sent to an AI model, but you need to customize the `send_to_ai_model` function with your preferred AI provider's API calls to get real analysis.

Usage:
```bash
# From the repo-mapper directory
./scripts/ai_analysis_example.py <repo_name> <target_repo_path> [options]
```

Arguments:
```
repo_name           Name of the repository (used in output filenames)
target_repo_path    Absolute path to the repository being analyzed
```

Options:
```
--output-dir DIR     Directory containing repo-mapper outputs (default: repo-mapper/output)
--analysis-file FILE File to save the analysis (default: repo-mapper/repo-rt.md)
--template-file FILE Path to a custom prompt template (default: repo-mapper/LLM_Analysis_Prompt_Template.md)
```

Example:
```bash
# Process outputs for a repository named "my-project" located at /path/to/my-project
./scripts/ai_analysis_example.py my-project /path/to/my-project
```

The script will:
1. Load all repository data from output files
2. Format the data using the LLM template
3. Prepare it for sending to an AI model
4. (In simulation mode) Display a preview of what would be sent
5. Generate a placeholder repo-rt.md file with instructions for completing the integration

### custom_config_example.py

A template for customizing repo-mapper's behavior. Copy this file to `src_mapper/custom_config.py` and modify it to adjust which files and directories are included, excluded, or prioritized during mapping.

### save_clipboard.sh

A utility script that saves your clipboard contents to a timestamped file. See [README_save_clipboard.md](README_save_clipboard.md) for detailed documentation.

Usage:
```bash
# From the repo-mapper directory
./scripts/save_clipboard.sh [extension] [output_directory]
```

Examples:
```bash
# Save clipboard as markdown in the default 'chatlog' directory
./scripts/save_clipboard.sh

# Save clipboard as text in a 'notes' directory
./scripts/save_clipboard.sh txt notes
```