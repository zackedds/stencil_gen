#!/bin/bash
# Setup script for the stencil generator backend

echo "Setting up backend environment..."

# Check if venv exists, if so remove it
if [ -d "venv" ]; then
    echo "Removing existing venv..."
    rm -rf venv
fi

# Create new venv with Python 3.11 (better wheel support)
echo "Creating virtual environment with Python 3.11..."
if command -v python3.11 &> /dev/null; then
    python3.11 -m venv venv
elif command -v python3.12 &> /dev/null; then
    echo "Python 3.11 not found, using Python 3.12..."
    python3.12 -m venv venv
else
    echo "Python 3.11 or 3.12 not found, using default python3..."
    python3 -m venv venv
fi

# Activate venv
source venv/bin/activate

# Set environment variables for GEOS
export GEOS_CONFIG=/opt/homebrew/bin/geos-config
export CPPFLAGS="-I/opt/homebrew/include"
export LDFLAGS="-L/opt/homebrew/lib"

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "Setup complete! To activate the environment, run:"
echo "  source venv/bin/activate"
echo ""
echo "Then start the server with:"
echo "  python main.py"

