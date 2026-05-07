-- ============================================================
-- 贸易云档 - 补建 Spatie Permission 包用的表 + 数据
-- 用法: 在 phpMyAdmin/Navicat 选中 tradedoc 库后执行
-- ============================================================

USE `tradedoc`;

-- ============================================================
-- 1. 三张 pivot 表（Spatie Permission 必需）
-- ============================================================

CREATE TABLE IF NOT EXISTS `model_has_roles` (
  `role_id` INT UNSIGNED NOT NULL,
  `model_type` VARCHAR(255) NOT NULL,
  `model_id` BIGINT UNSIGNED NOT NULL,
  PRIMARY KEY (`role_id`, `model_id`, `model_type`),
  KEY `model_has_roles_model_idx` (`model_id`, `model_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `model_has_permissions` (
  `permission_id` INT UNSIGNED NOT NULL,
  `model_type` VARCHAR(255) NOT NULL,
  `model_id` BIGINT UNSIGNED NOT NULL,
  PRIMARY KEY (`permission_id`, `model_id`, `model_type`),
  KEY `model_has_permissions_model_idx` (`model_id`, `model_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `role_has_permissions` (
  `permission_id` INT UNSIGNED NOT NULL,
  `role_id` INT UNSIGNED NOT NULL,
  PRIMARY KEY (`permission_id`, `role_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 2. 把 admin 用户绑到 super_admin 角色（role_id=1）
-- ============================================================
INSERT IGNORE INTO `model_has_roles` (`role_id`, `model_id`, `model_type`)
VALUES (1, 1, 'App\\Models\\User');

-- ============================================================
-- 3. 角色权限映射（从开发机 dump 出的 52 条）
--    role_id 1=super_admin / 2=manager / 3=salesman / 4=doc_clerk / 5=finance / 6=readonly
-- ============================================================
INSERT IGNORE INTO `role_has_permissions` (`permission_id`, `role_id`) VALUES
-- super_admin (role 1): 所有 18 个权限
(1,1),(2,1),(3,1),(4,1),(5,1),(6,1),(7,1),(8,1),(9,1),
(10,1),(11,1),(12,1),(13,1),(14,1),(15,1),(16,1),(17,1),(18,1),
-- manager (role 2)
(1,2),(2,2),(3,2),(5,2),(6,2),(7,2),(10,2),(11,2),(12,2),(13,2),(14,2),(17,2),
-- salesman (role 3)
(1,3),(2,3),(3,3),(5,3),(6,3),(10,3),(12,3),(14,3),
-- doc_clerk (role 4)
(1,4),(2,4),(3,4),(8,4),(9,4),(14,4),
-- finance (role 5)
(1,5),(2,5),(5,5),(6,5),(12,5),(13,5),(14,5),
-- readonly (role 6)
(2,6);

-- ============================================================
-- 验证
-- ============================================================
SELECT 'tables_check' AS info;
SHOW TABLES LIKE 'model_has_%';
SHOW TABLES LIKE 'role_has_%';

SELECT 'admin_role' AS info;
SELECT mhr.*, r.name AS role_name
FROM model_has_roles mhr
JOIN roles r ON r.id = mhr.role_id
WHERE mhr.model_id = 1;

SELECT 'permissions_count_per_role' AS info;
SELECT r.name, COUNT(rhp.permission_id) AS perm_count
FROM roles r
LEFT JOIN role_has_permissions rhp ON rhp.role_id = r.id
GROUP BY r.id, r.name;
