#!/bin/bash
# map_repo.sh
# A simple script to run the repo-mapper tool on the parent directory of repo-mapper 
# (i.e., your project repository)

# Get the repo-mapper directory
REPO_MAPPER_DIR=$(cd "$(dirname "$0")/.." && pwd)

# Check if virtual environment exists, create if it doesn't
if [ ! -d "$REPO_MAPPER_DIR/venv_mapper" ]; then
    echo "Creating virtual environment..."
    cd "$REPO_MAPPER_DIR"
    python3 -m venv venv_mapper
fi

# Activate virtual environment
echo "Activating virtual environment..."
source "$REPO_MAPPER_DIR/venv_mapper/bin/activate"

# Run the mapper on the parent directory with all outputs
echo "Running repo-mapper on parent directory..."
cd "$REPO_MAPPER_DIR"
python3 src_mapper/main_orchestrator.py .. --all

# Generate output path
OUTPUT_DIR="$REPO_MAPPER_DIR/output"

# Display the output files
echo ""
echo "Generated output files:"
echo "----------------------"
ls -la "$OUTPUT_DIR"

# Determine parent directory name
PARENT_DIR=$(basename $(dirname "$REPO_MAPPER_DIR"))

# Instructions for viewing the outputs
echo ""
echo "To view the HTML map, open this file in your browser:"
echo "  $OUTPUT_DIR/$PARENT_DIR-mapper.html"
echo ""
echo "To view the repository structure:"
echo "  $OUTPUT_DIR/$PARENT_DIR-structure.txt"
echo ""
echo "To see which files were included in the selective map and why:"
echo "  $OUTPUT_DIR/$PARENT_DIR-scan_report.csv"
echo ""

# Deactivate virtual environment
deactivate