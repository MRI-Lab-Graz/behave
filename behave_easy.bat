@echo off
REM BEHAVE Easy Launcher - For Students (Windows)
REM This script automatically handles virtual environment setup and activation

echo 🎓 BEHAVE Easy Launcher - Starting...

REM Get the directory where this script is located
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

REM Check if virtual environment exists
if not exist ".behave" if not exist "venv" if not exist ".venv" (
    echo 🔧 No virtual environment found. Setting up automatically...
    
    REM Try to use uv first (fastest)
    where uv >nul 2>nul
    if %errorlevel% == 0 (
        echo 🚀 Using uv for fast setup...
        call uv_setup.bat
    ) else (
        echo 📦 Using standard Python venv...
        python -m venv .venv
        
        REM Activate environment
        if exist ".venv\Scripts\activate.bat" (
            call .venv\Scripts\activate.bat
        ) else (
            echo ❌ Failed to create virtual environment
            exit /b 1
        )
        
        REM Install dependencies
        echo 📦 Installing dependencies...
        pip install -r requirements.txt
    )
    
    echo ✅ Virtual environment setup complete!
)

REM Now run the main script - it will handle environment detection automatically
echo 🚀 Starting BEHAVE conversion...
python behave.py %*
