-- v5: Structured interview message state for safer scheduling.
USE interview_echo;

DROP PROCEDURE IF EXISTS interview_echo_v5_message_state;
DELIMITER //
CREATE PROCEDURE interview_echo_v5_message_state()
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'messages'
          AND COLUMN_NAME = 'round_index'
    ) THEN
        ALTER TABLE messages ADD COLUMN round_index INT NULL AFTER category;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'messages'
          AND COLUMN_NAME = 'question_id'
    ) THEN
        ALTER TABLE messages ADD COLUMN question_id VARCHAR(160) NULL AFTER round_index;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'messages'
          AND COLUMN_NAME = 'parent_question_id'
    ) THEN
        ALTER TABLE messages ADD COLUMN parent_question_id INT NULL AFTER question_id;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'messages'
          AND COLUMN_NAME = 'action'
    ) THEN
        ALTER TABLE messages ADD COLUMN action VARCHAR(30) NULL AFTER parent_question_id;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'messages'
          AND COLUMN_NAME = 'source'
    ) THEN
        ALTER TABLE messages ADD COLUMN source VARCHAR(50) NULL AFTER action;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM INFORMATION_SCHEMA.STATISTICS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'messages'
          AND INDEX_NAME = 'idx_messages_round'
    ) THEN
        CREATE INDEX idx_messages_round ON messages (interview_id, round_index);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM INFORMATION_SCHEMA.STATISTICS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'messages'
          AND INDEX_NAME = 'idx_messages_question'
    ) THEN
        CREATE INDEX idx_messages_question ON messages (interview_id, question_id);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM INFORMATION_SCHEMA.STATISTICS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'messages'
          AND INDEX_NAME = 'idx_messages_parent'
    ) THEN
        CREATE INDEX idx_messages_parent ON messages (interview_id, parent_question_id);
    END IF;
END //
DELIMITER ;

CALL interview_echo_v5_message_state();
DROP PROCEDURE IF EXISTS interview_echo_v5_message_state;
