================================================================
  贸易云档 TradeDoc - 部署指南（Windows 服务器 + phpStudy）
================================================================

【架构】

  浏览器
     ↓
  phpStudy Nginx :8000
     ├─ 静态文件 (public/build, *.js *.css)
     └─ PHP 请求 → FastCGI 127.0.0.1:9002 (phpStudy 自带 php-cgi 池)
                       ↓
                    Laravel
                       ↓
                    MySQL :3306
                       +
                    Python OCR :8100 (可选)

  - 不需要 RoadRunner / Octane（旧版本用过，已弃用）
  - PHP 进程由 phpStudy 自动管理（启停在 phpStudy 面板）
  - 我们只需启动 Python OCR（如启用）


【部署步骤】

1. 安装 phpStudy Pro
   - 下载 phpStudy_pro 并安装
   - 在面板里启动: Nginx + MySQL + PHP 8.5 NTS

2. 复制 PHP 8.5（如果 phpStudy 默认没装）
   - 把 php8.5.0nts 整个文件夹复制到:
     phpStudy_pro\Extensions\php\php8.5.0nts\
   - 在面板「PHP 版本」里选中并启动它，记下 phpStudy 给它分配的端口（默认 9002）

3. 复制项目文件到服务器
   - 整个 business_file_management 目录复制到目标位置
     例: D:\work\product\business_file_management\
   - 注意：vendor/ 目录较大（约 1G），建议直接打包复制，避免在内网服务器跑 composer

4. 创建数据库
   - 在 phpStudy MySQL 里执行:
     CREATE DATABASE tradedoc DEFAULT CHARSET utf8mb4 COLLATE utf8mb4_unicode_ci;
   - 导入数据:
     mysql -u root -p tradedoc < database/trade_doc_system.sql

5. 修改配置
   - tradedoc/.env
       APP_URL=http://服务器IP:8000
       APP_ENV=production
       APP_DEBUG=false
       DB_PASSWORD=（实际密码）
   - tradedoc-python/.env（如启用 Python OCR）
       数据库密码、阿里云 API Key 等

6. 配置 Nginx 站点
   - 把 deploy/nginx_tradedoc.conf 复制到:
     phpStudy_pro\Extensions\Nginx{版本}\conf\vhosts\tradedoc.conf
   - 编辑两处路径：root 和 access_log/error_log（改成实际路径）
   - 如果 phpStudy 给的 PHP-CGI 端口不是 9002，改 upstream 里的端口号
   - 在 phpStudy 里点「重启 Nginx」

7. 缓存配置（生产环境必做，提速）
   cd tradedoc
   php artisan config:cache
   php artisan route:cache
   php artisan view:cache

8. （可选）启动 Python OCR 服务
   - 装 Python 3.10+ 和依赖：
     pip install fastapi uvicorn pymysql sqlalchemy python-dotenv python-multipart Pillow pdfplumber pymupdf dashscope
   - 改 start.bat 里的 PYTHON_EXE 路径
   - 双击 start.bat（只启动 Python OCR；PHP/Nginx 由 phpStudy 管）

9. 访问 http://服务器IP:8000
   - 默认账号: admin / admin123（首次登录请改密码）


【日常运维】

- 启动/停止 PHP/Nginx/MySQL：直接在 phpStudy 面板点
- 启动/停止 Python OCR：双击 start.bat / stop.bat
- 查 Nginx 日志：phpStudy_pro\Extensions\Nginx{版本}\logs\tradedoc_*.log
- 查 PHP/Laravel 日志：tradedoc\storage\logs\laravel.log
- 文件存储位置：tradedoc\storage\app\private\documents\（更新代码不要覆盖）


【目录说明】

business_file_management/
├── tradedoc/                ← Laravel 主项目
│   ├── .env                 ← 数据库等配置（需修改）
│   ├── public/              ← Web 入口（Nginx root 指这里）
│   ├── storage/             ← 上传文件 + 日志
│   ├── vendor/              ← PHP 依赖（已装好）
│   ├── .rr.yaml.bak         ← 旧 RoadRunner 配置（已弃用，保留参考）
│   └── ...
├── tradedoc-python/         ← Python OCR 服务（可选）
│   ├── .env                 ← 配置（需修改）
│   └── app/
├── database/                ← MySQL 建表 + 初始数据
├── deploy/
│   ├── README_DEPLOY.txt    ← 本文档
│   └── nginx_tradedoc.conf  ← Nginx 配置模板
├── start.bat                ← 仅启 Python OCR
└── stop.bat                 ← 仅停 Python OCR


【常见问题】

Q: 访问首页 502 Bad Gateway
A: phpStudy 的 PHP-CGI 没起来。在 phpStudy 面板「PHP 版本」里启动 8.5 NTS。
   或者 nginx_tradedoc.conf 里的 upstream 端口号和 phpStudy 给的不一致。
   netstat -ano | findstr "9002" 看实际端口。

Q: 接口报 404 但首页能打开
A: Nginx 配置里 try_files 没生效。检查 location / 里 try_files 行。

Q: 上传大文件报错
A: 改 client_max_body_size（Nginx）和 upload_max_filesize / post_max_size（php.ini）。
   phpStudy 的 php.ini 在: Extensions\php\php8.5.0nts\php.ini

Q: 数据库连接断（持续运行几天后报 SQLSTATE[2002]）
A: PHP-CGI 模式下每个请求独立，不存在 Octane 那种连接老化问题。
   如果还是报，看 MySQL 是否在运行（phpStudy 面板）。
