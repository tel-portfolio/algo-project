import os
import time
import pytz
from datetime import datetime, timedelta
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.data.historical import StockHistoricalDataClient
# FIXED: Added StockSnapshotRequest to imports
from alpaca.data.requests import StockBarsRequest, StockSnapshotRequest 
from alpaca.data.timeframe import TimeFrame
from database_api import DatabaseAPI

# --- Configuration ---
db = DatabaseAPI()
API_KEY = os.getenv("ALPACA_API_KEY")
API_SECRET = os.getenv("ALPACA_SECRET_KEY")
ACCOUNT_ID = os.getenv("ACCOUNT_ID", "default_account")

ALPACA_ENDPOINT = os.getenv("ALPACA_ENDPOINT", "https://paper-api.alpaca.markets/v2")
SIMULATION_MODE = os.getenv("SIMULATION_MODE", "False").lower() == "true"

def wait_for_market_close():
    """Sleeps until 3:59 PM Eastern Time"""
    if SIMULATION_MODE:
        print(f"[{ACCOUNT_ID}] SIMULATION: Skipping wait.")
        return

    est = pytz.timezone('US/Eastern')
    now = datetime.now(est)
    target_time = now.replace(hour=15, minute=59, second=0, microsecond=0)
    wait_seconds = (target_time - now).total_seconds()
    
    if wait_seconds > 0:
        print(f"[{ACCOUNT_ID}] Waiting {int(wait_seconds)}s for market close...")
        time.sleep(wait_seconds)

def get_market_data(ticker):
    """Fetches Yesterday's Close and Current Price"""
    try:
        data_client = StockHistoricalDataClient(API_KEY, API_SECRET)
        
        # 1. Get Yesterday's Close
        now = datetime.now()
        # Validation 1: Bars Request (You already fixed this)
        request_params = StockBarsRequest(
            symbol_or_symbols=[ticker], 
            timeframe=TimeFrame.Day,
            start=now - timedelta(days=5),
            end=now - timedelta(days=1)
        )
        bars = data_client.get_stock_bars(request_params)
        
        if not bars.data:
            return None, None

        yesterday_bar = bars[ticker][-1]
        yesterday_close = yesterday_bar.close
        
        # 2. Get Current Price
        # Validation 2: Snapshot Request (FIXED THIS PART)
        snapshot_req = StockSnapshotRequest(symbol_or_symbols=[ticker])
        snapshot = data_client.get_stock_snapshot(snapshot_req)
        
        current_price = snapshot[ticker].latest_trade.price
        
        return yesterday_close, current_price
    except Exception as e:
        print(f"[{ACCOUNT_ID}] Data Error for {ticker}: {e}")
        return None, None

def execute_trades(signals):
    if not API_KEY or not API_SECRET:
        print("CRITICAL: Alpaca API Keys missing.")
        return

    if not SIMULATION_MODE:
        print(f"[{ACCOUNT_ID}] Connecting to Alpaca: {ALPACA_ENDPOINT}")
        trading_client = TradingClient(API_KEY, API_SECRET, url_override=ALPACA_ENDPOINT)
    
    for trade in signals:
        ticker = trade["Ticker"]
        signal_type = trade["Signal"]
        
        try:
            print(f"[{ACCOUNT_ID}] Validating {signal_type} for {ticker}...")
            yesterday_close, current_price = get_market_data(ticker)
            
            if yesterday_close is None or current_price is None:
                print(f"[{ACCOUNT_ID}] SKIPPING: Data missing.")
                continue

            is_valid = False
            reason = ""
            
            if signal_type == "BUY":
                if current_price > yesterday_close:
                    is_valid = True
                    reason = f"{current_price} > {yesterday_close}"
                else:
                    reason = f"{current_price} NOT > {yesterday_close}"

            elif signal_type == "SELL":
                if current_price < yesterday_close:
                    is_valid = True
                    reason = f"{current_price} < {yesterday_close}"
                else:
                    reason = f"{current_price} NOT < {yesterday_close}"

            if is_valid:
                if SIMULATION_MODE:
                    print(f"[{ACCOUNT_ID}] [SIMULATION] WOULD {signal_type} {ticker} ({reason})")
                else:
                    print(f"[{ACCOUNT_ID}] EXECUTING {signal_type} {ticker} ({reason})")
                    if signal_type == "BUY":
                        req = MarketOrderRequest(symbol=ticker, notional=100, side=OrderSide.BUY, time_in_force=TimeInForce.DAY)
                        trading_client.submit_order(req)
                    elif signal_type == "SELL":
                        trading_client.close_position(ticker)
                    
                    db.log_transaction(ACCOUNT_ID, ticker, signal_type, "SUCCESS", current_price)
            else:
                msg = f"[SIMULATION] SKIP" if SIMULATION_MODE else "SKIP"
                print(f"[{ACCOUNT_ID}] {msg} {ticker}: {reason}")
                if not SIMULATION_MODE:
                     db.log_transaction(ACCOUNT_ID, ticker, signal_type, "SKIPPED", current_price, reason)

        except Exception as e:
            print(f"[{ACCOUNT_ID}] Error: {e}")

def main():
    print(f"--- Portfolio Manager Started (Account: {ACCOUNT_ID}) ---")
    signals = db.get_todays_signals()
    if not signals:
        print("No signals found.")
        return

    wait_for_market_close()
    execute_trades(signals)

if __name__ == "__main__":
    main()