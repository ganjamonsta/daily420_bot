@echo off
setlocal

REM Переходим в папку проекта (где лежит этот bat)
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo [INFO] Venv not found. Creating .venv...
  py -3 -m venv .venv
  if errorlevel 1 (
    echo [ERROR] Failed to create virtual environment.
    pause
    exit /b 1
  )
)

echo [INFO] Activating virtual environment...
call ".venv\Scripts\activate.bat"
if errorlevel 1 (
  echo [ERROR] Failed to activate venv.
  pause
  exit /b 1
)

echo [INFO] Installing/updating dependencies...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 (
  echo [ERROR] Dependency installation failed.
  pause
  exit /b 1
)

if not exist ".env" (
  echo [WARN] .env file not found.
  echo [WARN] Copy .env.example to .env and set BOT_TOKEN.
  pause
  exit /b 1
)

echo [INFO] Starting bot...
python bot.py

set EXIT_CODE=%ERRORLEVEL%
echo.
echo [INFO] Bot exited with code %EXIT_CODE%.
pause
exit /b %EXIT_CODE%
