@echo off
setlocal enabledelayedexpansion

title CancerCare AI Control Panel
cd /d "%~dp0"

set "ROOT_DIR=%cd%"
set "FRONTEND_DIR=%ROOT_DIR%\frontend"
set "BACKEND_DIR=%ROOT_DIR%\backend"
set "VENV_DIR=%ROOT_DIR%\.venv"
set "VENV_PY=%VENV_DIR%\Scripts\python.exe"
set "BACKEND_LOG=%BACKEND_DIR%\run_output.txt"

echo ==========================================
echo       CANCERCARE AI STARTUP SCRIPT
echo ==========================================
echo.

if not exist "%ROOT_DIR%\.env" (
    echo [ERROR] .env file not found in the project root.
    echo Please create "%ROOT_DIR%\.env" before running the launcher.
    pause
    exit /b 1
)

call :find_python
if not defined PYTHON_EXE (
    echo [ERROR] Could not find a usable Python installation.
    echo Install Python 3.11+ and make sure it is accessible from this machine.
    pause
    exit /b 1
)

echo [INFO] Using Python: %PYTHON_EXE%
echo.

echo [PROGRESS] Checking frontend dependencies...
if not exist "%FRONTEND_DIR%\node_modules\" (
    echo [INFO] Frontend dependencies not found. Installing...
    pushd "%FRONTEND_DIR%"
    call npm install
    set "NPM_EXIT=!ERRORLEVEL!"
    popd
    if not "!NPM_EXIT!"=="0" (
        echo [ERROR] Failed to install frontend dependencies.
        pause
        exit /b 1
    )
)

echo [PROGRESS] Starting frontend (Vite)...
start "CancerCare Frontend" /D "%FRONTEND_DIR%" cmd /k "npm run dev"

echo [PROGRESS] Validating backend virtual environment...
set "REBUILD_VENV=0"

if not exist "%VENV_PY%" (
    set "REBUILD_VENV=1"
)

if "!REBUILD_VENV!"=="0" (
    "%VENV_PY%" -c "import sys" >nul 2>&1
    if errorlevel 1 (
        echo [WARN] Existing virtual environment is unusable. Rebuilding...
        set "REBUILD_VENV=1"
    )
)

if "!REBUILD_VENV!"=="1" (
    if exist "%VENV_DIR%" (
        rmdir /s /q "%VENV_DIR%"
    )
    echo [INFO] Creating backend virtual environment...
    "%PYTHON_EXE%" -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo [ERROR] Failed to create the backend virtual environment.
        pause
        exit /b 1
    )
)

echo [PROGRESS] Checking backend dependencies...
"%VENV_PY%" -c "import fastapi, uvicorn, sqlalchemy" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing backend dependencies...
    "%VENV_PY%" -m pip install --upgrade pip
    if errorlevel 1 (
        echo [ERROR] Failed to upgrade pip in the backend virtual environment.
        pause
        exit /b 1
    )

    "%VENV_PY%" -m pip install -r "%BACKEND_DIR%\requirements.txt"
    if errorlevel 1 (
        echo [ERROR] Failed to install backend dependencies.
        pause
        exit /b 1
    )
)

if exist "%BACKEND_LOG%" del /f /q "%BACKEND_LOG%" >nul 2>&1

echo [PROGRESS] Starting backend (FastAPI)...
start "CancerCare Backend" /D "%BACKEND_DIR%" cmd /c ""%VENV_PY%" -m uvicorn app.main:app --reload --port 8000 --env-file ..\.env > "%BACKEND_LOG%" 2>&1"

echo [PROGRESS] Waiting for backend health check...
set "BACKEND_READY=0"
for /l %%I in (1,1,25) do (
    powershell -NoProfile -Command "try { $r = Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/health -TimeoutSec 2; if ($r.StatusCode -ge 200) { exit 0 } else { exit 1 } } catch { exit 1 }" >nul 2>&1
    if not errorlevel 1 (
        set "BACKEND_READY=1"
        goto :backend_ready
    )
    timeout /t 1 /nobreak >nul
)

:backend_ready
if "!BACKEND_READY!"=="0" (
    echo [ERROR] Backend did not start successfully on http://127.0.0.1:8000
    echo [INFO] Backend log:
    echo ------------------------------------------
    if exist "%BACKEND_LOG%" (
        type "%BACKEND_LOG%"
    ) else (
        echo No backend log was generated.
    )
    echo ------------------------------------------
    echo [HINT] This is the reason the login screen shows ERR_CONNECTION_REFUSED.
    pause
    exit /b 1
)

echo.
echo ==========================================
echo    CANCERCARE IS NOW RUNNING!
echo.
echo    Frontend: http://localhost:5173
echo    Backend:  http://localhost:8000/docs
echo ==========================================
echo.
echo Close the frontend window to stop Vite.
echo Backend logs are written to "%BACKEND_LOG%".
echo.
pause
exit /b 0

:find_python
set "PYTHON_EXE="

where py >nul 2>&1
if not errorlevel 1 (
    py -3 -c "import sys" >nul 2>&1
    if not errorlevel 1 (
        for /f "usebackq delims=" %%P in (`py -3 -c "import sys; print(sys.executable)"`) do (
            set "PYTHON_EXE=%%P"
        )
        goto :eof
    )
)

where python >nul 2>&1
if not errorlevel 1 (
    python -c "import sys" >nul 2>&1
    if not errorlevel 1 (
        for /f "usebackq delims=" %%P in (`python -c "import sys; print(sys.executable)"`) do (
            set "PYTHON_EXE=%%P"
        )
        goto :eof
    )
)

for %%V in (313 312 311 310) do (
    if exist "%LocalAppData%\Programs\Python\Python%%V\python.exe" (
        set "PYTHON_EXE=%LocalAppData%\Programs\Python\Python%%V\python.exe"
        goto :eof
    )
)

goto :eof
