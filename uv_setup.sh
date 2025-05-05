#!/bin/bash

# UV-based setup script (macOS/Linux)

# Check for uv
if ! command -v uv &> /dev/null; then
    echo "❌ uv is not installed. Please install it from https://github.com/astral-sh/uv"
    exit 1
fi

echo "🚀 Creating virtual environment using uv..."
uv venv .venv

# Activate the virtual environment
source .venv/bin/activate

# Install packages
echo "📦 Installing dependencies from requirements.txt..."
uv pip install -r requirements.txt

# Check for deno
if ! command -v deno &> /dev/null; then
    echo "⚠️  Deno is not installed. BIDS validation will not work without it."
    echo "👉 Install Deno from https://deno.land/#installation"
fi

echo "✅ Setup complete!"
echo "🔧 Activate your environment later with: source .venv/bin/activate"
