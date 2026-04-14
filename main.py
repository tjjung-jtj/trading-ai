import streamlit as st
import datetime
import json
import os
import requests

# --- 1. 설정 ---
VERSION = "7.2-AUTO-FIX"
DB_FILE = "trading_db.json"

def get_now():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))

# 세션 상태를 이용해 서버가 켜져 있는 동안 로그 유지
if "memory_logs" not in st.session_state:
    st.session_state.memory_logs = []

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding='utf-8') as f:
                return json.load(f)
        except: pass
    return {"logs": [], "last_ts": 0}

def save_db(data):
    try:
        with open(DB_FILE, "w", encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except: pass

# --- 2. 통합 스캔 엔진 ---
def run_scan():
    db = load_db()
    now = get_now()
    now_ts = now.timestamp()
    
    # [핵심 수정] 5분 체크를 4분(240초)으로 살짝 줄여서 크론잡 주기에 더 잘 걸리게 함
    last_ts = db.get("last_ts", 0)
    
    # 시세 및 이슈 수집
    headers = {'User-Agent': 'Mozilla/5.0'}
    prices = {"BTC": "N/A", "NVDA": "N/A", "삼성": "N/A"}
    
    try:
        # 코인/주식 수신 (실패해도 진행)
        btc = requests.get("https://api.upbit.com/v1/ticker?markets=KRW-BTC", timeout=3).json()
        prices["BTC"] = f"{btc[0]['trade_price']:,.0f}"
        
        nvda_url = "https://query1.finance.yahoo.com/v8/finance/chart/NVDA?interval=1m&range=1d"
        n_res = requests.get(nvda_url, headers=headers, timeout=3).json()
        prices["NVDA"] = f"{n_res['chart']['result'][0]['meta']['regularMarketPrice']:.1f}"
    except: pass

    # 로그 생성
    price_str = f"BTC:{prices['BTC']} | NVDA:{prices['NVDA']}"
    log_entry = f"[{now.strftime('%H:%M')}] {price_str} | 스캔성공"

    # 5분이 지났거나, 로그가 아예 없으면 기록
    if now_ts - last_ts >= 240 or not db["logs"]:
        db["logs"].append(log_entry)
        db["last_ts"] = now_ts
        if len(db["logs"]) > 30: db["logs"] = db["logs"][-30:]
        save_db(db)
        # 메모리에도 백업 (서버 재시작 대비)
        st.session_state.memory_logs = db["logs"]
    
    return db

# --- 3. UI ---
st.set_page_config(page_title="Auto Scan v7.2")
# 접속하자마자 스캔 로직 가동
db_data = run_scan()

st.title(f"🚀 스캔 감시자 v{VERSION}")
st.write(f"현재 시간: {get_now().strftime('%Y-%m-%d %H:%M:%S')}")

st.divider()

# 로그 출력
st.subheader("📜 5분 주기 기록")
display_logs = db_data.get("logs", [])
if not display_logs:
    st.warning("아직 기록된 로그가 없습니다. 크론잡 작동을 기다리는 중...")
else:
    for log in reversed(display_logs):
        st.write(log)

if st.button("🔄 수동 강제 스캔"):
    # 버튼 누를 때는 시간 상관없이 기록하도록 로직 추가 가능
    st.rerun()
