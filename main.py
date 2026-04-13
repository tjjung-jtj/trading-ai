import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import json
import os

# --- 1. 한국 시간 설정 ---
def get_now():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))

# --- 2. 데이터 저장/불러오기 (각 100만 원 세팅) ---
DB_FILE = "trading_db.json"
def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {
        "balance_kr": 1000000, 
        "balance_us": 1000000, 
        "balance_coin": 1000000,
        "portfolio": [], 
        "logs": []
    }

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f)

if 'db' not in st.session_state:
    st.session_state.db = load_db()

# --- 3. 핵심 분석 함수 ---
def get_analysis(ticker):
    try:
        data = yf.download(ticker, period="5d", interval="1h", progress=False)
        if data.empty or len(data) < 2: return None
        current_price = float(data['Close'].iloc[-1])
        prev_price = float(data['Close'].iloc[-2])
        change = (current_price - prev_price) / prev_price
        return {"p": current_price, "c": change}
    except:
        return None

# --- 4. 자동 매매 로직 ---
def run_trading_engine():
    db = st.session_state.db
    
    # [종목 리스트] 테더, 솔라나 제외 완료
    kr_tickers = ["005930.KS", "000660.KS", "035720.KS"] 
    us_tickers = ["NVDA", "TSLA", "AAPL", "PLTR", "MSFT"]
    coin_tickers = ["BTC-USD", "ETH-USD", "DOGE-USD", "XRP-USD"] 
    
    trade_happened = False
    
    with st.status("🔍 전 자산 시장 스캔 중...", expanded=True) as status:
        # 1. 매도 감시 (익절 8%, 손절 -4%)
        for item in db['portfolio'][:]:
            res = get_analysis(item['ticker'])
            if res:
                profit = (res['p'] - item['buy_p']) / item['buy_p']
                if profit >= 0.08 or profit <= -0.04:
                    if item['type'] == 'KR': db['balance_kr'] += res['p'] * item['qty']
                    elif item['type'] == 'US': db['balance_us'] += res['p'] * item['qty']
                    else: db['balance_coin'] += res['p'] * item['qty']
                    
                    db['logs'].append(f"[{get_now().strftime('%H:%M:%S')}] 💰 {item['ticker']} 매도 (수익: {profit*100:.2f}%)")
                    db['portfolio'].remove(item)
                    trade_happened = True

        # 2. 매수 탐색 (2.5% 상승 조건)
        categories = [('KR', kr_tickers, 'balance_kr'), ('US', us_tickers, 'balance_us'), ('COIN', coin_tickers, 'balance_coin')]
        for p_type, t_list, b_key in categories:
            for t in t_list:
                if any(p['ticker'] == t for p in db['portfolio']): continue
                res = get_analysis(t)
                if res and res['c'] >= 0.025: 
                    qty = (db[b_key] * 0.2) // res['p'] 
                    if qty > 0:
                        db[b_key] -=
