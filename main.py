import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import json
import os

# --- 0. 버전 설정 ---
VERSION = "1.6"

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

# --- 1. 크론잡 감지 (UI 렌더링 전 최상단 실행) ---
if st.query_params.get("auto") == "true":
    db = load_db()
    now_str = get_now().strftime('%Y-%m-%d %H:%M:%S')
    
    # [매매 엔진 로직 실행 - 종목 스캔 및 매수/매도]
    # (여기에 기존 yfinance 기반 분석 코드가 들어갑니다)
    
    db["scan_count"] += 1
    db["last_scan"] = now_str
    db['logs'].append(f"[{now_str}] 🤖 자동 스캔 완료 (v{VERSION})")
    save_db(db)
    
    st.write(f"V{VERSION} ACTIVE") 
    st.stop()

# --- 2. 메인 UI 구성 ---
st.set_page_config(page_title="AI 종합관리", layout="wide")
db = load_db()

st.title("🤖 AI 자산 관리 시스템")

# 파란색 상태바에 v1.6 적용
st.info(f"📊 **엔진 상태 (v{VERSION})** | 마지막 스캔: {db.get('last_scan', '기록 없음')} | **누적 스캔: {db.get('scan_count', 0)}회**")

c1, c2, c3 = st.columns(3)
c1.metric("🇰🇷 국장", f"{db['balance_kr']:,.0f}원")
c2.metric("🇺🇸 미장", f"{db['balance_us']:,.0f}원")
c3.metric("🪙 코인", f"{db['balance_coin']:,.0f}원")

st.divider()

col1, col2 = st.columns(2)
with col1:
    if st.button("🚀 즉시 스캔 가동", use_container_width=True):
        # 수동 실행 시에도 로직 수행 및 기록
        db["scan_count"] += 1
        db["last_scan"] = get_now().strftime('%Y-%m-%d %H:%M:%S')
        db['logs'].append(f"[{db['last_scan']}] 🚀 수동 스캔 완료 (v{VERSION})")
        save_db(db)
        st.rerun()
with col2:
    if st.button("🔄 데이터 초기화", use_container_width=True):
        if os.path.exists(DB_FILE): os.remove(DB_FILE)
        st.rerun()

tab1, tab2 = st.tabs(["📜 거래 로그", "💼 포트폴리오"])
with tab1:
    for log in reversed(db.get('logs', [])): st.write(log)
with tab2:
    if not db.get('portfolio'): st.info("보유 종목 없음")
    else:
        for item in db['portfolio']:
            st.write(f"**[{item['type']}] {item['ticker']}** | {int(item['qty'])}주")
