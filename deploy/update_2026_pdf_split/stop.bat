@echo off
chcp 65001 >nul
title TradeDoc - Stop OCR Service
echo ============================================
echo   TradeDoc - Stop Python OCR Service
echo ============================================
echo.
echo Note: PHP/Nginx/MySQL are managed by phpStudy panel.
echo.

echo Stopping Python OCR service (port 8100)...
set FOUND=0
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8100.*LISTENING"') do (
    taskkill /F /PID %%a >nul 2>&1
    set FOUND=1
)
if "%FOUND%"=="1" (
    echo   [OK] Service stopped.
) else (
    echo   [INFO] No service running on port 8100.
)

:: Clean up old RoadRunner if any
taskkill /F /IM rr.exe >nul 2>&1

echo.
timeout /t 2 /nobreak >nul
exit
