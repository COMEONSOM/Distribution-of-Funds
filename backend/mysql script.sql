-- 🔄 Drop DB if exists
DROP DATABASE IF EXISTS expense_management_tools_database;

-- ✅ Create DB
CREATE DATABASE expense_management_tools_database;
USE expense_management_tools_database;

-- ✅ Table: users
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE
);

-- ✅ Table: expenses
CREATE TABLE expenses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    paid_by INT NOT NULL,
    location VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (paid_by) REFERENCES users(id) ON DELETE CASCADE
);

-- ✅ Table: expense_shares
CREATE TABLE expense_shares (
    id INT AUTO_INCREMENT PRIMARY KEY,
    expense_id INT NOT NULL,
    user_id INT NOT NULL,
    amount_owed DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (expense_id) REFERENCES expenses(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ✅ View: Detailed settlements
CREATE OR REPLACE VIEW user_pairwise_settlements AS
SELECT
    p.name AS payer_name,
    o.name AS receiver_name,
    e.title AS expense_title,
    s.amount_owed
FROM expense_shares s
JOIN users o ON s.user_id = o.id
JOIN expenses e ON s.expense_id = e.id
JOIN users p ON e.paid_by = p.id
ORDER BY p.name, o.name, e.created_at;

-- ✅ View: Total settlements
CREATE OR REPLACE VIEW user_settlement_totals AS
SELECT
    payer_name,
    receiver_name,
    SUM(amount_owed) AS total_owed
FROM user_pairwise_settlements
GROUP BY payer_name, receiver_name
ORDER BY payer_name, receiver_name;

-- 🔥 Indexes for performance
CREATE INDEX idx_paid_by ON expenses(paid_by);
CREATE INDEX idx_expense_shares ON expense_shares(expense_id, user_id);

-- ✅ Test
SHOW TABLES;
