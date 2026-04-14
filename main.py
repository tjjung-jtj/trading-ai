import streamlit as st
import yfinance as yf
import datetime
import json
import os

# --- 0. 설정 ---
VERSION = "2.8"
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

# --- 1. 엔진 핵심 로직 (UI 실행 전 실행) ---
db = load_db()
now = get_now()
now_ts = now.timestamp()
last_ts = db.get("last_scan_timestamp", 0)

# [핵심] 로봇 접속 여부 확인 (최신 Streamlit 호환 방식)
is_robot = False
if "auto" in st.query_params and st.query_params["auto"] == "true":
    is_robot = True

# 5분(290초) 주기 체크
if (now_ts - last_ts > 290):
    db["scan_count"] += 1
    db["last_scan"] = now.strftime('%Y-%m-%d %H:%M:%S')
    db["last_scan_timestamp"] = now_ts
    
    try:
        # 시세 스캔 (threads=False로 서버 과부하 방지)
        data = yf.download(" ".join(WATCH_LIST), period="1d", interval="1m", progress=False, timeout=10, threads=False)
        
        if not data.empty:
            price_summaries = []
            for ticker in WATCH_LIST:
                try:
                    ticker_df = data['Close'][ticker] if len(WATCH_LIST) > 1 else data['Close']
                    valid_series = ticker_df.dropna()
                    if not valid_series.empty:
                        last_p = valid_series.iloc[-1]
                        price_summaries.append(f"{ticker}:{last_p:,.0f}")
                    else:
                        price_summaries.append(f"{ticker}:휴장")
                except:
                    price_summaries.append(f"{ticker}:오류")
            
            summary_text = " | ".join(price_summaries)
            db['logs'].append(f"[{now.strftime('%H:%M')}] ✅ {summary_text}")
        else:
            db['logs'].append(f"[{now.strftime('%H:%M')}] ⚠️ 데이터 수신 실패")
            
    except Exception as e:
        db['logs'].append(f"[{now.strftime('%H:%M')}] ❌ 엔진지연: {str(e)[:15]}")

    if len(db['logs']) > 30: db['logs'] = db['logs'][-30:]
    save_db(db)
    
    # [핵심] 로봇이면 여기서 종료 (UI 안 그림)
    if is_robot:
        st.write("OK")
        st.stop()

# --- 2. 메인 UI (사람에게만 보임) ---
st.set_page_config(page_title=f"AI Trading v{VERSION}", layout="wide")
st.title("📊 AI 자동 매매 통합 관제")

st.success(f"**엔진 가동 중 (v{VERSION})** | 누적 스캔: **{db.get('scan_count', 0)}회** | 마지막: {db.get('last_scan')}")

c1, c2, c3 = st.columns(3)
c1.metric("🇰🇷 한국 주식", f"{db.get('balance_kr', 0):,.0f}원")
c2.metric("🇺🇸 미국 주식", f"{db.get('balance_us', 0):,.0f}$")
c3.metric("🪙 가상 자산", f"{db.get('balance_coin', 0):,.0f}원")

st.divider()

col1, col2 = st.columns(2)
with col1:
    if st.button("🚀 즉시 강제 스캔", use_container_width=True):
        db["last_scan_timestamp"] = 0
        save_db(db)
        st.rerun()
with col2:
    if st.button("🔄 데이터 초기화", use_container_width=True):
        if os.path.exists(DB_FILE): os.remove(DB_FILE)
        st.rerun()

st.subheader("📜 실시간 시스템 로그")
logs = db.get('logs', [])
if logs:
    for log in list(reversed(logs))[:15]:
        st.write(log)
