import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import json
import os

# --- 1. 한국 시간 설정 ---
def get_now():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))

# --- 2. 데이터 저장/불러오기 (잔고 분리) ---
DB_FILE = "trading_db.json"
def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    # 국장 100만, 미장 100만, 코인 100만 초기 세팅
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

# --- 4. 자동 매매 로직 (자산군별 매칭) ---
def run_trading_engine():
    db = st.session_state.db
    # 종목별 카테고리 분류
    kr_tickers = ["005930.KS", "000660.KS"] # 삼성전자, SK하이닉스 등 (국장)
    us_tickers = ["NVDA", "TSLA", "AAPL", "PLTR"] # (미장)
    coin_tickers = ["BTC-USD", "ETH-USD", "DOGE-USD"] # (코인)
    
    trade_happened = False
    
    with st.status("🔍 자산별 시장 정밀 스캔 중...", expanded=True) as status:
        # 1. 매도 로직 (공통)
        for item in db['portfolio'][:]:
            res = get_analysis(item['ticker'])
            if res:
                profit = (res['p'] - item['buy_p']) / item['buy_p']
                if profit >= 0.08 or profit <= -0.04:
                    # 매도 시 해당 자산군 잔고로 복구
                    if item['type'] == 'KR': db['balance_kr'] += res['p'] * item['qty']
                    elif item['type'] == 'US': db['balance_us'] += res['p'] * item['qty']
                    else: db['balance_coin'] += res['p'] * item['qty']
                    
                    db['logs'].append(f"[{get_now().strftime('%H:%M:%S')}] 💰 {item['ticker']} 매도 (수익률: {profit*100:.2f}%)")
                    db['portfolio'].remove(item)
                    trade_happened = True

        # 2. 매수 로직 (자산군별 처리)
        categories = [('KR', kr_tickers, 'balance_kr'), ('US', us_tickers, 'balance_us'), ('COIN', coin_tickers, 'balance_coin')]
        
        for p_type, t_list, b_key in categories:
            for t in t_list:
                if any(p['ticker'] == t for p in db['portfolio']): continue
                res = get_analysis(t)
                if res and res['c'] >= 0.025: # 2.5% 상승 조건
                    qty = (db[b_key] * 0.2) // res['p'] # 각 자산의 20%씩 투자
                    if qty > 0:
                        db[b_key] -= res['p'] * qty
                        db['portfolio'].append({"ticker": t, "buy_p": res['p'], "qty": qty, "type": p_type})
                        db['logs'].append(f"[{get_now().strftime('%H:%M:%S')}] ✅ {t} 매수 (상승률: {res['c']*100:.2f}%)")
                        trade_happened = True
        
        if not trade_happened:
            db['logs'].append(f"[{get_now().strftime('%H:%M:%S')}] 🤖 정기 스캔 완료 (조건 미달)")
        
        if len(db['logs']) > 50: db['logs'] = db['logs'][-50:]
        status.update(label="✅ 전 자산 스캔 완료", state="complete", expanded=False)
    
    save_db(db)
    st.session_state.db = db

# --- 5. UI 구성 ---
st.set_page_config(page_title="AI 종합 자산 관리", layout="wide")
if st.query_params.get("auto") == "true":
    run_trading_engine()

st.title("🤖 AI 종합 자산 관리 센터")

# 잔고 현황판
c1, c2, c3 = st.columns(3)
c1.metric("🇰🇷 국장 잔고", f"{st.session_state.db['balance_kr']:,.0f}원")
c2.metric("🇺🇸 미장 잔고", f"{st.session_state.db['balance_us']:,.0f}원")
c3.metric("🪙 코인 잔고", f"{st.session_state.db['balance_coin']:,.0f}원")

st.divider()

col1, col2 = st.columns(2)
with col1:
    if st.button("🚀 전체 시장 강제 스캔", use_container_width=True):
        run_trading_engine()
        st.rerun()
with col2:
    if st.button("🔄 전 자산 초기화 (각 100만)", use_container_width=True):
        if os.path.exists(DB_FILE): os.remove(DB_FILE)
        st.session_state.db = load_db()
        save_db(st.session_state.db)
        st.rerun()

tab1, tab2 = st.tabs(["📜 통합 거래 로그", "💼 통합 포트폴리오"])
with tab1:
    for log in reversed(st.session_state.db['logs']): st.write(log)
with tab2:
    if not st.session_state.db['portfolio']: st.info("보유 종목이 없습니다.")
    else:
        for item in st.session_state.db['portfolio']:
            st.write(f"**[{item['type']}] {item['ticker']}** - {int(item['qty'])}주 보유 중")
