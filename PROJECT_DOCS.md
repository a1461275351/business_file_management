# 贸易云档 (TradeDoc) - 项目功能文档

> 文档更新时间: 2026-04-28（v2 部署架构调整版）
> 上一版: 2026-04-09

---

## 1. 项目概述

**贸易云档**是一套面向外贸企业的文件智能管理系统，通过 OCR + AI 自动提取报关单、发票、装箱单等外贸单证的关键字段，实现文件的上传、识别、核对、归档、导出全流程数字化管理。

### 1.1 技术栈

| 层级 | 技术 | 版本 |
|------|------|------|
| 前端 | Vue 3 + Element Plus + Vite | 已编译，产物在 `tradedoc/public/build/` |
| 后端 (PHP) | Laravel 13 + Sanctum + Spatie Permission | PHP 8.5.5 NTS / VS17 / x64 |
| 后端 (Python) | FastAPI + 阿里云 DashScope OCR | Python 3.10+，可选 |
| 数据库 | MySQL 8.0 | utf8mb4 / utf8mb4_unicode_ci |
| Web 服务器 | Nginx 1.15+ (phpStudy 自带) | FastCGI 转发 |
| PHP 运行 | phpStudy 自带 php-cgi 池 | 1 主 + 16 worker |
| Excel 导出 | Maatwebsite/Excel (PhpSpreadsheet) | - |

### 1.2 关键变更（v2）

> 上线前从 RoadRunner/Octane 切换到传统 PHP-CGI 模式，原因：
> - Octane 在 Windows 长跑下 DB 连接老化导致偶发 502
> - phpStudy 自带 PHP-CGI 池更稳定，零额外依赖
> - 部署更简单：只需 phpStudy + 复制项目即可
>
> 旧版 `.rr.yaml` 已重命名为 `.rr.yaml.bak` 保留备查。

---

## 2. 系统架构

```
浏览器
  │
  │  http://server:8000
  ▼
┌─────────────────────────────────────────┐
│  Nginx :8000  (phpStudy 自带)           │
│  ├─ 静态资源 → public/build/、*.js/css  │
│  └─ 其他请求 → FastCGI                  │
└─────────────────────────────────────────┘
                │
                │  127.0.0.1:9001 (FastCGI)
                ▼
┌─────────────────────────────────────────┐
│  PHP-CGI 池 (phpStudy 管理)             │
│  ├─ xp.cn_cgi.exe (master)              │
│  └─ php-cgi.exe × 16 (workers)          │
│      ↓                                  │
│  Laravel 应用 (tradedoc/public/index.php)│
│  ├─ 认证 → Sanctum (Bearer Token)       │
│  ├─ 权限 → Spatie Permission            │
│  └─ ORM  → Eloquent                     │
└─────────────────────────────────────────┘
        │                       │
        │                       │ HTTP (可选)
        ▼                       ▼
┌──────────────┐      ┌──────────────────┐
│ MySQL :3306  │      │ Python OCR :8100 │
│ tradedoc 库  │      │ FastAPI (可选)   │
└──────────────┘      └──────────────────┘
```

| 服务 | 端口 | 进程 | 启停方式 |
|------|------|------|----------|
| Nginx | 8000 | nginx.exe | phpStudy 面板 |
| PHP-CGI 池 | 9001 | xp.cn_cgi.exe + php-cgi.exe | phpStudy 面板 |
| MySQL | 3306 | mysqld.exe | phpStudy 面板 |
| Python OCR | 8100 | python.exe (uvicorn) | start.bat（可选） |

---

## 3. 功能模块清单

### 3.1 概览仪表盘
| 功能点 | API | 前端页面 |
|--------|-----|----------|
| 文件统计概览 | `GET /api/v1/documents/statistics` | `/dashboard` |
| 通知未读数 | `GET /api/v1/notifications/unread-count` | 顶栏通知图标 |

### 3.2 文件管理
| 功能点 | API | 前端页面 |
|--------|-----|----------|
| 文件列表(分页/筛选/搜索) | `GET /api/v1/documents` | `/documents` |
| 文件详情 | `GET /api/v1/documents/{id}` | `/documents/:id` |
| 文件类型字典 | `GET /api/v1/document-types` | 上传时选择 |
| 文件预览 | `GET /api/v1/documents/{id}/preview` | 详情页内嵌 |
| 文件下载 | `GET /api/v1/documents/{id}/download` | 详情页按钮 |
| 单文件导出 Excel | `GET /api/v1/documents/{id}/export` | 详情页按钮 |
| 批量导出 Excel | `GET /api/v1/documents/export` | 列表页按钮 |
| 删除文件 | `DELETE /api/v1/documents/{id}` | 列表/详情页 |
| 变更文件状态 | `PUT /api/v1/documents/{id}/status` | 详情页 |
| 更新提取字段 | `POST /api/v1/documents/update-field` | 详情页编辑 |
| 新增提取字段 | `POST /api/v1/documents/add-field` | 详情页 |
| 删除提取字段 | `DELETE /api/v1/documents/fields/{fieldId}` | 详情页 |
| 重新 OCR 识别 | `POST /api/v1/documents/re-ocr` | 详情页按钮 |
| 查看 OCR 缓存 | `GET /api/v1/documents/{id}/ocr-cache` | 详情页 |
| 数据报表 | `GET /api/v1/documents/reports` | `/reports` |

### 3.3 上传录入
| 功能点 | API | 前端页面 |
|--------|-----|----------|
| 单文件上传 | `POST /api/v1/documents/upload` | `/upload` |
| 批量上传 | `POST /api/v1/documents/batch-upload` | `/upload` |

### 3.4 人工核对
| 功能点 | API | 前端页面 |
|--------|-----|----------|
| 核对任务列表 | `GET /api/v1/reviews` | `/review` |
| 核对统计 | `GET /api/v1/reviews/statistics` | `/review` |
| 核对详情 | `GET /api/v1/reviews/{id}` | `/review` |
| 确认核对 | `POST /api/v1/reviews/{id}/confirm` | `/review` |
| 跳过核对 | `POST /api/v1/reviews/{id}/skip` | `/review` |

### 3.5 订单管理
| 功能点 | API | 前端页面 |
|--------|-----|----------|
| 订单列表 | `GET /api/v1/orders` | `/orders` |
| 订单详情 | `GET /api/v1/orders/{id}` | `/orders` |
| 创建订单 | `POST /api/v1/orders` | `/orders` |
| 更新订单 | `PUT /api/v1/orders/{id}` | `/orders` |
| 删除订单 | `DELETE /api/v1/orders/{id}` | `/orders` |
| 订单选项(下拉) | `GET /api/v1/orders/options` | 表单选项 |

### 3.6 客户管理
| 功能点 | API | 前端页面 |
|--------|-----|----------|
| 客户列表 | `GET /api/v1/customers` | `/customers` |
| 客户详情 | `GET /api/v1/customers/{id}` | `/customers` |
| 创建客户 | `POST /api/v1/customers` | `/customers` |
| 更新客户 | `PUT /api/v1/customers/{id}` | `/customers` |
| 删除客户 | `DELETE /api/v1/customers/{id}` | `/customers` |
| 客户选项(下拉) | `GET /api/v1/customers/options` | 表单选项 |

### 3.7 通知中心
| 功能点 | API | 前端页面 |
|--------|-----|----------|
| 通知列表 | `GET /api/v1/notifications` | 顶栏弹窗 |
| 未读数量 | `GET /api/v1/notifications/unread-count` | 顶栏角标 |
| 标记已读 | `PUT /api/v1/notifications/{id}/read` | 通知列表 |
| 全部已读 | `PUT /api/v1/notifications/read-all` | 通知列表 |

### 3.8 AI 业务大模型
| 功能点 | API | 前端页面 |
|--------|-----|----------|
| AI 智能问答 | `POST /api/v1/ai/chat` | `/ai` |

> 集成阿里云通义千问 (DashScope)，以系统业务数据为上下文回答问题；无 API Key 时降级为本地规则引擎。

### 3.9 数据管道
| 功能点 | API | 前端页面 |
|--------|-----|----------|
| 管道流程可视化 | - | `/pipeline` |

> 展示文件从上传到归档的处理管道状态（前端页面）。

### 3.10 系统设置 (管理后台)
| 功能点 | API | 前端页面 |
|--------|-----|----------|
| 用户列表 | `GET /api/v1/admin/users` | `/settings` |
| 创建用户 | `POST /api/v1/admin/users` | `/settings` |
| 更新用户 | `PUT /api/v1/admin/users/{id}` | `/settings` |
| 删除用户 | `DELETE /api/v1/admin/users/{id}` | `/settings` |
| 角色列表 | `GET /api/v1/admin/roles` | `/settings` |
| 字段模板查询 | `GET /api/v1/admin/field-templates/{typeId}` | `/settings` |
| 操作日志 | `GET /api/v1/admin/logs` | `/settings` |

### 3.11 认证模块
| 功能点 | API | 前端页面 |
|--------|-----|----------|
| 登录 | `POST /api/v1/auth/login` | `/login` |
| 获取当前用户 | `GET /api/v1/auth/me` | 全局 |
| 退出登录 | `POST /api/v1/auth/logout` | 顶栏菜单 |

### 3.12 OCR 引擎
| 功能点 | API | 说明 |
|--------|-----|------|
| 引擎状态查询 | `GET /api/v1/ocr/engine-status` | 代理到 Python 服务 |

---

## 4. 数据库表清单

数据库名: `tradedoc`，共 **37 张表**（业务表 22 + Spatie 权限 5 + Laravel 内置 10）。

### 4.1 业务表（22 张，由 `database/install.sql` 创建）

| # | 表名 | 中文说明 |
|---|------|----------|
| 1 | departments | 部门表 |
| 2 | users | 用户表 |
| 3 | roles | 角色表 |
| 4 | permissions | 权限表 |
| 5 | role_permissions | 角色权限关联（旧表，已被 Spatie 取代） |
| 6 | user_roles | 用户角色关联（旧表，已被 Spatie 取代） |
| 7 | user_customers | 用户-客户负责关系表 |
| 8 | customers | 客户/供应商表 |
| 9 | orders | 订单表 |
| 10 | document_types | 文件类型字典表 |
| 11 | documents | 文件主表 |
| 12 | document_versions | 文件版本表 |
| 13 | document_relations | 文件关联表 |
| 14 | document_tags | 文件标签表 |
| 15 | field_templates | 字段提取模板表 |
| 16 | document_fields | 文件字段提取值表 |
| 17 | ocr_tasks | OCR/NLP 处理任务队列 |
| 18 | approval_rules | 审批规则配置表 |
| 19 | approval_records | 审批记录表 |
| 20 | approval_details | 审批明细表 |
| 21 | review_tasks | 人工核对任务表 |
| 22 | notifications | 通知表 |
| 23 | notification_settings | 通知偏好设置表 |
| 24 | operation_logs | 操作日志表 |
| 25 | field_change_logs | 字段变更历史表 |
| 26 | pipeline_logs | 数据管道处理日志 |
| 27 | anomaly_alerts | 跨文件异常告警表 |
| 28 | system_configs | 系统配置表 |
| 29 | email_configs | 邮箱绑定配置表 |

### 4.2 Spatie Permission 表（3 张，由 `database/fix_spatie_tables.sql` 创建）

> 实际权限关系存储用这套 Spatie 标准表，原 `role_permissions`/`user_roles` 仅为兼容保留。

| # | 表名 | 中文说明 |
|---|------|----------|
| 1 | model_has_roles | 用户 ↔ 角色绑定（实际使用） |
| 2 | model_has_permissions | 用户 ↔ 直接授权（绕过角色） |
| 3 | role_has_permissions | 角色 ↔ 权限映射（实际使用） |

### 4.3 Laravel 内置表（7 张，由 `database/fix_missing_tables.sql` 创建）

| # | 表名 | 用途 |
|---|------|------|
| 1 | personal_access_tokens | **Sanctum API Token，登录必需** |
| 2 | password_reset_tokens | 密码重置 Token |
| 3 | sessions | Laravel Session（当前 file 驱动暂未用） |
| 4 | cache | Laravel Cache（当前 file 驱动暂未用） |
| 5 | cache_locks | Laravel 缓存锁 |
| 6 | jobs | 队列任务（当前 sync 驱动暂未用） |
| 7 | job_batches | 队列批次 |
| 8 | failed_jobs | 队列失败记录 |
| 9 | migrations | Laravel 迁移记录表 |

---

## 5. API 接口清单

### 5.1 认证模块 (Auth)
| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | `/api/v1/auth/login` | 用户登录 | 否 |
| GET | `/api/v1/auth/me` | 获取当前用户信息 | 是 |
| POST | `/api/v1/auth/logout` | 退出登录 | 是 |

### 5.2 文件管理 (Document)
| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | `/api/v1/document-types` | 文件类型列表 | 是 |
| GET | `/api/v1/documents` | 文件列表(分页筛选) | 是 |
| GET | `/api/v1/documents/statistics` | 文件统计数据 | 是 |
| GET | `/api/v1/documents/reports` | 数据报表 | 是 |
| GET | `/api/v1/documents/{id}` | 文件详情 | 是 |
| POST | `/api/v1/documents/upload` | 上传单个文件 | 是 |
| POST | `/api/v1/documents/batch-upload` | 批量上传文件 | 是 |
| POST | `/api/v1/documents/update-field` | 更新提取字段值 | 是 |
| POST | `/api/v1/documents/add-field` | 新增提取字段 | 是 |
| DELETE | `/api/v1/documents/fields/{fieldId}` | 删除提取字段 | 是 |
| POST | `/api/v1/documents/re-ocr` | 重新执行 OCR | 是 |
| GET | `/api/v1/documents/{id}/ocr-cache` | 查看 OCR 缓存结果 | 是 |
| PUT | `/api/v1/documents/{id}/status` | 变更文件状态 | 是 |
| DELETE | `/api/v1/documents/{id}` | 删除文件 | 是 |
| GET | `/api/v1/documents/{id}/preview` | 文件预览 | 否 |
| GET | `/api/v1/documents/{id}/download` | 文件下载 | 否 |
| GET | `/api/v1/documents/{id}/export` | 单文件导出 Excel | 否 |
| GET | `/api/v1/documents/export` | 批量导出 Excel | 否 |

### 5.3 人工核对 (Review)
| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | `/api/v1/reviews` | 核对任务列表 | 是 |
| GET | `/api/v1/reviews/statistics` | 核对统计 | 是 |
| GET | `/api/v1/reviews/{id}` | 核对任务详情 | 是 |
| POST | `/api/v1/reviews/{id}/confirm` | 确认核对通过 | 是 |
| POST | `/api/v1/reviews/{id}/skip` | 跳过核对 | 是 |

### 5.4 订单管理 (Order)
| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | `/api/v1/orders/options` | 订单下拉选项 | 是 |
| GET | `/api/v1/orders` | 订单列表 | 是 |
| GET | `/api/v1/orders/{id}` | 订单详情 | 是 |
| POST | `/api/v1/orders` | 创建订单 | 是 |
| PUT | `/api/v1/orders/{id}` | 更新订单 | 是 |
| DELETE | `/api/v1/orders/{id}` | 删除订单 | 是 |

### 5.5 客户管理 (Customer)
| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | `/api/v1/customers/options` | 客户下拉选项 | 是 |
| GET | `/api/v1/customers` | 客户列表 | 是 |
| GET | `/api/v1/customers/{id}` | 客户详情 | 是 |
| POST | `/api/v1/customers` | 创建客户 | 是 |
| PUT | `/api/v1/customers/{id}` | 更新客户 | 是 |
| DELETE | `/api/v1/customers/{id}` | 删除客户 | 是 |

### 5.6 通知 (Notification)
| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | `/api/v1/notifications` | 通知列表 | 是 |
| GET | `/api/v1/notifications/unread-count` | 未读通知数 | 是 |
| PUT | `/api/v1/notifications/{id}/read` | 标记单条已读 | 是 |
| PUT | `/api/v1/notifications/read-all` | 全部标记已读 | 是 |

### 5.7 AI 问答 (AI Chat)
| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | `/api/v1/ai/chat` | AI 智能问答 | 是 |

### 5.8 OCR 引擎
| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | `/api/v1/ocr/engine-status` | OCR 引擎状态(代理 Python) | 是 |

### 5.9 管理后台 (Admin)
| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | `/api/v1/admin/users` | 用户列表 | 是 |
| POST | `/api/v1/admin/users` | 创建用户 | 是 |
| PUT | `/api/v1/admin/users/{id}` | 更新用户 | 是 |
| DELETE | `/api/v1/admin/users/{id}` | 删除用户 | 是 |
| GET | `/api/v1/admin/roles` | 角色列表 | 是 |
| GET | `/api/v1/admin/field-templates/{typeId}` | 字段模板查询 | 是 |
| GET | `/api/v1/admin/logs` | 操作日志列表 | 是 |

---

## 6. 文件处理流程

```
上传 → OCR 识别 → 字段提取 → 人工核对 → 审批 → 归档 → 导出
```

**详细步骤**：

1. **上传**: 用户通过 `/upload` 页面上传文件（支持单文件/批量），系统生成文件编号，存储到 `storage/app/private/documents/`
2. **OCR 识别**: PHP 后端调用 Python FastAPI 服务 (`http://127.0.0.1:8100`) 进行 OCR
   - 引擎按优先级选择: 阿里云 DashScope API > 本地模型 > Mock
   - 若 Python 服务未启动，文件停留在 `draft` 状态等待人工处理
3. **字段提取**: OCR 完成后根据文件类型对应的字段模板 (`field_templates`) 自动提取关键字段（如报关单号、金额、日期等），存入 `document_fields` 表
4. **人工核对**: 置信度低于阈值 (默认 80%) 的字段自动生成核对任务 (`review_tasks`)，由单证员在 `/review` 页面逐一确认或修正
5. **审批**: 变更状态触发审批规则 (`approval_rules`)，支持多级审批（**未实现**，见第 11 节）
6. **归档**: 审批通过后文件状态变为 `archived`，记录归档时间
7. **导出**: 支持单文件/批量导出 Excel，使用 Maatwebsite/Excel

**文件状态流转**:
```
draft → ocr_processing → pending_review → pending_approval → approved → archived
                                                                   ↓
                                                                voided（任意状态可作废）
```

---

## 7. 账号与权限

### 7.1 角色定义

| 角色标识 | 显示名称 | 说明 |
|----------|----------|------|
| super_admin | 超级管理员 | 全部功能与系统配置权限（18 项）|
| manager | 业务主管 | 部门文件管理、审批、报表导出（12 项）|
| salesman | 业务员 | 上传与管理自己负责客户的文件（8 项）|
| doc_clerk | 单证员 | OCR 核对、字段修正、文件关联（6 项）|
| finance | 财务人员 | 查看银行水单/发票、导出财务数据（7 项）|
| readonly | 只读访客 | 仅查看授权范围内文件（1 项）|

### 7.2 权限模块

共 18 项权限，按模块分组：

| 模块 | 权限项 |
|------|--------|
| document (7) | upload, view, edit, delete, download, export, batch |
| review (2) | list, execute |
| approval (2) | submit, approve |
| report (2) | view, export |
| ai (1) | query |
| system (4) | config, user_manage, audit_log, notification_manage |

### 7.3 默认账号（v2 部署后）

| 字段 | 值 |
|------|----|
| 用户名 | `admin` |
| 密码 | `admin123` |
| 角色 | `super_admin`（model_has_roles 已绑定）|
| 邮箱 | `admin@tradedoc.local` |
| 状态 | 启用 |

> **首次登录后请立即改密码**：用 admin 登入 → `/settings` → 用户管理 → 改 admin 密码。

### 7.4 创建新用户

通过管理后台 API 创建：

```http
POST /api/v1/admin/users
Authorization: Bearer {admin_token}
{
  "username": "zhangsan",
  "real_name": "张三",
  "password": "abc123456",
  "email": "zhangsan@company.com",
  "role_id": 3,
  "status": 1
}
```

或在数据库直接 INSERT（需手动管理 model_has_roles 关联）。

### 7.5 菜单权限控制

| 菜单 | 需要权限 |
|------|----------|
| 人工核对 | `review.list` |
| 数据报表 | `report.view` |
| 系统设置 | `system.config` |
| AI 问答 | `ai.query` |

---

## 8. 部署说明（v2 - phpStudy 标准方案）

### 8.1 环境要求

| 组件 | 要求 |
|------|------|
| 操作系统 | Windows Server 2016+ / Windows 10+ |
| phpStudy Pro | 最新版（提供 Nginx + MySQL + PHP-CGI 池）|
| PHP | 8.5.5 NTS x64 (VS17，需 VC++ 2022 运行库) |
| MySQL | 8.0+ |
| Nginx | 1.15+ |
| 磁盘空间 | 至少 2GB（含 vendor、storage） |
| 内存 | 至少 2GB |
| Python | 3.10+（仅 OCR 服务需要，可选） |

### 8.2 服务端口

| 服务 | 端口 | 是否对外 |
|------|------|----------|
| Nginx (HTTP) | 8000 | ✅ 用户访问 |
| MySQL | 3306 | ❌ 仅本地 |
| PHP-CGI 池 | 9001 | ❌ 仅 Nginx 内部用 |
| Python OCR | 8100 | ❌ 仅 PHP 内部用 |

### 8.3 部署步骤

参见 `deploy/README_DEPLOY.txt` 详细文档。**简要流程**：

1. **服务器准备**
   - 装 phpStudy Pro
   - 装 VC++ 2022 运行库（https://aka.ms/vs/17/release/vc_redist.x64.exe）
   - 解压 PHP 8.5.5 NTS 到 `phpStudy_pro\Extensions\php\php8.5.0nts\`
   - 复制 `php.ini` 到该目录，确保 `extension_dir` 路径正确
   - 编辑 `phpStudy_pro\COM\xp.ini` 加入 `xp.cn_cgi9001=...php8.5.0nts/php-cgi.exe 9001 1+16` 行（或在 phpStudy 网站设置里选 PHP 版本会自动加）

2. **复制项目**
   - 整个 `business_file_management` 目录复制到目标服务器（含 vendor）
   - 推荐路径：`C:\product\business_file_management\`

3. **配置 .env**
   - 改 `tradedoc/.env`：APP_ENV=production / APP_DEBUG=false / APP_URL=http://服务器IP:8000 / DB_PASSWORD=实际密码

4. **建数据库 + 导入数据**
   - 在 phpStudy MySQL 里建库 + 导入：
     - `database/install.sql`（建表 + 初始数据）
     - `database/fix_missing_tables.sql`（Laravel 内置表）
     - `database/fix_spatie_tables.sql`（Spatie 权限表 + admin 绑定）

5. **缓存 Laravel 配置**
   ```cmd
   cd 项目路径\tradedoc
   ..\Extensions\php\php8.5.0nts\php.exe artisan config:cache
   ..\Extensions\php\php8.5.0nts\php.exe artisan route:cache
   ..\Extensions\php\php8.5.0nts\php.exe artisan view:cache
   ..\Extensions\php\php8.5.0nts\php.exe artisan storage:link
   ```

6. **配置 Nginx 站点**
   - phpStudy 面板 → 创建网站，端口 **8000**，根目录 **`项目路径/tradedoc/public`**
   - 替换生成的 vhost.conf 为 `deploy/nginx_tradedoc.conf` 内容
   - phpStudy 重启 Nginx

7. **开 Windows 防火墙**
   ```powershell
   New-NetFirewallRule -DisplayName "TradeDoc HTTP 8000" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow -Profile Any
   ```

8. **访问 + 登录**
   - 浏览器：`http://服务器IP:8000`
   - 账号：`admin / admin123`

### 8.4 部署相关文件

| 文件 | 用途 |
|------|------|
| `deploy/README_DEPLOY.txt` | 完整部署指南 |
| `deploy/nginx_tradedoc.conf` | Nginx 站点配置模板 |
| `deploy/server_install/php-8.5.5-nts-Win32-vs17-x64.zip` | PHP 安装包 |
| `deploy/server_install/php.ini` | 已配好的 PHP 配置 |
| `deploy/server_install/INSTALL_PHP.txt` | PHP 安装说明 |
| `database/install.sql` | 主建表脚本 |
| `database/fix_missing_tables.sql` | Laravel 内置表补建 |
| `database/fix_spatie_tables.sql` | Spatie 权限表 + 数据 |

---

## 9. 配置说明

### 9.1 PHP 配置 (`tradedoc/.env`)

| 配置项 | 说明 | 生产建议值 |
|--------|------|-----------|
| APP_NAME | 应用名称 | TradeDoc |
| APP_ENV | 环境 | **production** |
| APP_DEBUG | 调试模式 | **false** |
| APP_URL | 应用地址 | http://服务器IP:8000 |
| APP_KEY | 加密密钥 | **保持开发机的值，否则旧 token 失效** |
| DB_HOST | 数据库地址 | 127.0.0.1 |
| DB_PORT | 数据库端口 | 3306 |
| DB_DATABASE | 数据库名 | tradedoc |
| DB_USERNAME | 数据库用户名 | root |
| DB_PASSWORD | 数据库密码 | 服务器实际密码 |
| LOG_LEVEL | 日志级别 | warning |
| SESSION_DRIVER | 会话驱动 | file |
| QUEUE_CONNECTION | 队列驱动 | sync |
| FILESYSTEM_DISK | 文件存储 | local |
| BCRYPT_ROUNDS | bcrypt 强度 | 12 |

### 9.2 PHP-CGI 配置 (`php8.5.0nts/php.ini`)

关键配置项：

| 配置项 | 值 |
|--------|----|
| memory_limit | 256M |
| upload_max_filesize | 100M |
| post_max_size | 100M |
| max_execution_time | 300 |
| extension_dir | `C:/soft/phpstudy_pro/Extensions/php/php8.5.0nts/ext` |
| opcache.enable | 1 |
| **opcache.jit** | **0**（PHP 8.5 上 JIT 不稳定，已禁用） |
| date.timezone | Asia/Shanghai |

### 9.3 Python 配置 (`tradedoc-python/.env`)

| 配置项 | 说明 | 当前值 |
|--------|------|--------|
| OCR_ENGINE | OCR 引擎模式 | auto |
| OCR_MODEL_PATH | 本地模型路径 | D:/ai_models/Logics-Parsing-v2 |
| OCR_CONFIDENCE_THRESHOLD | 置信度阈值 | 80 |
| DASHSCOPE_API_KEY | 阿里云 DashScope 密钥 | （需配置） |
| FILE_STORAGE_PATH | 文件存储路径(与PHP共享) | `tradedoc/storage/app/private` |
| API_HOST | 服务监听地址 | 127.0.0.1 |
| API_PORT | 服务端口 | 8100 |

### 9.4 OCR 引擎模式

| 模式 | 说明 |
|------|------|
| aliyun_api | 阿里云 DashScope qwen-vl-ocr，**推荐**，无需 GPU |
| local_model | 本地 Logics-Parsing-v2 模型，需 GPU |
| mock | 模拟模式，开发调试用 |
| auto | 按优先级自动选择: aliyun_api > local_model > mock |

---

## 10. 运维与故障排查

### 10.1 日常操作

| 操作 | 方法 |
|------|------|
| 启停 Nginx/MySQL/PHP | phpStudy 面板 |
| 启停 Python OCR | `start.bat` / `stop.bat` |
| 查看 Laravel 错误日志 | `tradedoc/storage/logs/laravel.log` |
| 查看 Nginx 错误日志 | `phpstudy_pro/Extensions/Nginx{版本}/logs/tradedoc_error.log` |
| 查看 PHP 错误日志 | `phpstudy_pro/Extensions/php/php8.5.0nts/php_errors.log` |
| 修改 .env 后生效 | `php artisan config:cache` |
| 上传文件位置 | `tradedoc/storage/app/private/documents/年/月/类型/` |

### 10.2 备份对象

1. **数据库** `tradedoc`（mysqldump 或 phpMyAdmin 导出）
2. **上传文件** `tradedoc/storage/app/private/documents/`
3. **环境配置** `tradedoc/.env`、`tradedoc-python/.env`

### 10.3 常见问题

#### 502 Bad Gateway
- 原因：phpStudy 的 PHP-CGI 池死了
- 解决：phpStudy 面板重启 PHP；查 `tradedoc_error.log` 是否 9001 连接被拒

#### 登录后 dashboard 报错
- 原因：缓存的 config 跟实际不一致
- 解决：
  ```cmd
  php artisan config:clear && php artisan config:cache
  ```

#### 修改代码不生效
- Laravel 的 view/route/config 缓存需要清掉重建
- 如果只改了一个 PHP 文件，OPcache 默认会自动重新编译（`opcache.validate_timestamps=1`）

#### 上传文件大小超限
- 改 `php.ini` 的 `upload_max_filesize` 和 `post_max_size`
- 改 Nginx 配置的 `client_max_body_size`
- phpStudy 重启 PHP 和 Nginx

#### 局域网内其他电脑访问不到
1. 检查 Nginx 是否监听 0.0.0.0（不是 127.0.0.1）
2. 检查 Windows 防火墙是否开了 8000 端口
3. 检查公司网络是否有 VLAN 隔离

#### MySQL 连不上
- 检查 phpStudy MySQL 是否启动
- 检查 `.env` 里 `DB_PASSWORD` 是否正确
- 跑 `php artisan db:show` 验证连接

---

## 11. 待开发 / 占位功能

| 模块 | 状态 | 说明 |
|------|------|------|
| 审批工作流 | 数据库已设计，后端未实现 | `approval_rules`/`approval_records`/`approval_details` 三张表已建，但无对应 Controller 和 API |
| 数据管道页面 | 前端页面占位 | `/pipeline` 路由已注册，数据库有 `pipeline_logs` 表，但无后端 API |
| 邮箱自动采集 | 数据库已设计，未实现 | `email_configs` 表已建，用于自动采集邮件附件，暂无实现 |
| 通知偏好设置 | 数据库已设计，未实现 | `notification_settings` 表已建，未暴露配置 API |
| 跨文件异常告警 | 数据库已设计，未实现 | `anomaly_alerts` 表已建，跨文件金额/数量比对等功能未实现 |
| 文件版本管理 | 数据库已设计，基础实现 | `document_versions` 表已建，上传时记录版本，但无版本回滚等高级功能 |
| 文件关联管理 | 数据库已设计，未暴露 API | `document_relations` 表已建，同一票货文件分组功能未完整实现 |
| 文件标签 | 数据库已设计，未暴露 API | `document_tags` 表已建，无标签增删改查 API |
| 部门管理 | 数据库已设计，未实现 | `departments` 表已建，无管理界面和 API |
| 用户-客户数据隔离 | 数据库已设计，部分实现 | `user_customers` 表已建，业务员只能看自己客户的文件 |
| 企微/钉钉/邮件通知推送 | 配置已预留，未实现 | `system_configs` 中有 webhook 配置项，实际推送未接入 |

---

## 12. 项目目录结构

```
business_file_management/
├── tradedoc/                       # Laravel 主项目
│   ├── .env                        # 环境配置（部署需修改）
│   ├── .rr.yaml.bak                # 旧 RoadRunner 配置（已弃用）
│   ├── app/
│   │   ├── Http/Controllers/Api/   # API 控制器
│   │   ├── Models/                 # Eloquent 模型
│   │   ├── Services/               # 业务服务层
│   │   └── Exports/                # Excel 导出类
│   ├── bootstrap/cache/            # Laravel 启动缓存（部署后会有 config.php、routes.php）
│   ├── config/                     # 配置文件
│   ├── database/migrations/        # 迁移文件（生产环境不用，靠 SQL 脚本）
│   ├── public/                     # Web 入口（Nginx root 指这里）
│   │   ├── index.php
│   │   └── build/                  # Vite 编译产物
│   ├── resources/js/               # Vue 前端源码
│   ├── routes/api.php              # API 路由
│   ├── storage/                    # 文件存储 + 日志
│   │   ├── app/private/documents/  # 上传文件
│   │   └── logs/laravel.log        # Laravel 日志
│   └── vendor/                     # Composer 依赖（已打包，约 1GB）
│
├── tradedoc-python/                # Python OCR 服务（可选）
│   ├── .env                        # OCR 配置
│   └── app/
│       ├── api/main.py             # FastAPI 入口
│       └── services/ocr/           # OCR 引擎
│           ├── engine.py
│           ├── processor.py
│           └── text_extractor.py
│
├── database/                       # 数据库脚本
│   ├── install.sql                 # 主建表（含初始数据）
│   ├── fix_missing_tables.sql      # Laravel 内置表
│   ├── fix_spatie_tables.sql       # Spatie 权限表 + 数据
│   └── trade_doc_system.sql        # 原始建表（被 install.sql 包含）
│
├── deploy/                         # 部署相关
│   ├── README_DEPLOY.txt           # 部署指南
│   ├── nginx_tradedoc.conf         # Nginx 站点配置模板
│   └── server_install/             # PHP 安装包
│       ├── php-8.5.5-nts-Win32-vs17-x64.zip
│       ├── php.ini
│       └── INSTALL_PHP.txt
│
├── PROJECT_DOCS.md                 # 本文档
├── start.bat                       # 启动 Python OCR
└── stop.bat                        # 停止 Python OCR
```

---

## 附 A：支持的文件类型

| 编码 | 中文名 | 英文名 | 编号前缀 |
|------|--------|--------|----------|
| customs_declaration | 报关单 | Customs Declaration | D |
| commercial_invoice | 商业发票 | Commercial Invoice | INV |
| packing_list | 装箱单 | Packing List | PL |
| bank_receipt | 银行水单 | Bank Receipt | BK |
| bill_of_lading | 提单/运单 | Bill of Lading | BL |
| certificate_of_origin | 原产地证 | Certificate of Origin | CO |
| contract | 合同协议 | Contract | CT |
| letter_of_credit | 信用证 | Letter of Credit | LC |
| other | 其他文件 | Other Documents | DOC |

> 文件编号格式：`{前缀}{YYMMDD}-{4位序号}`，例：`D260428-0001`

---

## 附 B：API 调用示例（以登录为例）

```bash
# 1. 登录获取 token
curl -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# 响应:
# {"data":{"token":"1|abc...","user":{"id":1,"username":"admin",...}}}

# 2. 用 token 调其他接口
curl http://127.0.0.1:8000/api/v1/documents/statistics \
  -H "Authorization: Bearer 1|abc..." \
  -H "Accept: application/json"
```

---

## 附 C：变更历史

| 日期 | 版本 | 变更内容 |
|------|------|----------|
| 2026-04-09 | v1 | 初始版本 |
| 2026-04-28 | v2 | - 架构从 RoadRunner/Octane 切换到 phpStudy + PHP-CGI<br>- 数据库从 22 张表更新为 37 张（增加 Spatie + Laravel 内置表）<br>- 增加默认账号 admin/admin123<br>- 重写部署章节，新增运维与故障排查<br>- 增加 PHP 8.5 安装包、Nginx 配置模板等部署文件 |
