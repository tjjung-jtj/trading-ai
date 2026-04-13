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
        try:
            with open(DB_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {"balance": 10000000, "portfolio": [], "logs": []}

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

# --- 4. 자동 매매 로직 (안정형 + 출석체크 로그) ---
def run_trading_engine():
    db = st.session_state.db
    tickers = ["PLTR", "NVDA", "TSLA", "AAPL", "MSFT", "GOOGL", "BTC-USD", "ETH-USD", "DOGE-USD"]
    trade_happened = False
    
    with st.status("🔍 AI 엔진이 시장을 정밀 스캔 중...", expanded=True) as status:
        # 1. 매도 감시 (익절 8%, 손절 -4%)
        for item in db['portfolio'][:]:
            res = get_analysis(item['ticker'])
            if res:
                profit = (res['p'] - item['buy_p']) / item['buy_p']
                if profit >= 0.08 or profit <= -0.04:
                    db['balance'] += res['p'] * item['qty']
                    db['logs'].append(f"[{get_now().strftime('%H:%M:%S')}] 💰 {item['ticker']} 매도 완료 (수익률: {profit*100:.2f}%)")
                    db['portfolio'].remove(item)
                    trade_happened = True

        # 2. 매수 탐색 (2.5% 이상 상승 시)
        for t in tickers:
            if any(p['ticker'] == t for p in db['portfolio']): continue
            st.write(f"📊 {t} 분석 중...")
            res = get_analysis(t)
            
            if res and res['c'] >= 0.025: 
                qty = (db['balance'] * 0.1) // res['p']
                if qty > 0:
                    db['balance'] -= res['p'] * qty
                    db['portfolio'].append({"ticker": t, "buy_p": res['p'], "qty": qty})
                    db['logs'].append(f"[{get_now().strftime('%H:%M:%S')}] ✅ {t} {int(qty)}주 매수 (상승률: {res['c']*100:.2f}%)")
                    trade_happened = True
        
        # [추가] 매매가 없어도 엔진이 돌아갔다는 '출석체크' 기록 남기기
        if not trade_happened:
            db['logs'].append(f"[{get_now().strftime('%H:%M:%S')}] 🤖 정기 스캔 완료 (조건 부합 종목 없음)")
        
        # 로그가 너무 많아지면 성능을 위해 최근 100개만 유지
        if len(db['logs']) > 100:
            db['logs'] = db['logs'][-100:]

        status.update(label="✅ 자동 매매 프로세스 완료", state="complete", expanded=False)
    
    save_db(db)
    st.session_state.db = db

# --- 5. UI 및 크론잡 설정 ---
st.set_page_config(page_title="AI 트레이딩 센터", layout="wide")

if st.query_params.get("auto") == "true":
    run_trading_engine()

st.title("🤖 AI 무한 트레이딩 센터 (안정 수익형)")

col1, col2 = st.columns(2)
with col1:
    if st.button("🚀 AI 자동매매 엔진 수동 가동", use_container_width=True):
        run_trading_engine()
        st.rerun()
with col2:
    if st.button("🔄 데이터 초기화 (Reset)", use_container_width=True):
        if os.path.exists(DB_FILE):
            os.remove(DB_FILE)
        st.session_state.db = {"balance": 10000000, "portfolio": [], "logs": []}
        save_db(st.session_state.db)
        st.success("시스템이 초기화되었습니다.")
        st.rerun()

st.divider()

tab1, tab2 = st.tabs(["📜 거래 로그", "💼 포트폴리오"])

with tab1:
    st.subheader(f"💰 가상 잔고: {st.session_state.db['balance']:,.0f}원")
    if not st.session_state.db['logs']:
        st.info("거래 기록이 없습니다. 크론잡이 가동될 때까지 기다려주세요.")
    else:
        for log in reversed(st.session_state.db['logs']):
            st.write(log)

with tab2:
    if not st.session_state.db['portfolio']:
        st.info("현재 보유 종목이 없습니다.")
    else:
        cols = st.columns(3)
        for idx, item in enumerate(st.session_state.db['portfolio']):
            res = get_analysis(item['ticker'])
            with cols[idx % 3]:
                if res:
                    p_val = (res['p'] - item['buy_p']) / item['buy_p'] * 100
                    st.metric(label=item['ticker'], value=f"{res['p']:,.2f}", delta=f"{p_val:.2f}%")
                    st.caption(f"매수가: {item['buy_p']:,.2f} | 수량: {int(item['qty'])}")
