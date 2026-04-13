import streamlit as st
import yfinance as yf
import datetime
import json
import os

VERSION = "1.9"

def get_now():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))

DB_FILE = "trading_db.json"

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding='utf-8') as f:
                return json.load(f)
        except: pass
    return {"balance_kr": 1000000, "balance_us": 1000000, "balance_coin": 1000000, "portfolio": [], "logs": [], "scan_count": 0, "last_scan": "없음", "last_scan_timestamp": 0}

def save_db(data):
    with open(DB_FILE, "w", encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# --- [핵심] 자동 실행 로직 (파라미터 없이도 작동) ---
db = load_db()
now = get_now()
now_ts = now.timestamp()
last_ts = db.get("last_scan_timestamp", 0)

# 마지막 스캔 후 280초(약 4.5분)가 지났다면 누구든 접속 시 엔진 가동!
if now_ts - last_ts > 280:
    now_str = now.strftime('%Y-%m-%d %H:%M:%S')
    
    # 시세 체크 (간략화)
    try: yf.download("BTC-USD", period="1d", progress=False)
    except: pass
    
    db["scan_count"] += 1
    db["last_scan"] = now_str
    db["last_scan_timestamp"] = now_ts
    db['logs'].append(f"[{now_str}] 🤖 자동 엔진 가동 (v{VERSION})")
    
    if len(db['logs']) > 50: db['logs'] = db['logs'][-50:]
    save_db(db)

# --- UI 부분 ---
st.set_page_config(page_title=f"AI Bot v{VERSION}")
st.title("🤖 AI 자산 관리 시스템")
st.info(f"📊 **누적 스캔: {db.get('scan_count', 0)}회** | 마지막: {db.get('last_scan')}")

if st.button("🚀 즉시 스캔"):
    last_ts = 0 # 강제 실행을 위해 타임스탬프 초기화
    st.rerun()

st.subheader("📜 로그")
logs = db.get('logs', [])
for log in list(reversed(logs))[:10]:
    st.write(log)
