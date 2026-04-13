import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import json
import os

# --- 1. 기본 설정 및 시간 함수 ---
def get_now():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))

DB_FILE = "trading_db.json"

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                return json.load(f)
        except: pass
    return {"balance_kr": 1000000, "balance_us": 1000000, "balance_coin": 1000000, "portfolio": [], "logs": []}

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f)

# --- 2. 자동 매매 핵심 엔진 ---
def run_trading_engine():
    # 데이터 로드 (세션이 아닌 파일에서 직접 읽기 - 크론잡용)
    db = load_db()
    
    kr_tickers = ["005930.KS", "000660.KS", "035720.KS"] 
    us_tickers = ["NVDA", "TSLA", "AAPL", "PLTR", "MSFT"]
    coin_tickers = ["BTC-USD", "ETH-USD", "DOGE-USD", "XRP-USD"] 
    
    trade_happened = False
    
    # 분석 및 매매 로직
    categories = [('KR', kr_tickers, 'balance_kr'), ('US', us_tickers, 'balance_us'), ('COIN', coin_tickers, 'balance_coin')]
    
    # 매도 체크
    for item in db['portfolio'][:]:
        try:
            data = yf.download(item['ticker'], period="2d", interval="1h", progress=False)
            curr = float(data['Close'].iloc[-1])
            profit = (curr - item['buy_p']) / item['buy_p']
            if profit >= 0.08 or profit <= -0.04:
                db[f"balance_{item['type'].lower()}"] += curr * item['qty']
                db['logs'].append(f"[{get_now().strftime('%H:%M:%S')}] 💰 {item['ticker']} 매도 ({profit*100:.2f}%)")
                db['portfolio'].remove(item)
                trade_happened = True
        except: pass

    # 매수 체크
    for p_type, t_list, b_key in categories:
        for t in t_list:
            if any(p['ticker'] == t for p in db['portfolio']): continue
            try:
                data = yf.download(t, period="2d", interval="1h", progress=False)
                curr, prev = float(data['Close'].iloc[-1]), float(data['Close'].iloc[-2])
                change = (curr - prev) / prev
                if change >= 0.025:
                    qty = (db[b_key] * 0.2) // curr
                    if qty > 0:
                        db[b_key] -= curr * qty
                        db['portfolio'].append({"ticker": t, "buy_p": curr, "qty": qty, "type": p_type})
                        db['logs'].append(f"[{get_now().strftime('%H:%M:%S')}] ✅ {t} 매수 ({change*100:.2f}%)")
                        trade_happened = True
            except: pass
    
    # 무조건 흔적 남기기
    db['logs'].append(f"[{get_now().strftime('%H:%M:%S')}] 🤖 엔진 가동 확인됨")
    if len(db['logs']) > 50: db['logs'] = db['logs'][-50:]
    save_db(db)

# --- 3. [최우선 실행] 파라미터 체크 ---
# 페이지 설정보다 먼저 실행하여 크론잡 신호를 놓치지 않음
if "auto" in st.query_params and st.query_params["auto"] == "true":
    run_trading_engine()
    st.write("자동화 엔진 실행 완료")
    st.stop()

# --- 4. UI 구성 (사용자가 직접 접속했을 때만 실행) ---
st.set_page_config(page_title="AI 관리 센터", layout="wide")
st.session_state.db = load_db() # 최신 데이터 불러오기

st.title("🤖 AI 종합 자산 관리 (100-100-100)")

c1, c2, c3 = st.columns(3)
c1.metric("🇰🇷 국장", f"{st.session_state.db['balance_kr']:,.0f}원")
c2.metric("🇺🇸 미장", f"{st.session_state.db['balance_us']:,.0f}원")
c3.metric("🪙 코인", f"{st.session_state.db['balance_coin']:,.0f}원")

st.divider()

if st.button("🚀 즉시 스캔 가동", use_container_width=True):
    run_trading_engine()
    st.rerun()

if st.button("🔄 데이터 초기화", use_container_width=True):
    if os.path.exists(DB_FILE): os.remove(DB_FILE)
    st.rerun()

tab1, tab2 = st.tabs(["📜 거래 로그", "💼 포트폴리오"])
with tab1:
    for log in reversed(st.session_state.db['logs']): st.write(log)
with tab2:
    for item in st.session_state.db['portfolio']:
        st.write(f"**[{item['type']}] {item['ticker']}** | {int(item['qty'])}주")
