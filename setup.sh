#!/bin/bash
# Setup script for MACAD-Thesis-MEP-Graph project

echo "Setting up MACAD-Thesis-MEP-Graph project..."

# Check if Python 3.12 is installed
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows - use py launcher
    if ! py -3.12 --version &> /dev/null; then
        echo "Error: Python 3.12 is not installed or not available"
        echo "Please install Python 3.12 from https://www.python.org/downloads/"
        exit 1
    fi
    PYTHON_CMD="py -3.12"
else
    # macOS/Linux - check for python3.12
    if command -v python3.12 &> /dev/null; then
        PYTHON_CMD="python3.12"
    elif command -v python3 &> /dev/null && python3 --version | grep -q "3\.12"; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null && python --version | grep -q "3\.12"; then
        PYTHON_CMD="python"
    else
        echo "Error: Python 3.12 is not installed or not available"
        echo "Please install Python 3.12 from https://www.python.org/downloads/"
        exit 1
    fi
fi

# Create virtual environment with Python 3.12
echo "Creating virtual environment with Python 3.12..."
$PYTHON_CMD -m venv venv

# Activate virtual environment based on OS
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows
    source venv/Scripts/activate
else
    # macOS/Linux
    source venv/bin/activate
fi

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt
plotly_get_chrome

echo "Setup complete!"
echo ""
echo "To activate the virtual environment:"
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    echo "  source venv/Scripts/activate    # Git Bash"
    echo "  .\\venv\\Scripts\\Activate.ps1   # PowerShell"
    echo "  venv\\Scripts\\activate.bat      # Command Prompt"
else
    echo "  source venv/bin/activate"
fi
echo ""
echo "To run the graph viewer:"
echo "  panel serve graph_viewer.py --show"
