import os
import shutil
import yfinance as yf
import pandas as pd
from datetime import datetime
import requests
from database_api import DatabaseAPI

# --- Configuration ---
db = DatabaseAPI()
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
STORAGE_ACCOUNT = os.getenv("STORAGE_ACCOUNT")
CONTAINER_NAME = os.getenv("CONTAINER_NAME", "daily-analysis")

# UPDATED: Defaults to False (Prod) if variable is missing. 
# It will only be True if your .env file explicitly says "True".
LOCAL_MODE = os.getenv("LOCAL_MODE", "False").lower() == "true"

def cleanup_local_files():
    """Removes files inside 'signals/' but keeps the folder itself (required for Docker mounts)."""
    folder = "signals"
    
    # Create folder if it doesn't exist (e.g. first run)
    if not os.path.exists(folder):
        os.makedirs(folder, exist_ok=True)
        print(f"[LOCAL] Created fresh '{folder}/' directory.")
        return

    # If it exists, clear the contents
    print(f"[LOCAL] Cleaning up old files in '{folder}/'...")
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path) # Deletes the file
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path) # Deletes subdirectories
        except Exception as e:
            print(f"Failed to delete {file_path}. Reason: {e}")

def upload_to_blob(filename, data_frame):
    """Uploads the analysis Excel file to Azure Blob Storage (Production Only)"""
    from azure.storage.blob import BlobServiceClient
    from azure.identity import DefaultAzureCredential

    try:
        print(f"[AZURE] Connecting to Storage Account: {STORAGE_ACCOUNT}...")
        credential = DefaultAzureCredential()
        blob_service_client = BlobServiceClient(
            account_url=f"https://{STORAGE_ACCOUNT}.blob.core.windows.net", 
            credential=credential
        )
        
        excel_filename = filename.replace(".csv", ".xlsx")
        data_frame.to_excel(excel_filename, index=False)
        
        blob_client = blob_service_client.get_blob_client(container=CONTAINER_NAME, blob=excel_filename)
        
        with open(excel_filename, "rb") as data:
            blob_client.upload_blob(data, overwrite=True)
        print(f"[AZURE] Uploaded {excel_filename} successfully.")
        
        if os.path.exists(excel_filename):
            os.remove(excel_filename)
            
    except Exception as e:
        print(f"[AZURE-ERROR] Failed to upload to blob: {e}")

def send_alert(message):
    """Sends a notification to Discord/Teams/Slack"""
    if not WEBHOOK_URL:
        return
    
    payload = {"content": message}
    try:
        requests.post(WEBHOOK_URL, json=payload)
    except Exception as e:
        print(f"Failed to send alert: {e}")

def main():
    print(f"--- Starting Nightly Analysis [{datetime.now()}] ---")
    
    # 1. Local Cleanup (Only if explicitly enabled via .env)
    if LOCAL_MODE:
        cleanup_local_files()
    
    # 2. Get Stock List via API
    tickers = db.get_stock_list()
    if not tickers:
        print("No stocks found in database to analyze.")
        return

    analysis_data = []
    
    # 3. Logic Loop
    print(f"Analyzing {len(tickers)} stocks...")
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="5d")
            
            if len(hist) < 2: 
                print(f"Skipping {ticker}: Insufficient data.")
                continue

            today = hist['Close'].iloc[-1]
            yesterday = hist['Close'].iloc[-2]
            
            signal = "HOLD"
            
            if today > yesterday:
                signal = "BUY"
            elif today < yesterday:
                signal = "SELL"
            
            if signal != "HOLD":
                db.save_signal(ticker, signal, today)
                print(f"{ticker}: {signal} (Today: {today:.2f} vs Yest: {yesterday:.2f})")
                
            analysis_data.append({
                "Ticker": ticker,
                "Date": datetime.now().strftime("%Y-%m-%d"),
                "Signal": signal, 
                "Price": round(today, 2),
                "Yesterday_Price": round(yesterday, 2)
            })

        except Exception as e:
            print(f"Error analyzing {ticker}: {e}")

    # 4. Generate Reports
    if not analysis_data:
        print("No analysis data generated.")
        return

    df = pd.DataFrame(analysis_data)
    base_filename = f"analysis_{datetime.now().strftime('%Y-%m-%d')}.csv"

    if LOCAL_MODE:
        local_path = os.path.join("signals", base_filename)
        df.to_csv(local_path, index=False)
        print(f"[LOCAL] Saved analysis to: {local_path}")
    else:
        upload_to_blob(base_filename, df)

    # 5. Maintenance
    print("Pruning old database records...")
    db.prune_old_signals(days=7) 

    send_alert(f"Nightly Analysis Complete. Processed {len(tickers)} stocks.")
    print("--- Analysis Complete ---")

if __name__ == "__main__":
    main()