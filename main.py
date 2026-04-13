import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import json
import os

# --- 1. 한국 시간 설정 ---
def get_now():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))

# --- 2. 데이터 저장/불러오기 ---
DB_FILE = "trading_db.json"
def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f: return json.load(f)
    return {"balance": 10000000, "portfolio": [], "logs": []}

def save_db(data):
    with open(DB_FILE, "w") as f: json.dump(data, f)

# 세션 초기화
if 'db' not in st.session_state:
    st.session_state.db = load_db()

# --- 3. 핵심 분석 함수 ---
def get_analysis(ticker):
    try:
        data = yf.download(ticker, period="2d", interval="1h", progress=False)
        if data.empty: return None
        current_price = data['Close'].iloc[-1]
        prev_price = data['Close'].iloc[-2]
        change = (current_price - prev_price) / prev_price
        return {"p": float(current_price), "c": float(change)}
    except: return None

# --- 4. 자동 매매 로직 ---
def run_trading_engine():
    db = st.session_state.db
    tickers = ["PLTR", "NVDA", "TSLA", "AAPL", "BTC-USD", "ETH-USD"]
    
    # 실시간 진행 상황을 보여주기 위한 Streamlit 전용 위젯
    with st.status("🔍 AI 엔진이 시장을 정밀 스캔 중...", expanded=True) as status:
        # 1. 익절/손절 감시
        for item in db['portfolio'][:]:
            res = get_analysis(item['ticker'])
            if res:
                profit = (res['p'] - item['buy_p']) / item['buy_p']
                if profit >= 0.05 or profit <= -0.03:
                    db['balance'] += res['p'] * item['qty']
                    db['logs'].append(f"[{get_now().strftime('%m/%d %H:%M')}] {item['ticker']} 매도 (수익률: {profit*100:.2f}%)")
                    db['portfolio'].remove(item)

        # 2. 신규 매수 탐색
        for t in tickers:
            if any(p['ticker'] == t for p in db['portfolio']): continue
            st.write(f"📊 {t} 데이터 분석 중...")
            res = get_analysis(t)
            if res and res['c'] > 0.02: # 2% 이상 상승 시 매수
                qty = (db['balance'] * 0.1) // res['p']
                if qty > 0:
                    db['balance'] -= res['p'] * qty
                    db['portfolio'].append({"ticker": t, "buy_p": res['p'], "qty": qty})
                    db['logs'].append(f"[{get_now().strftime('%m/%d %H:%M')}] {t} {qty}주 매수 완료")
        
        status.update(label="✅ 스캔 및 거래 완료!", state="complete", expanded=False)
    
    save_db(db)

# --- 5. UI 구성 ---
st.title("🤖 AI 무한 트레이딩 센터")

if st.button("🚀 AI 자동매매 엔진 가동"):
    run_trading_engine()
    st.rerun()

tab1, tab2 = st.tabs(["📜 거래 로그", "💼 포트폴리오"])

with tab1:
    st.write(f"현재 잔고: {st.session_state.db['balance']:,.0f}원")
    for log in reversed(st.session_state.db['logs']):
        st.write(log)

with tab2:
    for item in st.session_state.db['portfolio']:
        res = get_analysis(item['ticker'])
        p_val = (res['p'] - item['buy_p']) / item['buy_p'] * 100 if res else 0
        st.metric(item['ticker'], f"{item['buy_p']:,.2f}", f"{p_val:.2f}%")
