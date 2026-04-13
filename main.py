import streamlit as st
import yfinance as yf
import datetime
import json
import os
import time

# --- 0. 기본 설정 ---
VERSION = "2.5"
DB_FILE = "trading_db.json"
# 감시할 종목 리스트 (원하시는 만큼 추가 가능)
WATCH_LIST = ["BTC-USD", "ETH-USD", "NVDA", "TSLA", "005930.KS", "000660.KS"]

def get_now():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))

def load_db():
    try:
        if os.path.exists(DB_FILE):
            with open(DB_FILE, "r", encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return {"balance_kr": 1000000, "balance_us": 1000, "balance_coin": 1000000, "logs": [], "scan_count": 0, "last_scan": "없음", "last_scan_timestamp": 0}

def save_db(data):
    try:
        with open(DB_FILE, "w", encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        st.error(f"데이터 저장 실패: {e}")

# --- 1. 엔진 가동 (가장 상단 배치) ---
db = load_db()
now = get_now()
now_ts = now.timestamp()
last_ts = db.get("last_scan_timestamp", 0)

# 5분 주기 체크 (290초)
if (now_ts - last_ts > 290):
    # 즉시 카운트부터 올리고 세션 상태에 저장 (가장 빠름)
    db["scan_count"] += 1
    db["last_scan"] = now.strftime('%Y-%m-%d %H:%M:%S')
    db["last_scan_timestamp"] = now_ts
    
    # [핵심] 시세 조회 실패가 전체를 멈추지 않도록 분리
    try:
        # threads=False로 설정하여 저사양 서버에서 꼬임 방지
        data = yf.download(" ".join(WATCH_LIST), period="1d", interval="1m", progress=False, timeout=10, threads=False)
        
        if not data.empty:
            # 예시: 비트코인 가격 추출
            current_price = data['Close']['BTC-USD'].iloc[-1]
            db['logs'].append(f"[{now.strftime('%H:%M')}] ✅ 스캔 성공 (BTC: ${current_price:,.0f})")
            # --- 여기에 매매 로직 추가 가능 ---
        else:
            db['logs'].append(f"[{now.strftime('%H:%M')}] ⚠️ 데이터 빈값 수신")
    except Exception as e:
        db['logs'].append(f"[{now.strftime('%H:%M')}] ❌ 시세조회 지연/오류")

    # 로그 관리 및 저장
    if len(db['logs']) > 30: db['logs'] = db['logs'][-30:]
    save_db(db)
    
    # 업타임로봇 접속이면 UI를 그리지 않고 즉시 종료하여 자원 확보
    if st.query_params.get("auto") == "true":
        st.write("OK")
        st.stop()

# --- 2. UI 구성 ---
st.set_page_config(page_title=f"AI Trading Bot v{VERSION}", layout="wide")
st.title("📊 AI 자동 매매 통합 관제")

# 상태 요약
st.success(f"**엔진 가동 중 (v{VERSION})** | 누적 가동: **{db.get('scan_count', 0)}회** | 마지막: {db.get('last_scan')}")

# 잔고/포트폴리오
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
st.subheader("📜 시스템 로그")
for log in list(reversed(db.get('logs', [])))[:10]:
    st.write(log)
