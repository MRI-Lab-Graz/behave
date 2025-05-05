@echo off

:: UV-based setup script (Windows)

where uv >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ uv is not installed. Please install it from https://github.com/astral-sh/uv
    exit /b 1
)

echo 🚀 Creating virtual environment using uv...
uv venv .venv

echo 📦 Installing dependencies...
call .venv\Scripts\activate
uv pip install -r requirements.txt

:: Check for deno
where deno >nul 2>nul
if %errorlevel% neq 0 (
    echo ⚠️  Deno is not installed. BIDS validation will not work.
    echo 👉 Install it from https://deno.land/#installation
)

echo ✅ Setup complete!
echo 🔧 Activate with: call .venv\Scripts\activate
