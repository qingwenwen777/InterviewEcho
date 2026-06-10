-- v4: Code practice module with self-hosted Judge0 submissions.
USE interview_echo;

CREATE TABLE IF NOT EXISTS code_problems (
    id INT PRIMARY KEY,
    title VARCHAR(120) NOT NULL,
    slug VARCHAR(120) NOT NULL UNIQUE,
    difficulty VARCHAR(20) NOT NULL,
    tags TEXT NOT NULL,
    description TEXT NOT NULL,
    input_format TEXT NOT NULL,
    output_format TEXT NOT NULL,
    samples TEXT NOT NULL,
    constraints TEXT NOT NULL,
    starter_code TEXT NOT NULL,
    source VARCHAR(50) DEFAULT 'Hot200',
    is_active BOOLEAN DEFAULT TRUE,
    order_index INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_code_problems_order (order_index),
    INDEX idx_code_problems_slug (slug)
);

CREATE TABLE IF NOT EXISTS code_test_cases (
    id INT AUTO_INCREMENT PRIMARY KEY,
    problem_id INT NOT NULL,
    input TEXT NOT NULL,
    expected_output TEXT NOT NULL,
    is_sample BOOLEAN DEFAULT FALSE,
    explanation TEXT NULL,
    sort_order INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (problem_id) REFERENCES code_problems(id) ON DELETE CASCADE,
    INDEX idx_code_test_cases_problem (problem_id, is_sample)
);

CREATE TABLE IF NOT EXISTS code_submissions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    problem_id INT NOT NULL,
    language VARCHAR(30) NOT NULL,
    source_code TEXT NOT NULL,
    status VARCHAR(40) NOT NULL,
    runtime FLOAT NULL,
    memory INT NULL,
    passed_count INT DEFAULT 0,
    total_count INT DEFAULT 0,
    stdout TEXT NULL,
    stderr TEXT NULL,
    compile_output TEXT NULL,
    result_json TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (problem_id) REFERENCES code_problems(id) ON DELETE CASCADE,
    INDEX idx_code_submissions_user_created (user_id, created_at),
    INDEX idx_code_submissions_problem (problem_id)
);
