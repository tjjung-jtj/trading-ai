import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import json
import os

# --- 1. 기본 설정 및 데이터 관리 ---
def get_now():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))

DB_FILE = "trading_db.json"

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                data = json.load(f)
                # 필수 항목 누락 방지 (백-백-백 세팅)
                for key in ["balance_kr", "balance_us", "balance_coin"]:
                    if key not in data: data[key] = 1000000
                if "portfolio" not in data: data["portfolio"] = []
                if "logs" not in data: data["logs"] = []
                return data
        except: pass
    return {"balance_kr": 1000000, "balance_us": 1000000, "balance_coin": 1000000, "portfolio": [], "logs": []}

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

# --- 2. 자동 매매 핵심 엔진 ---
def run_trading_engine():
    db = load_db()
    
    # 종목 리스트 (요청하신 대로 테더, 솔라나 제외 / 리플 포함)
    kr_tickers = ["005930.KS", "000660.KS", "035720.KS"] 
    us_tickers = ["NVDA", "TSLA", "AAPL", "PLTR", "MSFT"]
    coin_tickers = ["BTC-USD", "ETH-USD", "DOGE-USD", "XRP-USD"] 
    
    trade_happened = False
    
    # [매도 로직] 익절 8%, 손절 -4%
    for item in db['portfolio'][:]:
        try:
            data = yf.download(item['ticker'], period="2d", interval="1h", progress=False)
            curr = float(data['Close'].iloc[-1])
            profit = (curr - item['buy_p']) / item['buy_p']
            if profit >= 0.08 or profit <= -0.04:
                b_key = f"balance_{item['type'].lower()}"
                db[b_key] += curr * item['qty']
                db['logs'].append(f"[{get_now().strftime('%H:%M:%S')}] 💰 {item['ticker']} 매도 ({profit*100:.2f}%)")
                db['portfolio'].remove(item)
                trade_happened = True
        except: pass

    # [매수 로직] 2.5% 이상 급등 시 자산의 20% 투입
    categories = [('KR', kr_tickers, 'balance_kr'), ('US', us_tickers, 'balance_us'), ('COIN', coin_tickers, 'balance_coin')]
    for p_type, t_list, b_key in categories:
        for t in t_list:
            if any(p['ticker'] == t for p in db['portfolio']): continue
            try:
                data = yf.download(t, period="2d", interval="1h", progress=False)
                curr, prev = float(data['Close'].iloc[-1]), float(data['Close'].iloc[-2])
                change = (curr - prev) / prev
                if change >= 0.025:
                    buy_amount = db[b_key] * 0.2
                    qty = buy_amount // curr
                    if qty > 0:
                        db[b_key] -= curr * qty
                        db['portfolio'].append({"ticker": t, "buy_p": curr, "qty": qty, "type": p_type})
                        db['logs'].append(f"[{get_now().strftime('%H:%M:%S')}] ✅ {t} 매수 ({change*100:.2f}%)")
                        trade_happened = True
            except: pass
    
    # 엔진 가동 흔적 남기기
    db['logs'].append(f"[{get_now().strftime('%H:%M:%S')}] 🤖 엔진 가동 확인됨")
    if len(db['logs']) > 50: db['logs'] = db['logs'][-50:]
    save_db(db)
    return db

# --- 3. [최우선] 크론잡 신호 감지 ---
# UI를 그리기 전에 파라미터를 먼저 체크하여 실행 속도를 높임
if st.query_params.get("auto") == "true":
    run_trading_engine()
    st.write("자동화 엔진이 백그라운드에서 실행되었습니다.")
    st.stop()

# --- 4. 사용자 UI 구성 ---
st.set_page_config(page_title="AI 자산관리 센터", layout="wide")
db = load_db()

st.title("🤖 AI 종합 자산 관리 (100-100-100)")

# 상단 자산 현황
c1, c2, c3 = st.columns(3)
c1.metric("🇰🇷 국장 잔고", f"{db['balance_kr']:,.0f}원")
c2.metric("🇺🇸 미장 잔고", f"{db['balance_us']:,.0f}원")
c3.metric("🪙 코인 잔고", f"{db['balance_coin']:,.0f}원")

st.divider()

col1, col2 = st.columns(2)
with col1:
    if st.button("🚀 즉시 스캔 가동", use_container_width=True):
        db = run_trading_engine()
        st.rerun()
with col2:
    if st.button("🔄 데이터 전체 초기화", use_container_width=True):
        if os.path.exists(DB_FILE): os.remove(DB_FILE)
        st.rerun()

tab1, tab2 = st.tabs(["📜 거래 로그", "💼 내 포트폴리오"])
with tab1:
    if not db['logs']: st.info("아직 기록된 로그가 없습니다.")
    for log in reversed(db['logs']): st.write(log)
with tab2:
    if not db['portfolio']: st.info("현재 보유 중인 종목이 없습니다.")
    else:
        for item in db['portfolio']:
            st.write(f"**[{item['type']}] {item['ticker']}** | {int(item['qty'])}주 보유 | 매수가: {item['buy_p']:,.2f}")
