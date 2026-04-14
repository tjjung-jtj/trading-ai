import streamlit as st
import yfinance as yf
import datetime
import json
import os

# --- 0. 설정 ---
VERSION = "2.9"
DB_FILE = "trading_db.json"
WATCH_LIST = ["BTC-USD", "ETH-USD", "NVDA", "TSLA", "005930.KS", "000660.KS"]

def get_now():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))

def load_db():
    try:
        if os.path.exists(DB_FILE):
            with open(DB_FILE, "r", encoding='utf-8') as f:
                return json.load(f)
    except: pass
    return {"balance_kr": 1000000, "balance_us": 1000, "balance_coin": 1000000, "logs": [], "scan_count": 0, "last_scan": "없음", "last_scan_timestamp": 0}

def save_db(data):
    try:
        with open(DB_FILE, "w", encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except: pass

# --- 1. 엔진 가동 (가장 먼저 실행) ---
db = load_db()
now = get_now()
now_ts = now.timestamp()
last_ts = db.get("last_scan_timestamp", 0)

# [수정] 5분이 지났다면 "즉시" 저장부터 실행
if (now_ts - last_ts > 290):
    db["scan_count"] += 1
    db["last_scan"] = now.strftime('%Y-%m-%d %H:%M:%S')
    db["last_scan_timestamp"] = now_ts
    # 시세 조회 전에 일단 숫자부터 저장 (서버 뻗기 방지)
    save_db(db)
    
    # 그 다음 시세 조회 시도
    try:
        data = yf.download(" ".join(WATCH_LIST), period="1d", interval="1m", progress=False, timeout=10, threads=False)
        if not data.empty:
            price_summaries = []
            for ticker in WATCH_LIST:
                try:
                    ticker_df = data['Close'][ticker] if len(WATCH_LIST) > 1 else data['Close']
                    valid_series = ticker_df.dropna()
                    price = f"{valid_series.iloc[-1]:,.0f}" if not valid_series.empty else "휴장"
                    price_summaries.append(f"{ticker}:{price}")
                except: price_summaries.append(f"{ticker}:?")
            db['logs'].append(f"[{now.strftime('%H:%M')}] ✅ { ' | '.join(price_summaries) }")
        else:
            db['logs'].append(f"[{now.strftime('%H:%M')}] ⚠️ 데이터 수신 지연")
    except Exception as e:
        db['logs'].append(f"[{now.strftime('%H:%M')}] ❌ 엔진지연")
    
    save_db(db)

# [수정] 로봇 모드 확인 (더 넓은 범위 허용)
is_robot = False
params = st.query_params.to_dict()
if params.get("auto") == "true" or params.get("type") == "robot":
    is_robot = True

if is_robot:
    st.write("OK")
    st.stop()

# --- 2. UI 구성 ---
st.set_page_config(page_title=f"AI Trading v{VERSION}", layout="wide")
st.title("📊 AI 자동 매매 시스템")
st.success(f"**엔진 가동 중 (v{VERSION})** | 누적 스캔: **{db.get('scan_count', 0)}회**")

c1, c2, c3 = st.columns(3)
c1.metric("🇰🇷 국장", f"{db.get('balance_kr', 0):,.0f}원")
c2.metric("🇺🇸 미장", f"{db.get('balance_us', 0):,.0f}$")
c3.metric("🪙 코인", f"{db.get('balance_coin', 0):,.0f}원")

st.divider()
if st.button("🚀 즉시 강제 스캔", use_container_width=True):
    db["last_scan_timestamp"] = 0
    save_db(db)
    st.rerun()

st.subheader("📜 시스템 로그")
for log in list(reversed(db.get('logs', [])))[:15]:
    st.write(log)
