import streamlit as st
import yfinance as yf
import datetime
import json
import os

# --- 1. 설정 ---
VERSION = "6.2-FIX"
DB_FILE = "trading_db.json"
# 시세가 잘 나오던 핵심 종목
WATCH_LIST = ["005930.KS", "NVDA", "BTC-USD", "ETH-USD"]

def get_now():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding='utf-8') as f:
                return json.load(f)
        except: pass
    return {"logs": [], "scan_count": 0, "last_ts": 0}

def save_db(data):
    try:
        with open(DB_FILE, "w", encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except: pass

# --- 2. 시세 수신 (가장 단순한 구조로 복구) ---
def run_scan():
    db = load_db()
    now = get_now()
    now_ts = now.timestamp()
    
    # 4분 30초 이내 중복 실행 방지
    if now_ts - db.get("last_ts", 0) < 270:
        return db

    results = []
    for ticker in WATCH_LIST:
        try:
            # 시세가 잘 나오던 기본 download 방식
            df = yf.download(ticker, period="1d", interval="1m", progress=False, timeout=10)
            if not df.empty:
                last_p = df['Close'].iloc[-1]
                # 숫자 포맷팅 (정수형)
                results.append(f"{ticker}:{last_p:,.0f}")
            else:
                results.append(f"{ticker}:N/A") # 데이터가 비어있을 때
        except Exception as e:
            results.append(f"{ticker}:ERR") # 에러 발생 시
            
    # 결과가 있으면 로그 저장
    if results:
        db["scan_count"] += 1
        db["last_ts"] = now_ts
        log_entry = f"[{now.strftime('%H:%M')}] {' | '.join(results)}"
        db["logs"].append(log_entry)
        
        if len(db["logs"]) > 30:
            db["logs"] = db["logs"][-30:]
        save_db(db)
    return db

# --- 3. 실행 및 UI ---
db = run_scan()

st.set_page_config(page_title="AI 관제소", layout="centered")
st.title(f"📱 모바일 관제소 v{VERSION}")

# 상태 요약
col1, col2 = st.columns(2)
col1.metric("누적 스캔", f"{db['scan_count']}회")
col2.write(f"현재 시간: {get_now().strftime('%H:%M:%S')}")

st.divider()

# 로그 출력
if not db["logs"]:
    st.info("데이터를 기다리는 중입니다... 5분 뒤 다시 확인하세요.")
else:
    for log in reversed(db["logs"]):
        st.write(log)

if st.button("🔄 즉시 새로고침"):
    st.rerun()
