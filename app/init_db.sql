CREATE DATABASE StockDB;
GO
USE StockDB;
GO

CREATE TABLE Stocks (
    Ticker NVARCHAR(10) PRIMARY KEY,
    IsActive BIT DEFAULT 1
);

CREATE TABLE TradeSignals (
    ID INT IDENTITY(1,1) PRIMARY KEY,
    Date DATETIME,
    Ticker NVARCHAR(10),
    Signal NVARCHAR(10),
    Target_Price DECIMAL(10, 2)
);

CREATE TABLE TransactionLogs (
    TransactionID UNIQUEIDENTIFIER PRIMARY KEY,
    AccountID NVARCHAR(50),
    Ticker NVARCHAR(10),
    Action NVARCHAR(10),
    Price DECIMAL(10, 2),
    Timestamp DATETIME,
    Status NVARCHAR(20),
    ErrorMessage NVARCHAR(MAX)
);

CREATE TABLE Accounts (
    AccountID NVARCHAR(50) PRIMARY KEY, -- Links to Key Vault Secret Name
    AccountName NVARCHAR(100),
    IsActive BIT DEFAULT 1
);

-- Seed Data (Example)
INSERT INTO Accounts (AccountID, AccountName) VALUES 
('test-acct-1', 'Retirement Account'),
('test-acct-2', 'Retirement Account');

-- Seed Data: 10 High-Value Market Leaders
INSERT INTO Stocks (Ticker) VALUES 
('AAPL'),  -- Apple
('MSFT'),  -- Microsoft
('GOOGL'), -- Alphabet
('AMZN'),  -- Amazon
('NVDA'),  -- Nvidia
('TSLA'),  -- Tesla
('JPM'),   -- JPMorgan Chase 
('V'),     -- Visa 
('JNJ'),   -- Johnson & Johnson 
('PG');    -- Procter & Gamble 
GO