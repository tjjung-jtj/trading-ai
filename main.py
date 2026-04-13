import streamlit as st
import yfinance as yf
import datetime
import json
import os

# --- 0. 버전 설정 ---
VERSION = "1.8"

def get_now():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))

DB_FILE = "trading_db.json"

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding='utf-8') as f:
                return json.load(f)
        except: pass
    return {"balance_kr": 1000000, "balance_us": 1000000, "balance_coin": 1000000, "portfolio": [], "logs": [], "scan_count": 0, "last_scan": "없음"}

def save_db(data):
    with open(DB_FILE, "w", encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# --- 1. [핵심] 페이지 접속하자마자 실행 ---
# 다른 복잡한 체크 다 빼고, 주소에 auto=true만 있으면 즉시 실행합니다.
q = st.query_params
if q.get("auto") == "true" or q.get("auto") == ["true"]:
    db = load_db()
    now_str = get_now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 중복 실행 방지 (1분 안에는 한 번만)
    last_t = db.get("last_scan_raw", "")
    if last_t != now_str[:16]: # 분 단위가 다를 때만 실행
        db["scan_count"] += 1
        db["last_scan"] = now_str
        db["last_scan_raw"] = now_str[:16]
        db['logs'].append(f"[{now_str}] 🤖 자동 스캔 (v{VERSION})")
        
        # 실제 시세 체크 (짧게)
        try: yf.download("BTC-USD", period="1d", progress=False)
        except: pass
        
        save_db(db)
    
    # 로봇에게 응답만 주고 중단 (중요!)
    st.write("OK") 
    st.stop() 

# --- 2. 메인 UI (여기서부터는 동일) ---
st.set_page_config(page_title=f"AI Bot v{VERSION}")
db = load_db()

st.title("🤖 AI 자산 관리 시스템")
st.info(f"📊 **v{VERSION} 엔진 가동 중** | 누적 스캔: {db.get('scan_count', 0)}회")
st.write(f"마지막 스캔 일시: {db.get('last_scan')}")

if st.button("🚀 즉시 스캔"):
    # 버튼 로직
    db["scan_count"] += 1
    db["last_scan"] = get_now().strftime('%Y-%m-%d %H:%M:%S')
    save_db(db)
    st.rerun()

st.subheader("📜 최근 로그")
for log in reversed(db.get('logs', []))[:10]:
    st.write(log)
