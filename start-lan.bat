@echo off
REM AI Dungeon Master — LAN Server Launcher
REM Binds to 0.0.0.0 so all devices on the home network can connect.
REM Players open  http://<this-PC-IP>:8000  in their browser.

echo ============================================================
echo  AI Dungeon Master — LAN Mode
echo ============================================================
echo.

REM Find local IP so you can tell players what address to use
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4 Address"') do (
    set LOCAL_IP=%%a
    goto :found_ip
)
:found_ip
set LOCAL_IP=%LOCAL_IP: =%
echo  Your LAN address: http://%LOCAL_IP%:8000
echo  Share this with players on the same WiFi.
echo.
echo  Press Ctrl+C to stop the server.
echo ============================================================
echo.

cd /d "%~dp0backend"

REM Activate virtual environment if present
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
) else if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

REM Start FastAPI bound to all interfaces for LAN access
python -m uvicorn app.main:create_app --factory --host 0.0.0.0 --port 8000 --reload

pause
