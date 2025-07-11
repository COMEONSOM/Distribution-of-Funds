-- 🔄 Drop DB if exists
DROP DATABASE IF EXISTS login_system_emt;

-- ✅ Create DB
CREATE DATABASE login_system_emt;
USE login_system_emt;

-- ✅ Users table
CREATE TABLE login_users_emt (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 🔥 Add index for faster login checks
CREATE INDEX idx_email ON login_users_emt(email);

-- ✅ Test
SHOW TABLES;
SELECT * FROM login_users_emt;
