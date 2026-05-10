-- v3 增量迁移：GitHub 项目深挖功能
-- 用途：已有 v1/v2 数据库的同学执行此脚本升级，无需清库
-- 适用：拉取本分支后各自跑一次
--
-- MySQL 8.0 的 ADD COLUMN 不支持 IF NOT EXISTS，这里用 procedure 判断后再加

USE interview_echo;

DROP PROCEDURE IF EXISTS interview_echo_v3_add_columns;

DELIMITER $$
CREATE PROCEDURE interview_echo_v3_add_columns()
BEGIN
    -- repo_context
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'interviews'
          AND COLUMN_NAME = 'repo_context'
    ) THEN
        ALTER TABLE interviews ADD COLUMN repo_context TEXT NULL;
    END IF;

    -- custom_questions
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'interviews'
          AND COLUMN_NAME = 'custom_questions'
    ) THEN
        ALTER TABLE interviews ADD COLUMN custom_questions TEXT NULL;
    END IF;
END$$
DELIMITER ;

CALL interview_echo_v3_add_columns();
DROP PROCEDURE interview_echo_v3_add_columns;
