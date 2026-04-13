import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import json
import os

# --- 0. 버전 설정 ---
VERSION = "1.0.5 (Auto-Detection Enhanced)"

# --- 1. 기본 설정 및 데이터 로드 ---
def get_now():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))

DB_FILE = "trading_db.json"

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding='utf-8') as f:
                data = json.load(f)
                if "scan_count" not in data: data["scan_count"] = 0
                if "last_scan" not in data: data["last_scan"] = "없음"
                return data
        except: pass
    return {"balance_kr": 1000000, "balance_us": 1000000, "balance_coin": 1000000, "portfolio": [], "logs": [], "scan_count": 0, "last_scan": "없음"}

def save_db(data):
    with open(DB_FILE, "w", encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# --- 2. 자동 매매 엔진 ---
def run_trading_engine():
    db = load_db()
    now_str = get_now().strftime('%Y-%m-%d %H:%M:%S')
    
    kr_tickers = ["005930.KS", "000660.KS", "035720.KS"] 
    us_tickers = ["NVDA", "TSLA", "AAPL", "PLTR", "MSFT"]
    coin_tickers = ["BTC-USD", "ETH-USD", "DOGE-USD", "XRP-USD"] 
    
    # [매매 로직 실행]
    for p_type, t_list, b_key in [('KR', kr_tickers, 'balance_kr'), ('US', us_tickers, 'balance_us'), ('COIN', coin_tickers, 'balance_coin')]:
        for t in t_list:
            try:
                data = yf.download(t, period="2d", interval="1h", progress=False)
                curr, prev = float(data['Close'].iloc[-1]), float(data['Close'].iloc[-2])
                change = (curr - prev) / prev
                if change >= 0.025 and not any(p['ticker'] == t for p in db['portfolio']):
                    qty = (db[b_key] * 0.2) // curr
                    if qty > 0:
                        db[b_key] -= curr * qty
                        db['portfolio'].append({"ticker": t, "buy_p": curr, "qty": qty, "type": p_type})
                        db['logs'].append(f"[{now_str}] ✅ {t} 매수 ({change*100:.2f}%)")
            except: pass
    
    # 상태 업데이트
    db["scan_count"] += 1
    db["last_scan"] = now_str
    db['logs'].append(f"[{now_str}] 🤖 엔진 가동 (누적 {db['scan_count']}회)")
    if len(db['logs']) > 50: db['logs'] = db['logs'][-50:]
    save_db(db)

# --- 3. [중요] 크론잡 신호 감지 ---
# 쿼리 파라미터가 들어오면 무조건 엔진 가동
if st.query_params.get("auto") == "true":
    run_trading_engine()
    st.write(f"Version {VERSION}: Engine Active")
    st.stop()

# --- 4. UI 구성 ---
st.set_page_config(page_title=f"AI 관리 센터 v{VERSION}", layout="wide")
db = load_db()

st.title("🤖 AI 자산 관리 시스템")

# [업데이트됨] 버전과 엔진 상태를 동시에 표시
st.info(f"📌 **시스템 버전:** {VERSION} | 📊 **누적 스캔:** {db['scan_count']}회 | 🕒 **최근 실행:** {db['last_scan']}")

c1, c2, c3 = st.columns(3)
c1.metric("🇰🇷 국장", f"{db['balance_kr']:,.0f}원")
c2.metric("🇺🇸 미장", f"{db['balance_us']:,.0f}원")
c3.metric("🪙 코인", f"{db['balance_coin']:,.0f}원")

st.divider()

col1, col2 = st.columns(2)
with col1:
    if st.button("🚀 즉시 스캔 가동", use_container_width=True):
        run_trading_engine()
        st.rerun()
with col2:
    if st.button("🔄 데이터 초기화 (0회로 리셋)", use_container_width=True):
        if os.path.exists(DB_FILE): os.remove(DB_FILE)
        st.rerun()

tab1, tab2 = st.tabs(["📜 거래 로그", "💼 포트폴리오"])
with tab1:
    for log in reversed(db['logs']): st.write(log)
with tab2:
    for item in db['portfolio']: st.write(f"**[{item['type']}] {item['ticker']}** | {int(item['qty'])}주")
