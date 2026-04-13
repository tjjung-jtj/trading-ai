import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import json
import os

# --- 1. 기본 설정 및 데이터 로드 ---
def get_now():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))

DB_FILE = "trading_db.json"

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding='utf-8') as f:
                data = json.load(f)
                # 상태 확인용 데이터 필드 추가
                if "scan_count" not in data: data["scan_count"] = 0
                if "last_scan" not in data: data["last_scan"] = "없음"
                return data
        except: pass
    return {
        "balance_kr": 1000000, "balance_us": 1000000, "balance_coin": 1000000, 
        "portfolio": [], "logs": [], "scan_count": 0, "last_scan": "없음"
    }

def save_db(data):
    with open(DB_FILE, "w", encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# --- 2. 자동 매매 엔진 ---
def run_trading_engine():
    db = load_db()
    now_str = get_now().strftime('%Y-%m-%d %H:%M:%S')
    
    # [종목 리스트]
    kr_tickers = ["005930.KS", "000660.KS", "035720.KS"] 
    us_tickers = ["NVDA", "TSLA", "AAPL", "PLTR", "MSFT"]
    coin_tickers = ["BTC-USD", "ETH-USD", "DOGE-USD", "XRP-USD"] 
    
    # 1. 매도 감시
    for item in db['portfolio'][:]:
        try:
            data = yf.download(item['ticker'], period="2d", interval="1h", progress=False)
            curr = float(data['Close'].iloc[-1])
            profit = (curr - item['buy_p']) / item['buy_p']
            if profit >= 0.08 or profit <= -0.04:
                db[f"balance_{item['type'].lower()}"] += curr * item['qty']
                db['logs'].append(f"[{now_str}] 💰 {item['ticker']} 매도 ({profit*100:.2f}%)")
                db['portfolio'].remove(item)
        except: pass

    # 2. 매수 탐색
    categories = [('KR', kr_tickers, 'balance_kr'), ('US', us_tickers, 'balance_us'), ('COIN', coin_tickers, 'balance_coin')]
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
                        db['logs'].append(f"[{now_str}] ✅ {t} 매수 ({change*100:.2f}%)")
            except: pass
    
    # --- 상태 업데이트 ---
    db["scan_count"] += 1
    db["last_scan"] = now_str
    db['logs'].append(f"[{now_str}] 🤖 엔진 가동 완료 (누적 {db['scan_count']}회)")
    
    if len(db['logs']) > 50: db['logs'] = db['logs'][-50:]
    save_db(db)

# --- 3. 크론잡 자동 실행 감지 ---
if st.query_params.get("auto") == "true":
    run_trading_engine()
    st.write("Engine running...")
    st.stop()

# --- 4. UI 구성 ---
st.set_page_config(page_title="AI 종합관리", layout="wide")
current_db = load_db()

st.title("🤖 AI 자산 관리 시스템")

# [추가된 부분] 엔진 상태 대시보드
st.info(f"📊 **엔진 상태:** 마지막 스캔 - {current_db['last_scan']} | **누적 스캔 횟수:** {current_db['scan_count']}회")

# 상단 잔고 현황
c1, c2, c3 = st.columns(3)
c1.metric("🇰🇷 국장", f"{current_db['balance_kr']:,.0f}원")
c2.metric("🇺🇸 미장", f"{current_db['balance_us']:,.0f}원")
c3.metric("🪙 코인", f"{current_db['balance_coin']:,.0f}원")

st.divider()

col1, col2 = st.columns(2)
with col1:
    if st.button("🚀 즉시 스캔 가동", use_container_width=True):
        run_trading_engine()
        st.rerun()
with col2:
    if st.button("🔄 데이터 초기화", use_container_width=True):
        if os.path.exists(DB_FILE): os.remove(DB_FILE)
        st.rerun()

tab1, tab2 = st.tabs(["📜 거래 로그", "💼 포트폴리오"])
with tab1:
    for log in reversed(current_db['logs']): st.write(log)
with tab2:
    if not current_db['portfolio']: st.info("보유 종목 없음")
    else:
        for item in current_db['portfolio']:
            st.write(f"**[{item['type']}] {item['ticker']}** | {int(item['qty'])}주")
