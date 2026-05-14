-- ============================================================
-- 修复 Spatie Permission - roles/permissions 表缺 guard_name 列
-- ============================================================
-- 背景：旧版 install.sql 创建的 roles/permissions 表是自研结构，
--       不含 Spatie Permission 必需的 guard_name 列。
--       系统升级后 Spatie 强制查询 guard_name，导致用户管理 500。
--
-- 兼容性：可重复执行（用存储过程检查列是否存在）
-- 执行方式：mysql -uroot -p tradedoc < fix_spatie_guard_name.sql
-- ============================================================

USE `tradedoc`;

DROP PROCEDURE IF EXISTS fix_spatie_guard_name;
DELIMITER //
CREATE PROCEDURE fix_spatie_guard_name()
BEGIN
  -- 1. roles.guard_name
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = DATABASE() AND table_name = 'roles' AND column_name = 'guard_name'
  ) THEN
    ALTER TABLE `roles` ADD COLUMN `guard_name` VARCHAR(125) NOT NULL DEFAULT 'web' AFTER `name`;
  END IF;

  -- 2. permissions.guard_name
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = DATABASE() AND table_name = 'permissions' AND column_name = 'guard_name'
  ) THEN
    ALTER TABLE `permissions` ADD COLUMN `guard_name` VARCHAR(125) NOT NULL DEFAULT 'web' AFTER `name`;
  END IF;
END //
DELIMITER ;

CALL fix_spatie_guard_name();
DROP PROCEDURE fix_spatie_guard_name;

-- 填补现有数据
UPDATE `roles` SET `guard_name` = 'web' WHERE `guard_name` IS NULL OR `guard_name` = '';
UPDATE `permissions` SET `guard_name` = 'web' WHERE `guard_name` IS NULL OR `guard_name` = '';

-- 验证（这两个 SELECT 在 mysql 客户端会输出结果）
SELECT id, name, guard_name FROM `roles`;
SELECT COUNT(*) AS permission_count FROM `permissions`;
