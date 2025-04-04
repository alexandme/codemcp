#!/bin/bash
set -e

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Format code using Black
echo "Running Black formatter..."
# Use Black executable directly if available
if [ -f "${SCRIPT_DIR}/.venv/bin/black" ]; then
    "${SCRIPT_DIR}/.venv/bin/black" .
else
    # Fall back to using Python module
    echo "Using Python module for Black..."
    "${SCRIPT_DIR}/.venv/bin/python" -m black .
fi

# Format code using Ruff
echo "Running Ruff formatter..."
# Use Python from the script directory's virtual environment
"${SCRIPT_DIR}/.venv/bin/python" -m ruff format .

echo "Format completed successfully!"
