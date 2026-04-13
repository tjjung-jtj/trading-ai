import streamlit as st
import yfinance as yf
import datetime
import json
import os

# --- 0. 버전 설정 ---
VERSION = "1.7"

def get_now():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))

DB_FILE = "trading_db.json"

# 데이터 로드/저장 함수
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

# --- 1. 엔진 가동 함수 ---
def run_engine(reason="자동"):
    db = load_db()
    now_str = get_now().strftime('%Y-%m-%d %H:%M:%S')
    
    # [시세 스캔]
    tickers = ["BTC-USD", "NVDA", "005930.KS"]
    for t in tickers:
        try: yf.download(t, period="2d", interval="1h", progress=False)
        except: pass
    
    db["scan_count"] += 1
    db["last_scan"] = now_str
    db['logs'].append(f"[{now_str}] 🤖 {reason} 스캔 완료 (v{VERSION})")
    save_db(db)
    return db

# --- 2. 크론잡 체크 (UI를 방해하지 않음) ---
# 주소창에 ?auto=true가 있으면 조용히 엔진만 돌리고 넘어갑니다.
if st.query_params.get("auto") == "true":
    run_engine("자동(크론)")
    # 여기서 st.stop()을 하지 않아야 화면이 정상적으로 뜹니다.

# --- 3. 메인 UI 구성 ---
st.set_page_config(page_title=f"AI 종합관리 v{VERSION}", layout="wide")
db = load_db()

st.title("🤖 AI 자산 관리 시스템")

# 파란색 상태바
st.info(f"📊 **엔진 상태 (v{VERSION})** | 마지막 스캔: {db.get('last_scan')} | **누적 스캔: {db.get('scan_count', 0)}회**")

# 잔고 표시
c1, c2, c3 = st.columns(3)
c1.metric("🇰🇷 국장", f"{db.get('balance_kr', 0):,.0f}원")
c2.metric("🇺🇸 미장", f"{db.get('balance_us', 0):,.0f}원")
c3.metric("🪙 코인", f"{db.get('balance_coin', 0):,.0f}원")

st.divider()

# 버튼들
col1, col2 = st.columns(2)
with col1:
    if st.button("🚀 즉시 스캔 가동", use_container_width=True):
        db = run_engine("수동")
        st.rerun()
with col2:
    if st.button("🔄 데이터 초기화", use_container_width=True):
        if os.path.exists(DB_FILE): os.remove(DB_FILE)
        st.rerun()

# 로그 표시
st.subheader("📜 거래 로그")
for log in reversed(db.get('logs', [])):
    st.write(log)
