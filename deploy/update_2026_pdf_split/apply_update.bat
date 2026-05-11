@echo off
chcp 65001 >nul
title 贸易云档 - PDF 拆分功能 增量更新

setlocal enabledelayedexpansion

echo ============================================================
echo   贸易云档 TradeDoc - 增量更新 v2026_pdf_split
echo ============================================================
echo.

:: ========== 配置区（按生产服务器实际路径修改）==========
set PROJECT_ROOT=C:\product\business_file_management
set PHPSTUDY_ROOT=C:\phpstudy_pro
set PHP_VERSION=php8.5.0nts
set MYSQL_VERSION=MySQL8.0.12
set PYTHON_EXE=C:\Users\Administrator\AppData\Local\Python\pythoncore-3.14-64\python.exe
set DB_NAME=tradedoc
set DB_USER=root

:: 自动计算路径
set PHP_EXE=%PHPSTUDY_ROOT%\Extensions\php\%PHP_VERSION%\php.exe
set MYSQL_EXE=%PHPSTUDY_ROOT%\Extensions\%MYSQL_VERSION%\bin\mysql.exe
set MYSQLDUMP_EXE=%PHPSTUDY_ROOT%\Extensions\%MYSQL_VERSION%\bin\mysqldump.exe

:: 备份目录（按时间戳）
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value ^| find "="') do set DT=%%I
set TIMESTAMP=%DT:~0,4%%DT:~4,2%%DT:~6,2%_%DT:~8,2%%DT:~10,2%%DT:~12,2%
set BACKUP_DIR=C:\product\backup_%TIMESTAMP%

:: ========== 部署前检查 ==========
echo [检查] 项目根目录: %PROJECT_ROOT%
if not exist "%PROJECT_ROOT%\tradedoc" (
    echo [错误] 项目目录不存在: %PROJECT_ROOT%\tradedoc
    echo 请检查 PROJECT_ROOT 配置
    pause & exit /b 1
)

if not exist "%PHP_EXE%" (
    echo [错误] PHP 不存在: %PHP_EXE%
    echo 请检查 PHPSTUDY_ROOT 和 PHP_VERSION 配置
    pause & exit /b 1
)

if not exist "%MYSQL_EXE%" (
    echo [错误] MySQL 不存在: %MYSQL_EXE%
    echo 请检查 MYSQL_VERSION 配置
    pause & exit /b 1
)

if not exist "%PYTHON_EXE%" (
    echo [警告] Python 不存在: %PYTHON_EXE%
    echo Python 端更新会跳过，可后续手动处理
    set SKIP_PYTHON=1
)

echo [检查] 通过
echo.

:: 二次确认
set /p DB_PWD=请输入 MySQL root 密码:
if "%DB_PWD%"=="" (
    echo [错误] 密码不能为空
    pause & exit /b 1
)

echo.
echo 即将执行以下操作:
echo   1. 备份数据库 + 代码到 %BACKUP_DIR%
echo   2. 停止 Python OCR 服务
echo   3. 复制覆盖代码到 %PROJECT_ROOT%
echo   4. 应用数据库迁移
echo   5. 安装 Python 依赖（pymupdf, pdfplumber）
echo   6. 清 Laravel 缓存并重建
echo   7. 启动 Python OCR 服务
echo.
set /p CONFIRM=确认开始？(y/N):
if /i not "%CONFIRM%"=="y" (
    echo 已取消
    pause & exit /b 0
)

:: ========== [1/7] 备份 ==========
echo.
echo [1/7] 备份数据库 + 代码...
mkdir "%BACKUP_DIR%" 2>nul

echo   - 数据库备份中...
"%MYSQLDUMP_EXE%" -u%DB_USER% -p%DB_PWD% %DB_NAME% > "%BACKUP_DIR%\db_backup.sql" 2>nul
if errorlevel 1 (
    echo [错误] 数据库备份失败，请检查密码是否正确
    pause & exit /b 1
)
echo   - 数据库备份完成: %BACKUP_DIR%\db_backup.sql

echo   - 代码备份中（约 1-2 分钟，含 vendor）...
xcopy "%PROJECT_ROOT%\tradedoc" "%BACKUP_DIR%\tradedoc\" /E /I /Y /Q >nul 2>&1
xcopy "%PROJECT_ROOT%\tradedoc-python" "%BACKUP_DIR%\tradedoc-python\" /E /I /Y /Q >nul 2>&1
echo   - 代码备份完成

:: ========== [2/7] 停 Python OCR ==========
echo.
echo [2/7] 停止 Python OCR 服务...
if exist "%PROJECT_ROOT%\stop.bat" (
    call "%PROJECT_ROOT%\stop.bat" >nul 2>&1
)
:: 强制 kill 8100 端口（防止没停干净）
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8100.*LISTENING"') do taskkill /F /PID %%a >nul 2>&1
timeout /t 2 /nobreak >nul

:: ========== [3/7] 复制覆盖 ==========
echo.
echo [3/7] 复制新文件覆盖旧文件...
xcopy "tradedoc" "%PROJECT_ROOT%\tradedoc\" /E /I /Y >nul
if errorlevel 1 (
    echo [错误] PHP 端复制失败
    pause & exit /b 1
)
echo   - PHP 端复制完成

if not defined SKIP_PYTHON (
    xcopy "tradedoc-python" "%PROJECT_ROOT%\tradedoc-python\" /E /I /Y >nul
    if errorlevel 1 (
        echo [错误] Python 端复制失败
        pause & exit /b 1
    )
    echo   - Python 端复制完成
)

:: ========== [4/7] 数据库迁移 ==========
echo.
echo [4/7] 应用数据库迁移...
"%MYSQL_EXE%" -u%DB_USER% -p%DB_PWD% %DB_NAME% < database\add_split_support.sql
if errorlevel 1 (
    echo [错误] 数据库迁移失败
    echo 备份文件: %BACKUP_DIR%\db_backup.sql
    pause & exit /b 1
)
echo   - 数据库迁移完成

:: 验证字段是否加上
echo   - 验证字段:
"%MYSQL_EXE%" -u%DB_USER% -p%DB_PWD% %DB_NAME% -e "DESC documents" | findstr /C:"parent_document_id" /C:"split_page_range" /C:"is_split_container"

:: ========== [5/7] Python 依赖 ==========
if not defined SKIP_PYTHON (
    echo.
    echo [5/7] 安装/升级 Python 依赖...
    pushd "%PROJECT_ROOT%\tradedoc-python"
    "%PYTHON_EXE%" -m pip install --quiet pymupdf pdfplumber
    if errorlevel 1 (
        echo [警告] Python 依赖安装失败，请手动执行:
        echo   %PYTHON_EXE% -m pip install pymupdf pdfplumber
    ) else (
        echo   - 依赖安装完成
    )
    popd
) else (
    echo.
    echo [5/7] 跳过 Python 依赖（Python 不可用）
)

:: ========== [6/7] Laravel 缓存 ==========
echo.
echo [6/7] 清 Laravel 缓存并重建...
pushd "%PROJECT_ROOT%\tradedoc"
"%PHP_EXE%" artisan view:clear >nul
"%PHP_EXE%" artisan config:clear >nul
"%PHP_EXE%" artisan route:clear >nul
"%PHP_EXE%" artisan config:cache >nul
"%PHP_EXE%" artisan route:cache >nul
"%PHP_EXE%" artisan view:cache >nul
echo   - Laravel 缓存重建完成
popd

:: ========== [7/7] 启动 Python OCR ==========
if not defined SKIP_PYTHON (
    echo.
    echo [7/7] 启动 Python OCR 服务...
    if exist "%PROJECT_ROOT%\start.bat" (
        start "" cmd /c "%PROJECT_ROOT%\start.bat"
        timeout /t 5 /nobreak >nul
        :: 健康检查
        curl -s -m 3 http://127.0.0.1:8100/api/health >nul 2>&1
        if errorlevel 1 (
            echo [警告] Python 服务启动后健康检查失败，请手动检查
        ) else (
            echo   - Python 服务已启动并健康
        )
    ) else (
        echo [警告] 找不到 start.bat，请手动启动 Python OCR
    )
) else (
    echo.
    echo [7/7] 跳过 Python 服务启动
)

:: ========== 完成 ==========
echo.
echo ============================================================
echo   增量更新完成
echo ============================================================
echo.
echo 备份位置: %BACKUP_DIR%
echo.
echo 接下来手动操作:
echo   1. phpStudy 面板 → PHP → 重启 PHP-CGI
echo   2. 浏览器强刷 Ctrl+Shift+F5
echo   3. 进入任意 PDF 文件详情页，确认右上角有「智能拆分」黄色按钮
echo.
echo 如需回滚，参考 UPDATE.txt 中的「回滚」一节
echo.
pause
