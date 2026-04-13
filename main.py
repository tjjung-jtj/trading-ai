import streamlit as st
import yfinance as yf
import datetime
import json
import os

# --- 0. 기본 설정 ---
VERSION = "1.9.2"
DB_FILE = "trading_db.json"

def get_now():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding='utf-8') as f:
                return json.load(f)
        except: pass
    return {"balance_kr": 1000000, "balance_us": 1000, "balance_coin": 1000000, "logs": [], "scan_count": 0, "last_scan": "없음", "last_scan_timestamp": 0}

def save_db(data):
    with open(DB_FILE, "w", encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# --- 1. 자동 실행 로직 (UI 그리기 전에 초고속 실행) ---
db = load_db()
now = get_now()
now_ts = now.timestamp()
last_ts = db.get("last_scan_timestamp", 0)

# 280초(약 4.5분) 지났을 때 실행
if (now_ts - last_ts > 280):
    now_str = now.strftime('%H:%M:%S')
    db["scan_count"] += 1
    db["last_scan"] = now.strftime('%Y-%m-%d %H:%M:%S')
    db["last_scan_timestamp"] = now_ts
    db['logs'].append(f"[{now_str}] 🤖 자동 스캔 성공 (v{VERSION})")
    
    # [주의] 무거운 시세 조회는 나중에 하고, 일단 횟수부터 저장!
    save_db(db)
    
    # 로봇 접속일 경우 여기서 끊어줘서 Render 부하를 줄임
    if st.query_params.get("auto") == "true":
        st.write("OK")
        st.stop()

# --- 2. UI 구성 ---
st.set_page_config(page_title=f"AI Bot v{VERSION}")
st.title("🤖 AI 자산 관리 시스템")
st.info(f"📊 **누적 스캔: {db.get('scan_count', 0)}회** | 마지막: {db.get('last_scan')}")

col1, col2 = st.columns(2)
with col1:
    if st.button("🚀 즉시 스캔 가동", use_container_width=True):
        db["last_scan_timestamp"] = 0 # 강제 실행 트리거
        save_db(db)
        st.rerun()

st.subheader("📜 로그")
logs = db.get('logs', [])
for log in list(reversed(logs))[:10]:
    st.write(log)
