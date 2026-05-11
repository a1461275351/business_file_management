-- ============================================================
-- PDF 拆分功能支持 (v2.1)
-- ============================================================
-- 用途：让一份混合 PDF（含报关单 + 提单 + 装箱单等多种单证）
--       可以被自动拆分成多个独立子文档，父子关系通过 parent_document_id 关联
--
-- 执行方式：在 MySQL 中导入此 SQL
-- 兼容性：可重复执行
-- ============================================================

USE `tradedoc`;

-- 用存储过程兼容"列已存在则跳过"
DROP PROCEDURE IF EXISTS apply_split_columns;
DELIMITER //
CREATE PROCEDURE apply_split_columns()
BEGIN
  -- 1. parent_document_id
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = DATABASE() AND table_name = 'documents' AND column_name = 'parent_document_id'
  ) THEN
    ALTER TABLE `documents`
      ADD COLUMN `parent_document_id` int unsigned DEFAULT NULL
        COMMENT '父文档 ID。NULL=顶层；非NULL=拆分子文档' AFTER `customer_id`;
  END IF;

  -- 2. split_page_range
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = DATABASE() AND table_name = 'documents' AND column_name = 'split_page_range'
  ) THEN
    ALTER TABLE `documents`
      ADD COLUMN `split_page_range` varchar(50) DEFAULT NULL
        COMMENT '子文档对应父文档的页范围 例: "1-2"' AFTER `parent_document_id`;
  END IF;

  -- 3. is_split_container
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = DATABASE() AND table_name = 'documents' AND column_name = 'is_split_container'
  ) THEN
    ALTER TABLE `documents`
      ADD COLUMN `is_split_container` tinyint(1) DEFAULT 0
        COMMENT '是否为拆分容器(父文档)。1=是，原文件无字段提取仅作归档' AFTER `split_page_range`;
  END IF;

  -- 4. idx_parent_document 索引
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.statistics
    WHERE table_schema = DATABASE() AND table_name = 'documents' AND index_name = 'idx_parent_document'
  ) THEN
    ALTER TABLE `documents` ADD INDEX `idx_parent_document` (`parent_document_id`);
  END IF;
END //
DELIMITER ;

CALL apply_split_columns();
DROP PROCEDURE apply_split_columns;
