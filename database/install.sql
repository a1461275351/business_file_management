-- ============================================================
-- 贸易云档 TradeDoc - 一键安装脚本
-- 用法: 在 phpMyAdmin / Navicat / 命令行 中直接执行本文件
-- 执行前: MySQL 服务已启动，root 密码已知
-- 执行后: 自动创建 tradedoc 数据库 + 全部表 + 初始数据
-- ============================================================

CREATE DATABASE IF NOT EXISTS `tradedoc`
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_unicode_ci;

USE `tradedoc`;

-- ============================================================
-- 外贸文件智能管理系统 — 数据库设计 v1.0
-- TradeDoc Intelligence Platform — Database Schema
-- 技术栈: MySQL 8.0 + Laravel (PHP) + FastAPI (Python)
-- 字符集: utf8mb4  排序规则: utf8mb4_unicode_ci
-- ============================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ============================================================
-- 一、用户与权限模块
-- ============================================================

-- 1.1 部门表
CREATE TABLE `departments` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `parent_id` int unsigned DEFAULT NULL COMMENT '上级部门ID，NULL为顶级',
  `name` varchar(100) NOT NULL COMMENT '部门名称',
  `code` varchar(50) DEFAULT NULL COMMENT '部门编码',
  `sort_order` smallint unsigned DEFAULT 0 COMMENT '排序权重',
  `status` tinyint unsigned DEFAULT 1 COMMENT '1=启用 0=停用',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_parent` (`parent_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='部门表';

-- 1.2 用户表
CREATE TABLE `users` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `username` varchar(50) NOT NULL COMMENT '登录用户名',
  `password` varchar(255) NOT NULL COMMENT '密码(bcrypt)',
  `real_name` varchar(50) NOT NULL COMMENT '真实姓名',
  `email` varchar(100) DEFAULT NULL,
  `phone` varchar(20) DEFAULT NULL,
  `department_id` int unsigned DEFAULT NULL COMMENT '所属部门',
  `avatar` varchar(255) DEFAULT NULL COMMENT '头像路径',
  `status` tinyint unsigned DEFAULT 1 COMMENT '1=正常 0=禁用',
  `last_login_at` timestamp NULL DEFAULT NULL,
  `last_login_ip` varchar(45) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_username` (`username`),
  UNIQUE KEY `uk_email` (`email`),
  KEY `idx_department` (`department_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- 1.3 角色表
CREATE TABLE `roles` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL COMMENT '角色标识: super_admin/manager/salesman/doc_clerk/finance/readonly',
  `display_name` varchar(50) NOT NULL COMMENT '显示名称',
  `description` varchar(200) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='角色表';

-- 1.4 权限表
CREATE TABLE `permissions` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL COMMENT '权限标识: document.upload / document.delete ...',
  `display_name` varchar(100) NOT NULL,
  `module` varchar(50) DEFAULT NULL COMMENT '所属模块: document/approval/report/system',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='权限表';

-- 1.5 角色-权限关联
CREATE TABLE `role_permissions` (
  `role_id` int unsigned NOT NULL,
  `permission_id` int unsigned NOT NULL,
  PRIMARY KEY (`role_id`, `permission_id`),
  KEY `idx_permission` (`permission_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='角色权限关联表';

-- 1.6 用户-角色关联
CREATE TABLE `user_roles` (
  `user_id` int unsigned NOT NULL,
  `role_id` int unsigned NOT NULL,
  PRIMARY KEY (`user_id`, `role_id`),
  KEY `idx_role` (`role_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户角色关联表';

-- 1.7 用户-客户负责关系（数据隔离用）
CREATE TABLE `user_customers` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `user_id` int unsigned NOT NULL,
  `customer_id` int unsigned NOT NULL,
  `assigned_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_customer` (`user_id`, `customer_id`),
  KEY `idx_customer` (`customer_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户-客户负责关系表';


-- ============================================================
-- 二、客户与供应商模块
-- ============================================================

-- 2.1 客户/供应商表
CREATE TABLE `customers` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `type` enum('customer','supplier','both') NOT NULL DEFAULT 'customer' COMMENT '类型',
  `company_name` varchar(200) NOT NULL COMMENT '公司名称',
  `company_name_en` varchar(200) DEFAULT NULL COMMENT '英文名称',
  `short_name` varchar(50) DEFAULT NULL COMMENT '简称',
  `country` varchar(50) DEFAULT NULL COMMENT '国家',
  `contact_person` varchar(50) DEFAULT NULL COMMENT '联系人',
  `contact_phone` varchar(50) DEFAULT NULL,
  `contact_email` varchar(100) DEFAULT NULL,
  `address` varchar(500) DEFAULT NULL,
  `bank_name` varchar(200) DEFAULT NULL COMMENT '开户行',
  `bank_account` varchar(100) DEFAULT NULL COMMENT '银行账号',
  `swift_code` varchar(20) DEFAULT NULL,
  `tax_id` varchar(50) DEFAULT NULL COMMENT '税号',
  `remarks` text DEFAULT NULL,
  `status` tinyint unsigned DEFAULT 1 COMMENT '1=正常 0=停用',
  `created_by` int unsigned DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_company_name` (`company_name`),
  KEY `idx_country` (`country`),
  FULLTEXT KEY `ft_company` (`company_name`, `company_name_en`, `short_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='客户/供应商表';


-- ============================================================
-- 三、订单模块（文件关联的业务主线）
-- ============================================================

-- 3.1 订单表
CREATE TABLE `orders` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `order_no` varchar(50) NOT NULL COMMENT '订单号 如 SO-8820',
  `order_type` enum('export','import') NOT NULL DEFAULT 'export' COMMENT '进/出口',
  `customer_id` int unsigned DEFAULT NULL,
  `total_amount` decimal(15,2) DEFAULT NULL COMMENT '订单金额',
  `currency` varchar(10) DEFAULT 'USD',
  `trade_terms` varchar(20) DEFAULT NULL COMMENT '贸易条款: FOB/CIF/EXW...',
  `payment_terms` varchar(100) DEFAULT NULL COMMENT '付款条款: T/T 30days...',
  `destination_country` varchar(50) DEFAULT NULL COMMENT '目的国',
  `port_of_loading` varchar(100) DEFAULT NULL COMMENT '装货港',
  `port_of_discharge` varchar(100) DEFAULT NULL COMMENT '卸货港',
  `status` enum('draft','confirmed','shipping','completed','cancelled') DEFAULT 'draft',
  `assigned_to` int unsigned DEFAULT NULL COMMENT '负责业务员',
  `remarks` text DEFAULT NULL,
  `created_by` int unsigned DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_order_no` (`order_no`),
  KEY `idx_customer` (`customer_id`),
  KEY `idx_assigned_to` (`assigned_to`),
  KEY `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='订单表';


-- ============================================================
-- 四、文件管理模块（核心）
-- ============================================================

-- 4.1 文件类型字典
CREATE TABLE `document_types` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `code` varchar(30) NOT NULL COMMENT '类型编码: customs_declaration / commercial_invoice / packing_list / bank_receipt / bill_of_lading / certificate_of_origin / contract / letter_of_credit / other',
  `name` varchar(50) NOT NULL COMMENT '中文名: 报关单 / 商业发票...',
  `name_en` varchar(50) DEFAULT NULL COMMENT '英文名',
  `icon` varchar(10) DEFAULT NULL COMMENT '图标emoji',
  `color` varchar(20) DEFAULT NULL COMMENT '标签颜色: blue/green/amber/gray/coral',
  `sort_order` smallint unsigned DEFAULT 0,
  `status` tinyint unsigned DEFAULT 1,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_code` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='文件类型字典表';

-- 4.2 文件主表
CREATE TABLE `documents` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `doc_no` varchar(50) NOT NULL COMMENT '文件编号: D240701-0045',
  `document_type_id` int unsigned NOT NULL COMMENT '文件类型',
  `order_id` int unsigned DEFAULT NULL COMMENT '关联订单',
  `customer_id` int unsigned DEFAULT NULL COMMENT '关联客户/供应商',
  `title` varchar(200) DEFAULT NULL COMMENT '文件标题/描述',
  `original_filename` varchar(255) NOT NULL COMMENT '原始文件名',
  `storage_path` varchar(500) NOT NULL COMMENT '存储路径',
  `file_size` int unsigned DEFAULT NULL COMMENT '文件大小(字节)',
  `file_ext` varchar(10) DEFAULT NULL COMMENT '扩展名: pdf/jpg/png/xlsx/docx',
  `mime_type` varchar(100) DEFAULT NULL,
  `file_hash` varchar(64) DEFAULT NULL COMMENT 'SHA-256 去重校验',
  `total_amount` decimal(15,2) DEFAULT NULL COMMENT '金额(提取自文件)',
  `currency` varchar(10) DEFAULT NULL COMMENT '币种',
  `trade_date` date DEFAULT NULL COMMENT '业务日期(提取自文件)',
  `language` varchar(10) DEFAULT 'zh' COMMENT '文件语种: zh/en/ja/ko',
  `ocr_confidence` decimal(5,2) DEFAULT NULL COMMENT 'OCR整体置信度(%)',
  `field_complete_rate` decimal(5,2) DEFAULT NULL COMMENT '字段完整率(%)',
  `version` int unsigned DEFAULT 1 COMMENT '当前版本号',
  `status` enum('draft','ocr_processing','pending_review','pending_approval','approved','archived','voided') DEFAULT 'draft' COMMENT '文件状态',
  `uploaded_by` int unsigned NOT NULL COMMENT '上传人',
  `reviewed_by` int unsigned DEFAULT NULL COMMENT '核对人',
  `reviewed_at` timestamp NULL DEFAULT NULL,
  `approved_by` int unsigned DEFAULT NULL COMMENT '审批人',
  `approved_at` timestamp NULL DEFAULT NULL,
  `archived_at` timestamp NULL DEFAULT NULL COMMENT '归档时间',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `deleted_at` timestamp NULL DEFAULT NULL COMMENT '软删除',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_doc_no` (`doc_no`),
  KEY `idx_type` (`document_type_id`),
  KEY `idx_order` (`order_id`),
  KEY `idx_customer` (`customer_id`),
  KEY `idx_status` (`status`),
  KEY `idx_uploaded_by` (`uploaded_by`),
  KEY `idx_trade_date` (`trade_date`),
  KEY `idx_created_at` (`created_at`),
  KEY `idx_hash` (`file_hash`),
  FULLTEXT KEY `ft_doc` (`doc_no`, `title`, `original_filename`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='文件主表';

-- 4.3 文件版本表
CREATE TABLE `document_versions` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `document_id` int unsigned NOT NULL,
  `version` int unsigned NOT NULL COMMENT '版本号',
  `storage_path` varchar(500) NOT NULL COMMENT '该版本文件存储路径',
  `file_size` int unsigned DEFAULT NULL,
  `file_hash` varchar(64) DEFAULT NULL,
  `change_summary` varchar(500) DEFAULT NULL COMMENT '版本变更说明',
  `created_by` int unsigned NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_document` (`document_id`),
  UNIQUE KEY `uk_doc_version` (`document_id`, `version`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='文件版本表';

-- 4.4 文件关联表（同一票货的文件组）
CREATE TABLE `document_relations` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `document_id` int unsigned NOT NULL COMMENT '文件A',
  `related_document_id` int unsigned NOT NULL COMMENT '文件B',
  `relation_type` enum('same_order','reference','supersede') DEFAULT 'same_order' COMMENT '关联类型',
  `created_by` int unsigned DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_relation` (`document_id`, `related_document_id`),
  KEY `idx_related` (`related_document_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='文件关联表';

-- 4.5 文件标签表
CREATE TABLE `document_tags` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `document_id` int unsigned NOT NULL,
  `tag` varchar(50) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_document` (`document_id`),
  KEY `idx_tag` (`tag`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='文件标签表';


-- ============================================================
-- 五、字段提取模块（OCR / NLP 结果）
-- ============================================================

-- 5.1 字段模板定义
CREATE TABLE `field_templates` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `document_type_id` int unsigned NOT NULL COMMENT '关联文件类型',
  `field_key` varchar(50) NOT NULL COMMENT '字段标识: declaration_no / trade_amount ...',
  `field_name` varchar(50) NOT NULL COMMENT '字段中文名: 报关单号',
  `field_name_en` varchar(50) DEFAULT NULL COMMENT '字段英文名',
  `field_type` enum('string','integer','decimal','date','enum','text') NOT NULL DEFAULT 'string',
  `is_required` tinyint unsigned DEFAULT 0 COMMENT '是否必填',
  `is_auto_extract` tinyint unsigned DEFAULT 1 COMMENT '是否自动提取',
  `extract_rule` varchar(500) DEFAULT NULL COMMENT '提取规则(正则/模板路径)',
  `validation_rule` varchar(500) DEFAULT NULL COMMENT '校验规则',
  `enum_options` json DEFAULT NULL COMMENT '枚举选项(field_type=enum时)',
  `sort_order` smallint unsigned DEFAULT 0,
  `status` tinyint unsigned DEFAULT 1,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_type_field` (`document_type_id`, `field_key`),
  KEY `idx_type` (`document_type_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='字段提取模板表';

-- 5.2 文件提取字段值
CREATE TABLE `document_fields` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `document_id` int unsigned NOT NULL,
  `field_template_id` int unsigned NOT NULL COMMENT '关联模板字段',
  `field_key` varchar(50) NOT NULL COMMENT '冗余字段标识(查询方便)',
  `field_value` text DEFAULT NULL COMMENT '提取值',
  `confidence` decimal(5,2) DEFAULT NULL COMMENT '置信度(%)',
  `extract_method` enum('auto_ocr','auto_nlp','manual','inferred') DEFAULT 'auto_ocr' COMMENT '提取方式',
  `bbox_info` json DEFAULT NULL COMMENT 'OCR定位信息 {page,x,y,w,h}',
  `is_confirmed` tinyint unsigned DEFAULT 0 COMMENT '是否已人工确认',
  `confirmed_by` int unsigned DEFAULT NULL,
  `confirmed_at` timestamp NULL DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_document` (`document_id`),
  KEY `idx_template` (`field_template_id`),
  KEY `idx_field_key` (`field_key`),
  KEY `idx_confidence` (`confidence`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='文件字段提取值表';


-- ============================================================
-- 六、OCR 任务队列
-- ============================================================

CREATE TABLE `ocr_tasks` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `document_id` int unsigned NOT NULL,
  `task_type` enum('ocr','nlp_extract','data_clean','cross_check') DEFAULT 'ocr',
  `status` enum('pending','processing','completed','failed','retry') DEFAULT 'pending',
  `priority` tinyint unsigned DEFAULT 5 COMMENT '1-10, 数字越小优先级越高',
  `retry_count` tinyint unsigned DEFAULT 0,
  `max_retries` tinyint unsigned DEFAULT 3,
  `started_at` timestamp NULL DEFAULT NULL,
  `completed_at` timestamp NULL DEFAULT NULL,
  `result_summary` json DEFAULT NULL COMMENT '处理结果摘要 {confidence, fields_extracted, ...}',
  `error_message` text DEFAULT NULL,
  `worker_id` varchar(50) DEFAULT NULL COMMENT '处理该任务的worker标识',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_document` (`document_id`),
  KEY `idx_status_priority` (`status`, `priority`),
  KEY `idx_type` (`task_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='OCR/NLP处理任务队列';


-- ============================================================
-- 七、审批与工作流模块
-- ============================================================

-- 7.1 审批规则配置
CREATE TABLE `approval_rules` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL COMMENT '规则名称',
  `description` varchar(500) DEFAULT NULL,
  `trigger_type` enum('archive','void','field_edit','amount_exceed') NOT NULL COMMENT '触发类型',
  `condition_config` json DEFAULT NULL COMMENT '触发条件配置 {document_type, amount_threshold, ...}',
  `approval_levels` json NOT NULL COMMENT '审批层级配置 [{level:1, role:"manager"}, {level:2, role:"super_admin"}]',
  `timeout_hours` int unsigned DEFAULT 24 COMMENT '超时时间(小时)',
  `timeout_action` enum('remind','escalate','auto_approve') DEFAULT 'remind',
  `status` tinyint unsigned DEFAULT 1 COMMENT '1=启用 0=停用',
  `created_by` int unsigned DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='审批规则配置表';

-- 7.2 审批记录
CREATE TABLE `approval_records` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `document_id` int unsigned NOT NULL,
  `approval_rule_id` int unsigned DEFAULT NULL COMMENT '触发的审批规则',
  `current_level` tinyint unsigned DEFAULT 1 COMMENT '当前审批层级',
  `total_levels` tinyint unsigned DEFAULT 1 COMMENT '总审批层级数',
  `status` enum('pending','approved','rejected','cancelled','expired') DEFAULT 'pending',
  `submitted_by` int unsigned NOT NULL COMMENT '提交人',
  `submitted_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `completed_at` timestamp NULL DEFAULT NULL,
  `remarks` text DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_document` (`document_id`),
  KEY `idx_status` (`status`),
  KEY `idx_submitted_by` (`submitted_by`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='审批记录表';

-- 7.3 审批明细（每一级审批的结果）
CREATE TABLE `approval_details` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `approval_record_id` int unsigned NOT NULL,
  `level` tinyint unsigned NOT NULL COMMENT '审批层级',
  `approver_id` int unsigned NOT NULL COMMENT '审批人',
  `action` enum('approved','rejected') DEFAULT NULL,
  `comment` text DEFAULT NULL COMMENT '审批意见',
  `acted_at` timestamp NULL DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_record` (`approval_record_id`),
  KEY `idx_approver` (`approver_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='审批明细表';

-- 7.4 人工核对任务
CREATE TABLE `review_tasks` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `document_id` int unsigned NOT NULL,
  `field_ids` json DEFAULT NULL COMMENT '需核对的字段ID列表',
  `priority` enum('urgent','medium','normal') DEFAULT 'normal',
  `status` enum('pending','assigned','in_progress','completed','transferred') DEFAULT 'pending',
  `assigned_to` int unsigned DEFAULT NULL COMMENT '分配给的单证员',
  `assigned_at` timestamp NULL DEFAULT NULL,
  `started_at` timestamp NULL DEFAULT NULL,
  `completed_at` timestamp NULL DEFAULT NULL,
  `timeout_at` timestamp NULL DEFAULT NULL COMMENT '超时截止时间',
  `transferred_from` int unsigned DEFAULT NULL COMMENT '转派来源',
  `remarks` text DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_document` (`document_id`),
  KEY `idx_assigned_to` (`assigned_to`),
  KEY `idx_status` (`status`),
  KEY `idx_priority_status` (`priority`, `status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='人工核对任务表';


-- ============================================================
-- 八、通知与消息模块
-- ============================================================

-- 8.1 通知表
CREATE TABLE `notifications` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `user_id` int unsigned NOT NULL COMMENT '接收人',
  `type` varchar(50) NOT NULL COMMENT '通知类型: ocr_complete/review_assigned/approval_pending/anomaly_alert/timeout_warning',
  `title` varchar(200) NOT NULL,
  `content` text DEFAULT NULL,
  `priority` enum('normal','medium','urgent') DEFAULT 'normal',
  `related_type` varchar(50) DEFAULT NULL COMMENT '关联对象类型: document/approval/review_task',
  `related_id` int unsigned DEFAULT NULL COMMENT '关联对象ID',
  `channels` json DEFAULT NULL COMMENT '推送渠道记录 ["internal","wechat_work","email"]',
  `is_read` tinyint unsigned DEFAULT 0,
  `read_at` timestamp NULL DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_user_read` (`user_id`, `is_read`),
  KEY `idx_type` (`type`),
  KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='通知表';

-- 8.2 用户通知偏好
CREATE TABLE `notification_settings` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `user_id` int unsigned NOT NULL,
  `notify_type` varchar(50) NOT NULL COMMENT '通知类型',
  `channel_internal` tinyint unsigned DEFAULT 1 COMMENT '站内信',
  `channel_wechat` tinyint unsigned DEFAULT 0 COMMENT '企微/钉钉',
  `channel_email` tinyint unsigned DEFAULT 0 COMMENT '邮件',
  `channel_sms` tinyint unsigned DEFAULT 0 COMMENT '短信',
  `is_enabled` tinyint unsigned DEFAULT 1 COMMENT '是否启用',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_type` (`user_id`, `notify_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='通知偏好设置表';


-- ============================================================
-- 九、操作日志与审计追踪模块
-- ============================================================

-- 9.1 操作日志（通用）
CREATE TABLE `operation_logs` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `user_id` int unsigned DEFAULT NULL COMMENT '操作人，NULL=系统自动',
  `module` varchar(30) NOT NULL COMMENT '模块: document/user/approval/system/ocr',
  `action` varchar(30) NOT NULL COMMENT '操作: upload/view/download/edit/delete/approve/reject/login/logout',
  `target_type` varchar(50) DEFAULT NULL COMMENT '操作对象类型: document/user/approval_rule',
  `target_id` int unsigned DEFAULT NULL COMMENT '操作对象ID',
  `description` varchar(500) DEFAULT NULL COMMENT '操作描述',
  `ip_address` varchar(45) DEFAULT NULL,
  `user_agent` varchar(300) DEFAULT NULL,
  `extra_data` json DEFAULT NULL COMMENT '附加数据(如修改前后值)',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_user` (`user_id`),
  KEY `idx_module_action` (`module`, `action`),
  KEY `idx_target` (`target_type`, `target_id`),
  KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='操作日志表';

-- 9.2 字段变更历史（细粒度审计）
CREATE TABLE `field_change_logs` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `document_id` int unsigned NOT NULL,
  `document_field_id` bigint unsigned NOT NULL,
  `field_key` varchar(50) NOT NULL,
  `old_value` text DEFAULT NULL,
  `new_value` text DEFAULT NULL,
  `change_reason` varchar(200) DEFAULT NULL COMMENT '修改原因',
  `changed_by` int unsigned NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_document` (`document_id`),
  KEY `idx_field` (`document_field_id`),
  KEY `idx_changed_by` (`changed_by`),
  KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='字段变更历史表';


-- ============================================================
-- 十、数据管道与质量监控
-- ============================================================

-- 10.1 数据管道处理日志
CREATE TABLE `pipeline_logs` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `document_id` int unsigned NOT NULL,
  `stage` enum('upload','ocr','nlp_extract','data_clean','cross_check','warehouse','model_feed') NOT NULL,
  `status` enum('success','warning','failed','skipped') NOT NULL,
  `input_summary` json DEFAULT NULL COMMENT '输入摘要',
  `output_summary` json DEFAULT NULL COMMENT '输出摘要 {fields_count, confidence_avg, ...}',
  `warnings` json DEFAULT NULL COMMENT '警告信息列表',
  `error_message` text DEFAULT NULL,
  `duration_ms` int unsigned DEFAULT NULL COMMENT '处理耗时(毫秒)',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_document` (`document_id`),
  KEY `idx_stage` (`stage`),
  KEY `idx_status` (`status`),
  KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='数据管道处理日志';

-- 10.2 跨文件异常告警
CREATE TABLE `anomaly_alerts` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `alert_type` enum('amount_mismatch','quantity_mismatch','missing_relation','duplicate_doc','hs_code_invalid','field_empty') NOT NULL,
  `severity` enum('low','medium','high') DEFAULT 'medium',
  `document_id` int unsigned NOT NULL COMMENT '主文件',
  `related_document_id` int unsigned DEFAULT NULL COMMENT '对比文件',
  `order_id` int unsigned DEFAULT NULL,
  `description` varchar(500) NOT NULL COMMENT '异常描述',
  `detail_data` json DEFAULT NULL COMMENT '差异详情 {field, value_a, value_b, diff_amount}',
  `status` enum('open','confirmed','resolved','ignored') DEFAULT 'open',
  `resolved_by` int unsigned DEFAULT NULL,
  `resolved_at` timestamp NULL DEFAULT NULL,
  `resolve_comment` text DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_document` (`document_id`),
  KEY `idx_order` (`order_id`),
  KEY `idx_type_status` (`alert_type`, `status`),
  KEY `idx_severity` (`severity`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='跨文件异常告警表';


-- ============================================================
-- 十一、系统配置
-- ============================================================

-- 11.1 系统配置表
CREATE TABLE `system_configs` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `config_group` varchar(50) NOT NULL COMMENT '配置组: general/ocr/notification/email/security',
  `config_key` varchar(100) NOT NULL,
  `config_value` text DEFAULT NULL,
  `value_type` enum('string','integer','boolean','json') DEFAULT 'string',
  `description` varchar(200) DEFAULT NULL,
  `updated_by` int unsigned DEFAULT NULL,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_group_key` (`config_group`, `config_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='系统配置表';

-- 11.2 邮箱绑定配置（自动采集邮件附件）
CREATE TABLE `email_configs` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `email_address` varchar(100) NOT NULL COMMENT '邮箱地址',
  `imap_host` varchar(100) NOT NULL,
  `imap_port` smallint unsigned DEFAULT 993,
  `imap_encryption` enum('ssl','tls','none') DEFAULT 'ssl',
  `username` varchar(100) NOT NULL,
  `password_encrypted` varchar(500) NOT NULL COMMENT '加密存储的密码',
  `auto_collect` tinyint unsigned DEFAULT 1 COMMENT '是否自动采集附件',
  `collect_rules` json DEFAULT NULL COMMENT '采集规则 {sender_filter, subject_filter, ...}',
  `last_sync_at` timestamp NULL DEFAULT NULL,
  `status` tinyint unsigned DEFAULT 1,
  `created_by` int unsigned DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='邮箱绑定配置表';


-- ============================================================
-- 十二、初始化数据
-- ============================================================

-- 文件类型
INSERT INTO `document_types` (`code`, `name`, `name_en`, `icon`, `color`, `sort_order`) VALUES
('customs_declaration', '报关单', 'Customs Declaration', '🗂️', 'blue', 1),
('commercial_invoice', '商业发票', 'Commercial Invoice', '🧾', 'green', 2),
('packing_list', '装箱单', 'Packing List', '📦', 'amber', 3),
('bank_receipt', '银行水单', 'Bank Receipt', '🏦', 'gray', 4),
('bill_of_lading', '提单/运单', 'Bill of Lading', '🚢', 'coral', 5),
('certificate_of_origin', '原产地证', 'Certificate of Origin', '🌍', 'green', 6),
('contract', '合同协议', 'Contract', '📝', 'gray', 7),
('letter_of_credit', '信用证', 'Letter of Credit', '💳', 'blue', 8),
('other', '其他文件', 'Other Documents', '📄', 'gray', 99);

-- 角色
INSERT INTO `roles` (`name`, `display_name`, `description`) VALUES
('super_admin', '超级管理员', '全部功能与系统配置权限'),
('manager', '业务主管', '部门文件管理、审批、报表导出'),
('salesman', '业务员', '上传与管理自己负责客户的文件'),
('doc_clerk', '单证员', 'OCR核对、字段修正、文件关联'),
('finance', '财务人员', '查看银行水单/发票、导出财务数据'),
('readonly', '只读访客', '仅查看授权范围内文件');

-- 权限
INSERT INTO `permissions` (`name`, `display_name`, `module`) VALUES
('document.upload', '上传文件', 'document'),
('document.view', '查看文件', 'document'),
('document.edit', '编辑文件字段', 'document'),
('document.delete', '删除/作废文件', 'document'),
('document.download', '下载文件原件', 'document'),
('document.export', '导出数据', 'document'),
('document.batch', '批量操作', 'document'),
('review.list', '查看核对队列', 'review'),
('review.execute', '执行核对操作', 'review'),
('approval.submit', '提交审批', 'approval'),
('approval.approve', '审批文件', 'approval'),
('report.view', '查看报表', 'report'),
('report.export', '导出报表', 'report'),
('ai.query', 'AI智能问答', 'ai'),
('system.config', '系统设置', 'system'),
('system.user_manage', '用户管理', 'system'),
('system.audit_log', '审计日志', 'system'),
('notification.manage', '通知管理', 'system');

-- 超级管理员赋予全部权限
INSERT INTO `role_permissions` (`role_id`, `permission_id`)
SELECT 1, id FROM `permissions`;

-- 业务主管权限
INSERT INTO `role_permissions` (`role_id`, `permission_id`)
SELECT 2, id FROM `permissions` WHERE `name` IN (
  'document.upload','document.view','document.edit','document.download','document.export','document.batch',
  'approval.submit','approval.approve','report.view','report.export','ai.query','system.audit_log'
);

-- 业务员权限
INSERT INTO `role_permissions` (`role_id`, `permission_id`)
SELECT 3, id FROM `permissions` WHERE `name` IN (
  'document.upload','document.view','document.edit','document.download','document.export',
  'approval.submit','report.view','ai.query'
);

-- 单证员权限
INSERT INTO `role_permissions` (`role_id`, `permission_id`)
SELECT 4, id FROM `permissions` WHERE `name` IN (
  'document.upload','document.view','document.edit',
  'review.list','review.execute','ai.query'
);

-- 财务权限
INSERT INTO `role_permissions` (`role_id`, `permission_id`)
SELECT 5, id FROM `permissions` WHERE `name` IN (
  'document.upload','document.view','document.download','document.export',
  'report.view','report.export','ai.query'
);

-- 只读权限
INSERT INTO `role_permissions` (`role_id`, `permission_id`)
SELECT 6, id FROM `permissions` WHERE `name` IN ('document.view');

-- 报关单字段模板
INSERT INTO `field_templates` (`document_type_id`, `field_key`, `field_name`, `field_name_en`, `field_type`, `is_required`, `is_auto_extract`, `sort_order`) VALUES
(1, 'declaration_no', '报关单号', 'Declaration No.', 'string', 1, 1, 1),
(1, 'customs_code', '海关编号', 'Customs Code', 'string', 0, 1, 2),
(1, 'declare_date', '申报日期', 'Declaration Date', 'date', 1, 1, 3),
(1, 'hs_code', 'HS编码', 'HS Code', 'string', 1, 1, 4),
(1, 'goods_name', '货物名称', 'Goods Name', 'string', 1, 1, 5),
(1, 'trade_amount', '成交金额', 'Trade Amount', 'decimal', 1, 1, 6),
(1, 'currency', '币种', 'Currency', 'string', 1, 1, 7),
(1, 'trade_mode', '贸易方式', 'Trade Mode', 'enum', 1, 1, 8),
(1, 'transport_mode', '运输方式', 'Transport Mode', 'enum', 0, 1, 9),
(1, 'destination_country', '目的国', 'Destination', 'string', 0, 1, 10),
(1, 'supervision_condition', '监管条件', 'Supervision', 'string', 0, 0, 11),
(1, 'company_name', '经营单位', 'Company', 'string', 0, 1, 12);

-- 商业发票字段模板
INSERT INTO `field_templates` (`document_type_id`, `field_key`, `field_name`, `field_name_en`, `field_type`, `is_required`, `is_auto_extract`, `sort_order`) VALUES
(2, 'invoice_no', '发票号', 'Invoice No.', 'string', 1, 1, 1),
(2, 'invoice_date', '开票日期', 'Invoice Date', 'date', 1, 1, 2),
(2, 'seller', '卖方', 'Seller', 'string', 1, 1, 3),
(2, 'buyer', '买方', 'Buyer', 'string', 1, 1, 4),
(2, 'goods_description', '商品描述', 'Goods Description', 'text', 1, 1, 5),
(2, 'unit_price', '单价', 'Unit Price', 'decimal', 0, 1, 6),
(2, 'total_amount', '总金额', 'Total Amount', 'decimal', 1, 1, 7),
(2, 'currency', '币种', 'Currency', 'string', 1, 1, 8),
(2, 'payment_terms', '付款条件', 'Payment Terms', 'string', 0, 1, 9),
(2, 'trade_terms', '贸易条款', 'Trade Terms', 'string', 0, 1, 10);

-- 装箱单字段模板
INSERT INTO `field_templates` (`document_type_id`, `field_key`, `field_name`, `field_name_en`, `field_type`, `is_required`, `is_auto_extract`, `sort_order`) VALUES
(3, 'packing_no', '箱单号', 'Packing List No.', 'string', 1, 1, 1),
(3, 'total_packages', '总件数', 'Total Packages', 'integer', 1, 1, 2),
(3, 'total_quantity', '总数量', 'Total Quantity', 'integer', 0, 1, 3),
(3, 'gross_weight', '毛重(KG)', 'Gross Weight', 'decimal', 1, 1, 4),
(3, 'net_weight', '净重(KG)', 'Net Weight', 'decimal', 0, 1, 5),
(3, 'volume_cbm', '体积(CBM)', 'Volume', 'decimal', 0, 1, 6),
(3, 'shipping_marks', '唛头', 'Shipping Marks', 'text', 0, 0, 7),
(3, 'goods_description', '货物描述', 'Goods Description', 'text', 1, 1, 8);

-- 银行水单字段模板
INSERT INTO `field_templates` (`document_type_id`, `field_key`, `field_name`, `field_name_en`, `field_type`, `is_required`, `is_auto_extract`, `sort_order`) VALUES
(4, 'transaction_no', '流水号', 'Transaction No.', 'string', 1, 1, 1),
(4, 'transaction_date', '交易日期', 'Transaction Date', 'date', 1, 1, 2),
(4, 'amount', '金额', 'Amount', 'decimal', 1, 1, 3),
(4, 'currency', '币种', 'Currency', 'string', 1, 1, 4),
(4, 'exchange_rate', '汇率', 'Exchange Rate', 'decimal', 0, 1, 5),
(4, 'amount_cny', '折合人民币', 'Amount (CNY)', 'decimal', 0, 1, 6),
(4, 'counterparty', '对手方', 'Counterparty', 'string', 0, 1, 7),
(4, 'counterparty_account', '对手方账号', 'Account', 'string', 0, 1, 8),
(4, 'purpose', '用途', 'Purpose', 'string', 0, 1, 9);

-- 提单字段模板
INSERT INTO `field_templates` (`document_type_id`, `field_key`, `field_name`, `field_name_en`, `field_type`, `is_required`, `is_auto_extract`, `sort_order`) VALUES
(5, 'bl_no', '提单号', 'B/L No.', 'string', 1, 1, 1),
(5, 'carrier', '船公司/承运人', 'Carrier', 'string', 1, 1, 2),
(5, 'vessel_voyage', '船名航次', 'Vessel/Voyage', 'string', 0, 1, 3),
(5, 'port_of_loading', '装货港', 'Port of Loading', 'string', 1, 1, 4),
(5, 'port_of_discharge', '卸货港', 'Port of Discharge', 'string', 1, 1, 5),
(5, 'container_info', '箱型箱量', 'Container Info', 'string', 0, 1, 6),
(5, 'goods_description', '货物描述', 'Goods Description', 'text', 1, 1, 7),
(5, 'issue_date', '签发日期', 'Issue Date', 'date', 1, 1, 8),
(5, 'shipper', '发货人', 'Shipper', 'string', 0, 1, 9),
(5, 'consignee', '收货人', 'Consignee', 'string', 0, 1, 10),
(5, 'notify_party', '通知方', 'Notify Party', 'string', 0, 0, 11);

-- 默认系统配置
INSERT INTO `system_configs` (`config_group`, `config_key`, `config_value`, `value_type`, `description`) VALUES
('general', 'system_name', '贸易云档', 'string', '系统名称'),
('general', 'company_name', '杨凌国合跨境贸易有限公司', 'string', '公司名称'),
('general', 'file_upload_max_size', '52428800', 'integer', '文件上传大小限制(字节) 50MB'),
('general', 'file_storage_base_path', '/data/tradedoc/files', 'string', '文件存储根目录'),
('ocr', 'engine_type', 'paddleocr', 'string', 'OCR引擎: paddleocr/baidu_api/aliyun_api'),
('ocr', 'python_api_url', 'http://127.0.0.1:8100', 'string', 'Python FastAPI 服务地址'),
('ocr', 'confidence_threshold', '80', 'integer', '自动提取置信度阈值(%)，低于此值需人工核对'),
('ocr', 'auto_language_detect', '1', 'boolean', '是否自动检测文件语种'),
('notification', 'wechat_work_webhook', '', 'string', '企业微信机器人 Webhook URL'),
('notification', 'dingtalk_webhook', '', 'string', '钉钉机器人 Webhook URL'),
('notification', 'email_daily_digest', '1', 'boolean', '是否发送每日待办汇总邮件'),
('security', 'login_max_attempts', '5', 'integer', '登录失败最大尝试次数'),
('security', 'login_lockout_minutes', '30', 'integer', '锁定时长(分钟)'),
('security', 'session_lifetime_minutes', '120', 'integer', '会话有效期(分钟)'),
('security', 'watermark_enabled', '1', 'boolean', '是否启用文件预览水印');


SET FOREIGN_KEY_CHECKS = 1;
