#!/bin/bash

# BEHAVE Easy Launcher - For Students
# This script automatically handles virtual environment setup and activation

echo "🎓 BEHAVE Easy Launcher - Starting..."

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if virtual environment exists
if [ ! -d ".behave" ] && [ ! -d "venv" ] && [ ! -d ".venv" ]; then
    echo "🔧 No virtual environment found. Setting up automatically..."
    
    # Try to use uv first (fastest)
    if command -v uv &> /dev/null; then
        echo "🚀 Using uv for fast setup..."
        ./uv_setup.sh
    else
        echo "📦 Using standard Python venv..."
        python3 -m venv .venv
        
        # Activate environment
        if [ -f ".venv/bin/activate" ]; then
            source .venv/bin/activate
        else
            echo "❌ Failed to create virtual environment"
            exit 1
        fi
        
        # Install dependencies
        echo "📦 Installing dependencies..."
        pip install -r requirements.txt
    fi
    
    echo "✅ Virtual environment setup complete!"
fi

# Now run the main script - it will handle environment detection automatically
echo "🚀 Starting BEHAVE conversion..."
python3 behave.py "$@"
