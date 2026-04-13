import streamlit as st
import yfinance as yf
import datetime
import json
import os

# --- 0. 기본 설정 ---
VERSION = "2.0"
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

# --- 1. 데이터 로드 및 UI 선언 ---
st.set_page_config(page_title=f"AI Bot v{VERSION}", layout="wide")
db = load_db()

# 화면 상단 구성 (무조건 보임)
st.title("🤖 AI 자산 관리 시스템")
st.info(f"📊 **누적 스캔: {db.get('scan_count', 0)}회** | 마지막: {db.get('last_scan')}")

# 잔고 표시
c1, c2, c3 = st.columns(3)
c1.metric("🇰🇷 국장", f"{db.get('balance_kr', 0):,.0f}원")
c2.metric("🇺🇸 미장", f"{db.get('balance_us', 0):,.0f}$")
c3.metric("🪙 코인", f"{db.get('balance_coin', 0):,.0f}원")

st.divider()

# 버튼 배치
col1, col2 = st.columns(2)
with col1:
    btn_scan = st.button("🚀 즉시 스캔 가동", use_container_width=True)
with col2:
    if st.button("🔄 데이터 초기화", use_container_width=True):
        if os.path.exists(DB_FILE): os.remove(DB_FILE)
        st.rerun()

# --- 2. 엔진 실행 로직 (UI 아래에 위치) ---
now = get_now()
now_ts = now.timestamp()
last_ts = db.get("last_scan_timestamp", 0)

# 5분(300초) 경과 또는 버튼 클릭 시
if (now_ts - last_ts > 300) or btn_scan:
    # 횟수부터 즉시 올리고 저장 (서버 멈춤 대비)
    db["scan_count"] += 1
    db["last_scan"] = now.strftime('%Y-%m-%d %H:%M:%S')
    db["last_scan_timestamp"] = now_ts
    
    # 로그 추가
    log_msg = f"[{now.strftime('%H:%M:%S')}] 🤖 자동 스캔 완료" if not btn_scan else f"[{now.strftime('%H:%M:%S')}] 🚀 수동 스캔 완료"
    db['logs'].append(log_msg)
    if len(db['logs']) > 20: db['logs'] = db['logs'][-20:]
    
    save_db(db)
    
    # 시세 조회는 가장 마지막에 시도 (실패해도 숫자엔 영향 없음)
    try:
        yf.download("BTC-USD", period="1d", timeout=5, progress=False)
    except:
        pass
        
    st.rerun()

# --- 3. 로그 출력 ---
st.subheader("📜 최근 로그")
logs = db.get('logs', [])
for log in list(reversed(logs))[:10]:
    st.write(log)
