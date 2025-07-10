#!/bin/bash
# Setup script for MACAD-Thesis-MEP-Graph project

echo "Setting up MACAD-Thesis-MEP-Graph project..."

# Check if Python is installed
if ! command -v python &> /dev/null; then
    echo "Error: Python is not installed or not in PATH"
    exit 1
fi

# Create virtual environment
echo "Creating virtual environment..."
python -m venv venv

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
