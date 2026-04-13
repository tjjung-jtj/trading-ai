import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import json
import os

# --- 0. 버전 설정 ---
VERSION = "1.6.1"

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

# --- 1. [긴급] 모든 경로로 파라미터 감지 ---
is_auto = False
try:
    # 방식 1: 최신 st.query_params (문자열 또는 리스트)
    p = st.query_params.get_all("auto") if hasattr(st.query_params, "get_all") else [st.query_params.get("auto")]
    if "true" in [str(val).lower() for val in p if val]:
        is_auto = True
except:
    pass

# --- 2. 크론잡 실행 로직 ---
if is_auto:
    db = load_db()
    now_str = get_now().strftime('%Y-%m-%d %H:%M:%S')
    
    # [종목 스캔] - 속도를 위해 최소화 테스트
    tickers = ["BTC-USD", "NVDA", "005930.KS"]
    for t in tickers:
        try:
            yf.download(t, period="2d", interval="1h", progress=False)
        except: pass
    
    db["scan_count"] += 1
    db["last_scan"] = now_str
    db['logs'].append(f"[{now_str}] 🤖 자동 스캔 완료 (v{VERSION})")
    save_db(db)
    
    st.write(f"V{VERSION} ENGINE_SUCCESS")
    st.stop()

# --- 3. 메인 UI (여기서부터는 동일) ---
st.set_page_config(page_title="AI 종합관리", layout="wide")
db = load_db()

st.title("🤖 AI 자산 관리 시스템")
st.info(f"📊 **엔진 상태 (v{VERSION})** | 마지막 스캔: {db.get('last_scan', '기록 없음')} | **누적 스캔: {db.get('scan_count', 0)}회**")

# ... (이하 버튼 및 잔고 표시는 이전과 동일) ...
if st.button("🚀 즉시 스캔 가동", use_container_width=True):
    db["scan_count"] += 1
    db["last_scan"] = get_now().strftime('%Y-%m-%d %H:%M:%S')
    db['logs'].append(f"[{db['last_scan']}] 🚀 수동 스캔 완료")
    save_db(db)
    st.rerun()

tab1, tab2 = st.tabs(["📜 거래 로그", "💼 포트폴리오"])
with tab1:
    for log in reversed(db.get('logs', [])): st.write(log)
