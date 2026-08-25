import os
import time
import requests
import numpy as np
import pandas as pd
import yfinance as yf
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
from datetime import datetime
import pytz

# ==================== CONFIGURATION ====================
TELEGRAM_TOKEN = "8982239237:AAGJCgl8qT6c4wPG42yyVXf_wuu7_DM8Pr4"
CHAT_ID = "7211531020"

PAIRS = {
    'Gold (XAUUSD)': 'GC=F',
    'Silver (XAGUSD)': 'SI=F',
    'Bitcoin (BTCUSD)': 'BTC-USD'
}

last_signals = {'Gold (XAUUSD)': None, 'Silver (XAGUSD)': None, 'Bitcoin (BTCUSD)': None}
last_morning_msg_date = None

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Error sending Telegram message: {e}")

def check_daily_good_morning():
    global last_morning_msg_date
    pkt = pytz.timezone('Asia/Karachi')
    now_pkt = datetime.now(pkt)
    
    if now_pkt.hour == 8 and now_pkt.minute == 0:
        today_str = now_pkt.strftime('%Y-%m-%d')
        if last_morning_msg_date != today_str:
            morning_msg = "☀️ *Good Morning Boss!*\n\nYour Lorentzian ML Engine is 24/7 Monitoring! 🚀📈"
            send_telegram_alert(morning_msg)
            last_morning_msg_date = today_str

# ==================== LORENTZIAN ML ENGINE ====================
def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_features(df):
    """Calculates Normalized Feature Space for Lorentzian Classifier"""
    df['RSI'] = calculate_rsi(df['Close'], 14) / 100.0
    
    # WaveTrend Approximation
    ap = (df['High'] + df['Low'] + df['Close']) / 3
    esa = ap.ewm(span=10, adjust=False).mean()
    d = (ap - esa).abs().ewm(span=10, adjust=False).mean()
    ci = (ap - esa) / (0.015 * d)
    df['WT'] = ci.ewm(span=21, adjust=False).mean() / 100.0
    
    # CCI
    tp = (df['High'] + df['Low'] + df['Close']) / 3
    sma = tp.rolling(20).mean()
    mad = tp.rolling(20).apply(lambda x: np.fabs(x - x.mean()).mean())
    df['CCI'] = ((tp - sma) / (0.015 * mad)) / 100.0
    
    df.fillna(0, inplace=True)
    return df

def lorentzian_distance(x, y):
    """Lorentzian Distance Calculation: sum(log(1 + |x_i - y_i|))"""
    return np.sum(np.log(1 + np.abs(x - y)))

def get_lorentzian_prediction(df, k=8, max_bars=1000):
    """K-NN Machine Learning Classifier using Lorentzian Distance"""
    df = calculate_features(df)
    features = ['RSI', 'WT', 'CCI']
    
    data = df[features].values
    n_bars = len(data)
    
    if n_bars < max_bars:
        max_bars = n_bars
        
    current_features = data[-1]
    distances = []
    
    # Historical Pattern Matching
    for i in range(n_bars - max_bars, n_bars - 4):
        dist = lorentzian_distance(current_features, data[i])
        
        # Label: Direction 4 bars ahead
        future_return = df['Close'].iloc[i+4] - df['Close'].iloc[i]
        label = 1 if future_return > 0 else (-1 if future_return < 0 else 0)
        
        distances.append((dist, label))
        
    distances.sort(key=lambda x: x[0])
    neighbors = distances[:k]
    
    # Voting logic
    prediction = sum([n[1] for n in neighbors])
    
    if prediction > 2:
        return 1, df['Close'].iloc[-1]   # BUY
    elif prediction < -2:
        return -1, df['Close'].iloc[-1]  # SELL
    else:
        return 0, df['Close'].iloc[-1]   # NEUTRAL

def check_market():
    global last_signals
    print("Executing Lorentzian Distance ML Engine...")
    
    for name, ticker in PAIRS.items():
        try:
            df = yf.download(tickers=ticker, period='5d', interval='15m', progress=False)
            if df.empty or len(df) < 100:
                continue
                
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
                
            signal, current_price = get_lorentzian_prediction(df)
            
            if signal != 0 and signal != last_signals[name]:
                direction = "🟢 BUY SIGNAL" if signal == 1 else "🔴 SELL SIGNAL"
                msg = (
                    f"⚠️ *LORENTZIAN ML RAW SIGNAL* ⚠️\n\n"
                    f"📌 *Pair:* {name}\n"
                    f"📈 *Direction:* {direction}\n"
                    f"💰 *Price:* ${current_price:.2f}\n"
                    f"⏰ *Timeframe:* 15M Candle Close\n\n"
                    f"⚡ _Pure K-NN Lorentzian Classifier Alert!_"
                )
                send_telegram_alert(msg)
                last_signals[name] = signal
                
        except Exception as e:
            print(f"Error checking {name}: {e}")

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Lorentzian Pure ML Bot is Active 24/7!")

def run_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

if __name__ == "__main__":
    threading.Thread(target=run_dummy_server, daemon=True).start()
    send_telegram_alert("🚀 *Lorentzian Pure Machine Learning Engine is Online!*")
    
    while True:
        check_daily_good_morning()
        check_market()
        time.sleep(90)
        
