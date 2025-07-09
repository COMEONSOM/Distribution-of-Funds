-- 🔄 Safer drop first (only if needed manually)
DROP DATABASE IF EXISTS expense_management_tools_database;

-- ✅ Create & Use the database
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
    title VARCHAR(255) NOT NULL,         -- What was the expense for?
    amount FLOAT NOT NULL,               -- Total amount paid
    paid_by INT NOT NULL,                -- FK: Who paid
    location VARCHAR(255),               -- Where it was spent
    group_size INT,                      -- Optional: number of people
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (paid_by) REFERENCES users(id) ON DELETE CASCADE
);

-- ✅ Table: expense_shares
CREATE TABLE expense_shares (
    id INT AUTO_INCREMENT PRIMARY KEY,
    expense_id INT NOT NULL,             -- FK: which expense
    user_id INT NOT NULL,                -- FK: who owes
    amount_owed FLOAT NOT NULL,          -- How much owed
    FOREIGN KEY (expense_id) REFERENCES expenses(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ✅ View: detailed per-expense settlements
CREATE OR REPLACE VIEW user_pairwise_settlements AS
SELECT
    p.name AS payer_name,                -- The one who paid
    o.name AS receiver_name,             -- The one who owes
    e.title AS expense_title,            -- Expense name
    s.amount_owed                        -- Amount owed
FROM expense_shares s
JOIN users o ON s.user_id = o.id         -- The person who owes
JOIN expenses e ON s.expense_id = e.id
JOIN users p ON e.paid_by = p.id         -- The person who paid
ORDER BY p.name, o.name, e.created_at;

-- ✅ View: final settlement totals per payer-receiver
CREATE OR REPLACE VIEW user_settlement_totals AS
SELECT
    payer_name,
    receiver_name,
    SUM(amount_owed) AS total_owed
FROM user_pairwise_settlements
GROUP BY payer_name, receiver_name
ORDER BY payer_name, receiver_name;
