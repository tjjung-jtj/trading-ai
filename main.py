import streamlit as st
import yfinance as yf
import datetime
import json
import os

# --- 0. 설정 ---
VERSION = "2.6"
DB_FILE = "trading_db.json"
# 감시할 모든 종목 리스트
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

# --- 1. 엔진 핵심 로직 ---
db = load_db()
now = get_now()
now_ts = now.timestamp()
last_ts = db.get("last_scan_timestamp", 0)

if (now_ts - last_ts > 290):
    db["scan_count"] += 1
    db["last_scan"] = now.strftime('%Y-%m-%d %H:%M:%S')
    db["last_scan_timestamp"] = now_ts
    
    try:
        # 모든 종목 데이터 다운로드
        data = yf.download(" ".join(WATCH_LIST), period="1d", interval="1m", progress=False, timeout=10, threads=False)
        
        if not data.empty:
            price_summaries = []
            # [수정 포인트] WATCH_LIST에 있는 모든 종목의 마지막 가격을 수집
            for ticker in WATCH_LIST:
                try:
                    # 다중 인덱스 처리 (종목이 여러개일 때 Close['종목명'])
                    if len(WATCH_LIST) > 1:
                        current_p = data['Close'][ticker].iloc[-1]
                    else:
                        current_p = data['Close'].iloc[-1]
                    
                    price_summaries.append(f"{ticker}:{current_p:,.0f}")
                except:
                    price_summaries.append(f"{ticker}:에러")
            
            # 로그에 모든 종목 시세 요약본 저장
            summary_text = " | ".join(price_summaries)
            db['logs'].append(f"[{now.strftime('%H:%M')}] ✅ 전종목 스캔: {summary_text}")
        else:
            db['logs'].append(f"[{now.strftime('%H:%M')}] ⚠️ 시세 데이터 수신 실패")
            
    except Exception as e:
        db['logs'].append(f"[{now.strftime('%H:%M')}] ❌ 엔진 오류: {str(e)[:20]}")

    if len(db['logs']) > 30: db['logs'] = db['logs'][-30:]
    save_db(db)
    
    if st.query_params.get("auto") == "true":
        st.write("OK")
        st.stop()

# --- 2. UI 구성 ---
st.set_page_config(page_title=f"AI Trading v{VERSION}", layout="wide")
st.title("📊 AI 자동 매매 통합 관제")

# 상태 요약
st.success(f"**엔진 가동 중 (v{VERSION})** | 누적 가동: **{db.get('scan_count', 0)}회** | 마지막: {db.get('last_scan')}")

# 잔고 표시
c1, c2, c3 = st.columns(3)
c1.metric("🇰🇷 한국 주식", f"{db.get('balance_kr', 0):,.0f}원")
c2.metric("🇺🇸 미국 주식", f"{db.get('balance_us', 0):,.0f}$")
c3.metric("🪙 가상 자산", f"{db.get('balance_coin', 0):,.0f}원")

st.divider()

if st.button("🚀 즉시 강제 엔진 가동", use_container_width=True):
    db["last_scan_timestamp"] = 0
    save_db(db)
    st.rerun()

# 로그 출력
st.subheader("📜 시스템 실시간 로그")
for log in list(reversed(db.get('logs', [])))[:15]: # 로그를 조금 더 많이 보여줌
    st.write(log)
