@echo off
:: UV-based setup script (Windows)

:: Check for uv
where uv >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ uv is not installed. Please install it from https://github.com/astral-sh/uv
    exit /b 1
)

:: Remove old virtual environment if it exists
if exist .behave (
    echo 🔁 Removing existing virtual environment...
    rmdir /s /q .behave
)

:: Create new virtual environment
echo 🚀 Creating virtual environment using uv...
uv venv .behave

:: Install dependencies using pip in the venv
echo 📦 Installing dependencies from requirements.txt...
.behave\Scripts\python.exe -m pip install -r requirements.txt

:: Optional: Show Python executable to confirm venv context
echo 🐍 Using Python from:
.behave\Scripts\python.exe -c "import sys; print(sys.executable)"

:: Check for deno
where deno >nul 2>nul
if %errorlevel% neq 0 (
    echo ⚠️  Deno is not installed. BIDS validation will not work.
    echo 👉 Install it from https://deno.land/#installation
)

echo ✅ Setup complete!
echo 🔧 To activate the environment, run: call .behave\Scripts\activate
