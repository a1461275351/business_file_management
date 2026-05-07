@echo off
chcp 65001 >nul
title 贸易云档 - TradeDoc 控制台

echo ============================================
echo   贸易云档 TradeDoc - 启动所有服务
echo ============================================
echo.

set PYTHON_DIR=%~dp0tradedoc-python
set PYTHON_EXE=C:\Users\Administrator\AppData\Local\Python\pythoncore-3.14-64\python.exe

:: 清理旧的 Python 进程（PHP 由 phpStudy 自己管理，不要碰）
echo 清理旧 Python 进程...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8100.*LISTENING"') do taskkill /F /PID %%a >nul 2>&1
timeout /t 1 /nobreak >nul

:: 启动 Python OCR 服务
if exist "%PYTHON_EXE%" (
    echo [1/1] 启动 Python OCR 服务 (FastAPI:8100)...
    start "TradeDoc-Python" cmd /k "cd /d %PYTHON_DIR% && %PYTHON_EXE% -m uvicorn app.api.main:app --host 127.0.0.1 --port 8100"
    timeout /t 3 /nobreak >nul
) else (
    echo [1/1] 跳过 Python 服务（未安装）
)

echo.
echo 正在验证服务状态...
timeout /t 2 /nobreak >nul

curl -s -o nul -w "  PHP    (9002): %%{http_code} (404=正常监听)\n" http://127.0.0.1:9002/
curl -s -o nul -w "  Python (8100): %%{http_code}\n" http://127.0.0.1:8100/api/health
curl -s -o nul -w "  Nginx  (8000): %%{http_code}\n" http://127.0.0.1:8000/

echo.
echo ============================================
echo   启动完成！Nginx 显示 200 即正常
echo.
echo   访问地址: http://127.0.0.1:8000
echo   前提:   phpStudy 中 Nginx + MySQL + PHP 已启动
echo.
echo   管理员账号: admin / admin123
echo ============================================
echo.
pause
