#!/bin/bash
# run_mapper.sh
# A helper script that handles the python vs python3 command issue

# Get the repo-mapper directory
REPO_MAPPER_DIR=$(cd "$(dirname "$0")/.." && pwd)

# Check which Python command is available
PYTHON_CMD=""
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "Error: Neither 'python3' nor 'python' commands were found."
    echo "Please install Python 3 before running this script."
    exit 1
fi

# Get arguments or use defaults
TARGET_PATH=${1:-..}
shift
OPTIONS=${@:-"--selective --text-tree"}

# Run the main_orchestrator.py script with the determined Python command
echo "Using Python command: $PYTHON_CMD"
echo "Running: $PYTHON_CMD src_mapper/main_orchestrator.py $TARGET_PATH $OPTIONS"
echo "==============================================================="

cd "$REPO_MAPPER_DIR"
$PYTHON_CMD src_mapper/main_orchestrator.py "$TARGET_PATH" $OPTIONS

# Exit with the same code that Python returned
exit $?