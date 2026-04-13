import streamlit as st
import yfinance as yf
import datetime
import json
import os
import time

# --- 0. 기본 설정 ---
VERSION = "1.9.1"
DB_FILE = "trading_db.json"

def get_now():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding='utf-8') as f:
                return json.load(f)
        except: pass
    return {"balance_kr": 1000000, "balance_us": 1000, "balance_coin": 1000000, "portfolio": [], "logs": [], "scan_count": 0, "last_scan": "없음", "last_scan_timestamp": 0}

def save_db(data):
    with open(DB_FILE, "w", encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# --- 1. 화면 구성 (가장 먼저 실행) ---
st.set_page_config(page_title=f"AI Bot v{VERSION}", layout="wide")
db = load_db()

st.title("🤖 AI 자산 관리 시스템")

# 상태 바 (누적 스캔 확인용)
st.info(f"📊 **누적 스캔: {db.get('scan_count', 0)}회** | 마지막: {db.get('last_scan')}")

# 잔고/버튼 UI를 엔진보다 먼저 그립니다.
c1, c2, c3 = st.columns(3)
c1.metric("🇰🇷 국장", f"{db.get('balance_kr', 0):,.0f}원")
c2.metric("🇺🇸 미장", f"{db.get('balance_us', 0):,.0f}$")
c3.metric("🪙 코인", f"{db.get('balance_coin', 0):,.0f}원")

st.divider()

col1, col2 = st.columns(2)
with col1:
    btn_scan = st.button("🚀 즉시 스캔 가동", use_container_width=True)
with col2:
    if st.button("🔄 데이터 초기화", use_container_width=True):
        if os.path.exists(DB_FILE): os.remove(DB_FILE)
        st.rerun()

# --- 2. 엔진 가동 로직 (UI 아래에 배치하여 방해 방지) ---
now = get_now()
now_ts = now.timestamp()
last_ts = db.get("last_scan_timestamp", 0)

# 자동 실행 (5분 경과) 또는 버튼 클릭 시
if (now_ts - last_ts > 280) or btn_scan:
    with st.spinner("데이터 스캔 중..."):
        now_str = now.strftime('%Y-%m-%d %H:%M:%S')
        
        # 실제 시세 체크 (에러 방지 처리)
        try:
            yf.download("BTC-USD", period="1d", progress=False, timeout=10)
        except Exception as e:
            db['logs'].append(f"[{now_str}] ⚠️ 시세조회 오류 발생")

        db["scan_count"] += 1
        db["last_scan"] = now_str
        db["last_scan_timestamp"] = now_ts
        db['logs'].append(f"[{now_str}] 🤖 스캔 완료 (v{VERSION})")
        
        if len(db['logs']) > 30: db['logs'] = db['logs'][-30:]
        save_db(db)
        st.rerun() # 데이터 갱신을 위해 화면 재시작

# --- 3. 로그 출력 ---
st.subheader("📜 최근 로그")
logs = db.get('logs', [])
if logs:
    for log in list(reversed(logs))[:10]:
        st.write(log)
else:
    st.write("아직 로그가 없습니다.")
