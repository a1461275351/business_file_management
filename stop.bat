@echo off
chcp 65001 >nul
title 贸易云档 - 停止服务

echo ============================================
echo   贸易云档 TradeDoc - 停止 Python OCR 服务
echo ============================================
echo.
echo 注意: PHP/Nginx/MySQL 由 phpStudy 管理，请在 phpStudy 面板停止
echo.

:: 停止 Python OCR
echo 停止 Python OCR (8100)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8100.*LISTENING"') do (
    taskkill /F /PID %%a >nul 2>&1
)
echo     [OK]

:: 顺手停掉旧的 RoadRunner（如果有残留）
taskkill /F /IM rr.exe >nul 2>&1

echo.
pause
