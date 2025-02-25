SHOW TABLES;


-- Accounts Table
CREATE TABLE Accounts (
    account_id INT PRIMARY KEY,
    account_name VARCHAR(255),
    account_type VARCHAR(50),
    bank_name VARCHAR(255),
    account_number VARCHAR(255),
    finta_id VARCHAR(255),
    client_entity_id INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

SHOW TABLES;

-- Statements Table
CREATE TABLE Statements (
    statement_id INT PRIMARY KEY AUTO_INCREMENT,
    account_id INT,
    start_date DATE,
    end_date DATE,
    starting_balance DECIMAL(10, 2),
    ending_balance DECIMAL(10, 2),
    download_status VARCHAR(20),
    pdf_location VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (account_id) REFERENCES Accounts(account_id)
);

-- Categories Table
CREATE TABLE Categories (
    category_id INT PRIMARY KEY AUTO_INCREMENT,
    category_name VARCHAR(255),
    tax_line VARCHAR(255),
    division VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Receipts Table (Moved before Transactions)
CREATE TABLE Receipts (
    receipt_id INT PRIMARY KEY AUTO_INCREMENT,
    transaction_id INT,
    receipt_date DATE,
    receipt_amount DECIMAL(10,2),
    receipt_source VARCHAR(50),
    image_location VARCHAR(255),
    scanned_status VARCHAR(20),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Transactions Table (Now Receipts exists)
CREATE TABLE Transactions (
    transaction_id INT PRIMARY KEY AUTO_INCREMENT,
    account_id INT,
    transaction_date DATE,
    description TEXT,
    amount DECIMAL(10, 2),
    debit_credit_flag VARCHAR(10),
    category_id INT NULL, -- Allow NULL for foreign key constraints
    validation_status VARCHAR(20),
    source VARCHAR(50),
    statement_id INT,
    receipt_id INT,
    paypal_transaction_id VARCHAR(255),
    amazon_transaction_id VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (account_id) REFERENCES Accounts(account_id),
    FOREIGN KEY (category_id) REFERENCES Categories(category_id) ON DELETE SET NULL,
    FOREIGN KEY (statement_id) REFERENCES Statements(statement_id),
    FOREIGN KEY (receipt_id) REFERENCES Receipts(receipt_id) -- Now Receipts exists!
);

-- Validation Table
CREATE TABLE Validation (
    validation_id INT PRIMARY KEY AUTO_INCREMENT,
    account_id INT,
    total_credits DECIMAL(10, 2),
    total_debits DECIMAL(10, 2),
    expected_balance DECIMAL(10, 2),
    actual_balance DECIMAL(10, 2),
    status VARCHAR(20),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (account_id) REFERENCES Accounts(account_id)
);

-- Tasks Table
CREATE TABLE Tasks (
    task_id INT PRIMARY KEY AUTO_INCREMENT,
    account_id INT,
    task_description TEXT,
    due_date DATE,
    status VARCHAR(20),
    assigned_to VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (account_id) REFERENCES Accounts(account_id)
);

-- Users Table
CREATE TABLE Users (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255),
    email VARCHAR(255),
    role VARCHAR(50),
    access_level VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Clients Table
CREATE TABLE Clients (
    client_entity_id INT PRIMARY KEY AUTO_INCREMENT,
    client_name VARCHAR(255),
    client_description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Add Foreign Key for Client in Accounts Table
ALTER TABLE Accounts ADD CONSTRAINT fk_accounts_clients FOREIGN KEY (client_entity_id) REFERENCES Clients(client_entity_id);

-- Indexes
CREATE INDEX idx_accounts_client_id ON Accounts (client_entity_id);
CREATE INDEX idx_transactions_account_id ON Transactions (account_id);
CREATE INDEX idx_transactions_category_id ON Transactions (category_id);
CREATE INDEX idx_statements_account_id ON Statements (account_id);
CREATE INDEX idx_receipts_transaction_id ON Receipts (transaction_id);
CREATE INDEX idx_validation_account_id ON Validation (account_id);
CREATE INDEX idx_tasks_account_id ON Tasks (account_id);

-- Constraints
ALTER TABLE Transactions ADD CONSTRAINT chk_debit_credit_flag CHECK (debit_credit_flag IN ('D', 'C', '+', '-'));
ALTER TABLE Statements ADD CONSTRAINT chk_download_status CHECK (download_status IN ('Pending', 'Downloaded'));
ALTER TABLE Receipts ADD CONSTRAINT chk_scanned_status CHECK (scanned_status IN ('Pending', 'Completed'));
ALTER TABLE Validation ADD CONSTRAINT chk_validation_status CHECK (status IN ('Balanced', 'Discrepancy'));
ALTER TABLE Tasks ADD CONSTRAINT chk_task_status CHECK (status IN ('Pending', 'Completed'));

