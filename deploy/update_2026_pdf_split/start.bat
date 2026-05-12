@echo off
chcp 65001 >nul
title TradeDoc - Python OCR Service
echo ============================================
echo   TradeDoc Python OCR Service
echo ============================================
echo.

set PYTHON_DIR=%~dp0tradedoc-python
set PYTHON_EXE=C:\Users\Administrator\AppData\Local\Programs\Python\Python314\python.exe

if not exist "%PYTHON_EXE%" (
    echo [ERROR] Python not found at:
    echo   %PYTHON_EXE%
    echo.
    echo Please install Python or update PYTHON_EXE path in this file.
    pause
    exit /b 1
)

if not exist "%PYTHON_DIR%\app\api\main.py" (
    echo [ERROR] Python app not found at:
    echo   %PYTHON_DIR%
    echo.
    echo Make sure to run start.bat from the project root.
    pause
    exit /b 1
)

echo [1/2] Cleaning up old process on port 8100...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8100.*LISTENING"') do taskkill /F /PID %%a >nul 2>&1
timeout /t 1 /nobreak >nul

echo [2/2] Starting Python OCR service on http://127.0.0.1:8100 ...
echo.
echo Keep this window open. Press Ctrl+C or close it to stop.
echo.
cd /d "%PYTHON_DIR%"
"%PYTHON_EXE%" -m uvicorn app.api.main:app --host 127.0.0.1 --port 8100

echo.
echo Service stopped.
pause
