@echo off
chcp 65001 >nul
title 贸易云档 - 自动化测试

echo ============================================
echo   贸易云档 TradeDoc - 自动化测试
echo ============================================
echo.

set PYTHON_EXE=C:\Users\Administrator\AppData\Local\Python\pythoncore-3.14-64\python.exe
cd /d "%~dp0"

echo [1/2] API 接口测试 (46项)...
echo.
"%PYTHON_EXE%" -m pytest tests/test_api.py -v --tb=short -s
echo.

echo [2/2] UI 自动化测试 (27项)...
echo.
"%PYTHON_EXE%" -m pytest tests/test_ui.py -v --tb=short -s
echo.

echo ============================================
echo   测试完成！截图保存在 tests\screenshots\
echo ============================================
pause
