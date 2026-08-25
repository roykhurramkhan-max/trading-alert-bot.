import time
import requests
import numpy as np
import pandas as pd
import yfinance as yf
from ta.trend import EMAIndicator

# ==================== CONFIGURATION ====================
TELEGRAM_TOKEN = "8982239237:AAGJCgl8qT6c4wPG42yyVXf_wuu7_DM8Pr4"  # Yahan apna Bot Token lagayein
CHAT_ID = "7211531020"                   # Yahan apni Chat ID lagayein

# Tickers: Gold, Silver, Bitcoin
PAIRS = {
    'Gold (XAUUSD)': 'GC=F',
    'Silver (XAGUSD)': 'SI=F',
    'Bitcoin (BTCUSD)': 'BTC-USD'
}

last_signals = {'Gold (XAUUSD)': None, 'Silver (XAGUSD)': None, 'Bitcoin (BTCUSD)': None}

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Error sending Telegram message: {e}")

def get_lorentzian_signal(df):
    """Simplified Machine Learning KNN Distance Classifier with 200 EMA Filter"""
    df = df.copy()
    
    # Technical Indicators (Features)
    df['EMA_200'] = EMAIndicator(close=df['Close'], window=200).ema_indicator()
    df['RSI'] = pd.qcut(df['Close'].pct_change(), q=4, labels=False, duplicates='drop')
    
    # Distance Metric Simulation (KNN logic)
    df['Price_Change'] = df['Close'].pct_change()
    df['Signal'] = 0
    
    # Trend Rules
    for i in range(200, len(df)):
        close_price = df['Close'].iloc[i]
        ema_val = df['EMA_200'].iloc[i]
        prev_close = df['Close'].iloc[i-1]
        
        # Simple Machine Learning Threshold Strategy
        momentum = (df['Close'].iloc[i] - df['Close'].iloc[i-4]) / df['Close'].iloc[i-4]
        
        if close_price > ema_val and momentum > 0.005 and prev_close <= ema_val:
            df.iloc[i, df.columns.get_loc('Signal')] = 1  # BUY Signal
        elif close_price < ema_val and momentum < -0.005 and prev_close >= ema_val:
            df.iloc[i, df.columns.get_loc('Signal')] = -1 # SELL Signal
            
    return df.iloc[-1]['Signal'], df.iloc[-1]['Close'], df.iloc[-1]['EMA_200']

def check_market():
    global last_signals
    print("Checking 1H Market Candles...")
    
    for name, ticker in PAIRS.items():
        try:
            # Download 1-Hour historical data
            df = yf.download(tickers=ticker, period='5d', interval='1h', progress=False)
            if df.empty or len(df) < 200:
                continue
                
            # Handle multi-index columns if present
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
                
            signal, current_price, ema_200 = get_lorentzian_signal(df)
            
            # Send alert only when a new signal forms
            if signal != 0 and signal != last_signals[name]:
                direction = "🟢 BUY SIGNAL" if signal == 1 else "🔴 SELL SIGNAL"
                msg = (
                    f"⚠️ *NEW TRADING SIGNAL DETECTED* ⚠️\n\n"
                    f"📌 *Pair:* {name}\n"
                    f"📈 *Direction:* {direction}\n"
                    f"💰 *Entry Price:* ${current_price:.2f}\n"
                    f"📊 *200 EMA Level:* ${ema_200:.2f}\n"
                    f"⏰ *Timeframe:* 1H Candle Close\n\n"
                    f"⚡ _Please check Risk Management ($40 Risk) before placing trade!_"
                )
                send_telegram_alert(msg)
                last_signals[name] = signal
                
        except Exception as e:
            print(f"Error checking {name}: {e}")
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is Running 24/7!")

def run_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

# Continuous 24/7 Monitoring Loop
if __name__ == "__main__":
    # Start dummy web server to keep Render happy
    threading.Thread(target=run_dummy_server, daemon=True).start()
    
    send_telegram_alert("🚀 *Lorentzian Alert Bot is Online & Monitoring 24/7!*")
    while True:
        check_market()
        time.sleep(300) # Check market every 5 minutes
