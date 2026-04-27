@echo off
setlocal enabledelayedexpansion

title CancerCare AI Control Panel
echo ==========================================
echo       CANCERCARE AI STARTUP SCRIPT
echo ==========================================
echo.

:: Ensure we are in the directory of the script
cd /d "%~dp0"

:: 1. Check for .env
if not exist ".env" (
    echo [ERROR] .env file not found! 
    echo Please create the .env file in the root directory before running.
    pause
    exit /b 1
)

:: 2. Check for Frontend dependencies
echo [PROGRESS] Checking Frontend Dependencies...
if not exist "frontend\node_modules\" (
    echo [INFO] node_modules not found in frontend. Installing...
    pushd frontend
    call npm install
    popd
    if errorlevel 1 (
        echo [ERROR] Failed to install frontend dependencies.
        pause
        exit /b 1
    )
)

:: 3. Start Frontend in a new window
echo [PROGRESS] Starting Frontend (Vite)...
start "CancerCare Frontend" /D "%~dp0frontend" cmd /k "npm run dev"

:: 4. Setup Backend Virtual Environment
echo [PROGRESS] Checking Backend Environment...
if not exist ".venv\" (
    echo [INFO] Virtual environment not found. Creating...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create Python virtual environment. Please ensure Python is installed and added to PATH.
        pause
        exit /b 1
    )
    
    echo [INFO] Upgrading pip and installing backend dependencies...
    ".venv\Scripts\python.exe" -m pip install --upgrade pip
    ".venv\Scripts\python.exe" -m pip install -r backend\requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install backend dependencies.
        pause
        exit /b 1
    )
)

:: 5. Start Backend in a new window
echo [PROGRESS] Starting Backend (FastAPI)...
start "CancerCare Backend" /D "%~dp0backend" cmd /k "..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000 --env-file ..\.env"

echo.
echo ==========================================
echo    CANCERCARE IS NOW RUNNING!
echo.
echo    Frontend: http://localhost:5173
echo    Backend:  http://localhost:8000/docs
echo ==========================================
echo.
echo Close the newly opened terminal windows to stop the project.
echo.
pause
