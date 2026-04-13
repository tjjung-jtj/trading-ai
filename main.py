import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import json
import os

# --- 1. 기본 설정 ---
def get_now():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))

DB_FILE = "trading_db.json"

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding='utf-8') as f:
                data = json.load(f)
                if "scan_count" not in data: data["scan_count"] = 0
                return data
        except: pass
    return {"balance_kr": 1000000, "balance_us": 1000000, "balance_coin": 1000000, "portfolio": [], "logs": [], "scan_count": 0, "last_scan": "없음"}

def save_db(data):
    with open(DB_FILE, "w", encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# --- 2. 매매 엔진 (최적화) ---
def run_trading_engine():
    db = load_db()
    now_str = get_now().strftime('%Y-%m-%d %H:%M:%S')
    
    # [종목 리스트]
    tickers = {
        'KR': ["005930.KS", "000660.KS", "035720.KS"],
        'US': ["NVDA", "TSLA", "AAPL", "PLTR", "MSFT"],
        'COIN': ["BTC-USD", "ETH-USD", "DOGE-USD", "XRP-USD"]
    }

    # 매도/매수 로직 통합 실행
    for p_type, t_list in tickers.items():
        b_key = f"balance_{p_type.lower()}"
        for t in t_list:
            try:
                data = yf.download(t, period="2d", interval="1h", progress=False)
                if data.empty: continue
                curr = float(data['Close'].iloc[-1])
                
                # 매도 체크
                for item in db['portfolio'][:]:
                    if item['ticker'] == t:
                        profit = (curr - item['buy_p']) / item['buy_p']
                        if profit >= 0.08 or profit <= -0.04:
                            db[b_key] += curr * item['qty']
                            db['logs'].append(f"[{now_str}] 💰 {t} 매도 ({profit*100:.1f}%)")
                            db['portfolio'].remove(item)

                # 매수 체크
                prev = float(data['Close'].iloc[-2])
                change = (curr - prev) / prev
                if change >= 0.025 and not any(p['ticker'] == t for p in db['portfolio']):
                    qty = (db[b_key] * 0.2) // curr
                    if qty > 0:
                        db[b_key] -= curr * qty
                        db['portfolio'].append({"ticker": t, "buy_p": curr, "qty": qty, "type": p_type})
                        db['logs'].append(f"[{now_str}] ✅ {t} 매수 (+{change*100:.1f}%)")
            except: continue

    db["scan_count"] += 1
    db["last_scan"] = now_str
    db['logs'].append(f"[{now_str}] 🤖 엔진 가동 완료 (누적 {db['scan_count']}회)")
    if len(db['logs']) > 50: db['logs'] = db['logs'][-50:]
    save_db(db)

# --- 3. [핵심] 크론잡 신호 감지 ---
# 쿼리 파라미터 방식이 안 먹힐 때를 대비해 감지 로직 강화
is_auto = False
params = st.query_params
if params.get("auto") == "true" or params.get("auto") == ["true"]:
    is_auto = True

if is_auto:
    run_trading_engine()
    st.write("### 🚀 ENGINE ACTIVE")
    st.stop()

# --- 4. UI 구성 ---
st.set_page_config(page_title="AI 종합관리", layout="wide")
db = load_db()

st.title("🤖 AI 자산 관리 시스템")
st.info(f"📊 **엔진 상태:** 마지막 스캔 - {db.get('last_scan', '기록 없음')} | **누적 스캔:** {db['scan_count']}회")

c1, c2, c3 = st.columns(3)
c1.metric("🇰🇷 국장", f"{db['balance_kr']:,.0f}원")
c2.metric("🇺🇸 미장", f"{db['balance_us']:,.0f}원")
c3.metric("🪙 코인", f"{db['balance_coin']:,.0f}원")

st.divider()

if st.button("🚀 즉시 스캔 가동", use_container_width=True):
    run_trading_engine()
    st.rerun()

if st.button("🔄 데이터 초기화", use_container_width=True):
    if os.path.exists(DB_FILE): os.remove(DB_FILE)
    st.rerun()

tab1, tab2 = st.tabs(["📜 거래 로그", "💼 포트폴리오"])
with tab1:
    for log in reversed(db.get('logs', [])): st.write(log)
with tab2:
    for item in db.get('portfolio', []): st.write(f"**[{item['type']}] {item['ticker']}** | {int(item['qty'])}주")
