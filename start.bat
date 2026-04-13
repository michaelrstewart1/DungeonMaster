@echo off
title AI Dungeon Master — Starting Up
color 0A

echo.
echo  ██████████████████████████████████████
echo  ██   AI DUNGEON MASTER  — STARTUP   ██
echo  ██████████████████████████████████████
echo.

set ROOT=%~dp0
set BACKEND=%ROOT%backend
set FRONTEND=%ROOT%frontend

REM ─────────────────────────────────────────
REM  1. Backend Python deps
REM ─────────────────────────────────────────
echo [1/4] Checking Python dependencies...
cd /d "%BACKEND%"

if not exist ".venv\Scripts\python.exe" (
    echo       Creating virtual environment...
    python -m venv .venv
)

call .venv\Scripts\activate.bat

REM Check if fastapi is already installed
python -c "import fastapi" 2>nul
if errorlevel 1 (
    echo       Installing backend packages (first time — takes ~1 min)...
    pip install -e ".[dev]" --quiet
    echo       Backend packages installed!
) else (
    echo       Backend packages OK
)

REM ─────────────────────────────────────────
REM  2. Frontend npm deps
REM ─────────────────────────────────────────
echo.
echo [2/4] Checking frontend dependencies...
cd /d "%FRONTEND%"

if not exist "node_modules" (
    echo       Installing npm packages (first time — takes ~30 sec)...
    npm install --silent
    echo       Frontend packages installed!
) else (
    echo       Frontend packages OK
)

REM ─────────────────────────────────────────
REM  3. Start backend
REM ─────────────────────────────────────────
echo.
echo [3/4] Starting backend on http://localhost:8000 ...
cd /d "%BACKEND%"
start "AI DM Backend" cmd /k "call .venv\Scripts\activate.bat && python -m uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000 --reload"

REM Give backend 3 seconds to boot
timeout /t 3 /nobreak >nul

REM ─────────────────────────────────────────
REM  4. Start frontend
REM ─────────────────────────────────────────
echo [4/4] Starting frontend on http://localhost:5173 ...
cd /d "%FRONTEND%"
start "AI DM Frontend" cmd /k "npm run dev"

REM Give frontend 4 seconds to compile
timeout /t 4 /nobreak >nul

REM ─────────────────────────────────────────
REM  5. Open browser
REM ─────────────────────────────────────────
echo.
echo  ============================================================
echo   Both servers are running!
echo.
echo   Open your browser to:  http://localhost:5173
echo.
echo   How to play:
echo    1. Click "New Campaign" and give your adventure a name
echo    2. Click into the campaign
echo    3. Click "Create Custom" to build YOUR character
echo       (choose Race → Class → Ability Scores → Name)
echo    4. Or click "Choose a Hero" for a ready-made character
echo    5. Click "Begin Adventure" when your party is ready
echo.
echo   Close the two server windows to stop everything.
echo  ============================================================
echo.

start "" "http://localhost:5173"

pause
