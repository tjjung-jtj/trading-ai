import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import json
import os

# --- 1. 한국 시간 및 기본 설정 ---
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

# 세션 데이터 초기화
if 'db' not in st.session_state:
    st.session_state.db = load_db()

# --- 2. 분석 및 엔진 로직 ---
def get_analysis(ticker):
    try:
        data = yf.download(ticker, period="2d", interval="1h", progress=False)
        if data.empty or len(data) < 2: return None
        current_price = float(data['Close'].iloc[-1])
        prev_price = float(data['Close'].iloc[-2])
        change = (current_price - prev_price) / prev_price
        return {"p": current_price, "c": change}
    except: return None

def run_trading_engine():
    db = st.session_state.db
    kr_tickers = ["005930.KS", "000660.KS", "035720.KS"] 
    us_tickers = ["NVDA", "TSLA", "AAPL", "PLTR", "MSFT"]
    coin_tickers = ["BTC-USD", "ETH-USD", "DOGE-USD", "XRP-USD"] 
    
    trade_happened = False
    
    # 1. 매도 감시
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

    # 2. 매수 탐색
    categories = [('KR', kr_tickers, 'balance_kr'), ('US', us_tickers, 'balance_us'), ('COIN', coin_tickers, 'balance_coin')]
    for p_type, t_list, b_key in categories:
        for t in t_list:
            if any(p['ticker'] == t for p in db['portfolio']): continue
            res = get_analysis(t)
            if res and res['c'] >= 0.025: 
                buy_amount = db[b_key] * 0.2
                qty = buy_amount // res['p'] 
                if qty > 0:
                    db[b_key] -= res['p'] * qty
                    db['portfolio'].append({"ticker": t, "buy_p": res['p'], "qty": qty, "type": p_type})
                    db['logs'].append(f"[{get_now().strftime('%H:%M:%S')}] ✅ {t} 매수 (상승률: {res['c']*100:.2f}%)")
                    trade_happened = True
    
    # [핵심] 출석 체크 로그
    db['logs'].append(f"[{get_now().strftime('%H:%M:%S')}] 🤖 정기 스캔 완료")
    if len(db['logs']) > 50: db['logs'] = db['logs'][-50:]
    
    save_db(db)
    st.session_state.db = db

# --- 3. [중요] 페이지 설정 및 자동 실행 체크 ---
st.set_page_config(page_title="AI 관리 센터", layout="wide")

# 크론잡이 보낸 파라미터 감지 로직 강화
# st.query_params 대신 더 직관적인 체크 사용
if "auto" in st.query_params and st.query_params["auto"] == "true":
    run_trading_engine()
    st.write("자동 실행 완료") # 확인용 출력
    st.stop() # 자동 실행 시에는 UI를 그리지 않고 멈춤 (서버 자원 절약)

# --- 4. UI 구성 ---
st.title("🤖 AI 종합 자산 관리 (100-100-100)")

c1, c2, c3 = st.columns(3)
c1.metric("🇰🇷 국장 잔고", f"{st.session_state.db['balance_kr']:,.0f}원")
c2.metric("🇺🇸 미장 잔고", f"{st.session_state.db['balance_us']:,.0f}원")
c3.metric("🪙 코인 잔고", f"{st.session_state.db['balance_coin']:,.0f}원")

st.divider()

col1, col2 = st.columns(2)
with col1:
    if st.button("🚀 즉시 스캔 가동", use_container_width=True):
        run_trading_engine()
        st.rerun()
with col2:
    if st.button("🔄 전 자산 초기화", use_container_width=True):
        if os.path.exists(DB_FILE): os.remove(DB_FILE)
        st.session_state.db = load_db()
        save_db(st.session_state.db)
        st.rerun()

tab1, tab2 = st.tabs(["📜 거래 로그", "💼 포트폴리오"])
with tab1:
    for log in reversed(st.session_state.db['logs']):
        st.write(log)
with tab2:
    if not st.session_state.db['portfolio']:
        st.info("보유 종목 없음")
    else:
        for item in st.session_state.db['portfolio']:
            st.write(f"**[{item['type']}] {item['ticker']}** | {int(item['qty'])}주 | 매수가: {item['buy_p']:,.2f}")
