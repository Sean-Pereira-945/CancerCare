@echo off
title CancerCare AI Control Panel
echo ==========================================
echo       CANCERCARE AI STARTUP SCRIPT
echo ==========================================
echo.

:: 1. Check for .env
if not exist ".env" (
    echo [ERROR] .env file not found! 
    echo Please create the .env file in the root directory.
    pause
    exit /b
)

:: 2. Start Frontend in a new window
echo [PROGRESS] Starting Frontend (Vite)...
start cmd /k "cd frontend && npm run dev"

:: 3. Setup Backend Virtual Environment
echo [PROGRESS] Checking Backend Environment...
if not exist "backend\venv" (
    echo [INFO] Creating virtual environment...
    python -m venv backend\venv
    call backend\venv\Scripts\activate
    pip install -r backend\requirements.txt
)

:: 4. Start Backend in a new window
echo [PROGRESS] Starting Backend (FastAPI)...
start cmd /k "cd backend && venv\Scripts\activate && uvicorn app.main:app --reload --port 8000 --env-file ..\.env"

echo.
echo ==========================================
echo    CANCERCARE IS NOW RUNNING!
echo.
echo    Frontend: http://localhost:5173
echo    Backend:  http://localhost:8000/docs
echo ==========================================
echo.
pause
