-- Create a new database for login
CREATE DATABASE IF NOT EXISTS login_system_emt;
USE login_system_emt;

-- Users who can log in
CREATE TABLE login_users_emt (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
