import os
import struct
import pyodbc
from datetime import datetime
from azure.identity import DefaultAzureCredential

# --- Configuration ---
# Uses Env Vars for flexibility. Defaults set for safety.
SQL_SERVER = os.getenv("SQL_SERVER", "your-sql-server.database.windows.net")
SQL_DB = os.getenv("SQL_DB", "StockDB")
SQL_PORT = os.getenv("SQL_PORT", "1433")

# Toggle Mock Mode for testing without any database
MOCK_MODE = os.getenv("MOCK_MODE", "False").lower() == "true"

class DatabaseAPI:
    def __init__(self):
        # Base connection string template
        self.base_conn_str = (
            f"DRIVER={{ODBC Driver 18 for SQL Server}};"
            f"SERVER={SQL_SERVER},{SQL_PORT};"
            f"DATABASE={SQL_DB};"
        )

    def prune_old_signals(self, days=7):
            """Deletes signals older than 'days' to keep the DB clean."""
            if MOCK_MODE:
                print(f"[DB-MOCK] Pruned signals older than {days} days.")
                return

            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                query = "DELETE FROM TradeSignals WHERE Date < DATEADD(day, ?, GETDATE())"
                cursor.execute(query, -days)
                conn.commit()
                conn.close()
                print(f"[DB] Pruned old signals > {days} days.")
            except Exception as e:
                print(f"[DB-ERROR] Failed to prune signals: {e}")

    def _get_connection(self):
        """
        Internal method to handle Authentication logic.
        1. Mock Mode -> Returns None
        2. Local Mode (Password) -> Uses SQL Auth
        3. Cloud Mode (No Password) -> Uses Azure Managed Identity
        """
        if MOCK_MODE:
            print("[DB-MOCK] Connection Requested (Mock Mode)")
            return None

        # Check for Local Password (Docker/LocalDev)
        db_password = os.getenv("DB_PASSWORD")
        db_username = os.getenv("DB_USERNAME", "sa")

        if db_password:
            # Local Connection logic
            # TrustServerCertificate=yes is required for local Docker SQL Edge
            conn_str = (
                f"{self.base_conn_str}"
                f"UID={db_username};PWD={db_password};"
                "Encrypt=yes;TrustServerCertificate=yes;Connection Timeout=30;"
            )
            return pyodbc.connect(conn_str)

        # Azure Connection logic (Managed Identity)
        # We need a token for the SQL Database
        credential = DefaultAzureCredential()
        token_bytes = credential.get_token("https://database.windows.net/.default").token.encode("UTF-16-LE")
        token_struct = struct.pack(f'<I{len(token_bytes)}s', len(token_bytes), token_bytes)

        # Connect using the Access Token
        # Encrypt=yes is standard for Azure SQL
        conn_str = f"{self.base_conn_str}Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
        return pyodbc.connect(conn_str, attrs_before={1256: token_struct})

    def get_stock_list(self):
        """Fetches the list of tickers to analyze from the DB"""
        if MOCK_MODE:
            return ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "JPM", "V", "JNJ", "PG"]
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            # Only get stocks marked as active
            cursor.execute("SELECT Ticker FROM Stocks WHERE IsActive = 1")
            rows = cursor.fetchall()
            conn.close()
            return [row.Ticker for row in rows]
        except Exception as e:
            print(f"[DB-ERROR] Failed to fetch stock list: {e}")
            return []

    def get_active_accounts(self):
        """
        Fetches metadata for all active trading accounts.
        Returns a list of dictionaries: [{'AccountID': '...', 'AccountName': '...'}]
        """
        if MOCK_MODE:
            return [
                {"AccountID": "test-acct-1", "AccountName": "Mock Growth"},
                {"AccountID": "test-acct-2", "AccountName": "Mock Safe"}
            ]

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT AccountID, AccountName FROM Accounts WHERE IsActive = 1")
            
            columns = [column[0] for column in cursor.description]
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            
            conn.close()
            return results
        except Exception as e:
            print(f"[DB-ERROR] Failed to fetch accounts: {e}")
            return []

    def save_signal(self, ticker, signal, price):
        """Inserts a new Buy/Sell signal into the daily table"""
        if MOCK_MODE:
            print(f"[DB-MOCK] Saved Signal: {ticker} -> {signal} @ ${price}")
            return

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            # Use T-SQL MERGE or simple INSERT. 
            # Here we assume cleanup happens separately or we just append.
            cursor.execute(
                "INSERT INTO TradeSignals (Date, Ticker, Signal, Target_Price) VALUES (?, ?, ?, ?)",
                datetime.now(), ticker, signal, price
            )
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[DB-ERROR] Failed to save signal for {ticker}: {e}")

    def clear_todays_signals(self):
        """Removes existing signals for today to prevent duplicates"""
        if MOCK_MODE:
            print("[DB-MOCK] Cleared old signals.")
            return

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM TradeSignals WHERE CAST(Date AS Date) = CAST(GETDATE() AS Date)")
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[DB-ERROR] Failed to clear signals: {e}")

    def get_todays_signals(self):
        """Fetches signals generated for the current day"""
        if MOCK_MODE:
            return [
                {"Ticker": "AAPL", "Signal": "BUY", "Target_Price": 150.00},
                {"Ticker": "TSLA", "Signal": "SELL", "Target_Price": 200.00}
            ]

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT Ticker, Signal, Target_Price 
                FROM TradeSignals 
                WHERE CAST(Date AS Date) = CAST(GETDATE() AS Date)
            """
            cursor.execute(query)
            
            columns = [column[0] for column in cursor.description]
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            
            conn.close()
            return results
        except Exception as e:
            print(f"[DB-ERROR] Failed to fetch today's signals: {e}")
            return []

    def log_transaction(self, account_id, ticker, action, status, price, error_msg=None):
        """Logs the trade result (Success/Fail)"""
        if MOCK_MODE:
            print(f"[DB-MOCK] Logged Transaction: {account_id} | {action} {ticker} | {status} | Err: {error_msg}")
            return

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            query = """
                INSERT INTO TransactionLogs 
                (TransactionID, AccountID, Ticker, Action, Price, Timestamp, Status, ErrorMessage) 
                VALUES (NEWID(), ?, ?, ?, ?, ?, ?, ?)
            """
            cursor.execute(query, account_id, ticker, action, price, datetime.now(), status, error_msg)
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[DB-ERROR] Failed to log transaction: {e}")