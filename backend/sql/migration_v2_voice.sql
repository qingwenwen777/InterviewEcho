-- v2 增量迁移：表达分析模块
-- 用途：已有 v1 数据库的同学执行此脚本升级，无需清库
-- 适用：A、B 拉取本分支后各自跑一次

USE interview_echo;

-- 1. evaluations 表新增三维子分
-- ALTER TABLE evaluations
    -- ADD COLUMN speech_rate_score FLOAT DEFAULT 0.0,
    -- ADD COLUMN clarity_score FLOAT DEFAULT 0.0,
    -- ADD COLUMN confidence_score FLOAT DEFAULT 0.0;

-- 2. 新建 voice_metrics 表
CREATE TABLE IF NOT EXISTS voice_metrics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    interview_id INT NOT NULL,
    message_id INT NOT NULL,
    duration_sec FLOAT,
    wpm FLOAT,
    pause_ratio FLOAT,
    long_pause_count INT DEFAULT 0,
    filler_total INT DEFAULT 0,
    pitch_mean FLOAT,
    pitch_std FLOAT,
    volume_mean FLOAT,
    volume_std FLOAT,
    raw_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (interview_id) REFERENCES interviews(id) ON DELETE CASCADE,
    FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE,
    INDEX idx_interview (interview_id)
);
