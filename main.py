import streamlit as st
import yfinance as yf
import datetime
import json
import os
import time
import threading

# --- 0. 설정 ---
VERSION = "4.2"
DB_FILE = "trading_db.json"
# 테스트를 위해 가장 확실한 종목 3개만 먼저 시도
WATCH_LIST = ["BTC-USD", "NVDA", "TSLA"]

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

# --- 1. 시세 수신 함수 (진단 모드) ---
def get_prices():
    results = []
    for t in WATCH_LIST:
        try:
            # fast_info를 사용하여 아주 가벼운 데이터만 요청
            ticker = yf.Ticker(t)
            price = ticker.fast_info['last_price']
            if price:
                results.append(f"{t}:{price:,.2f}")
            else:
                results.append(f"{t}:값없음")
        except Exception as e:
            # 에러가 나면 에러 메시지 앞부분을 로그에 찍음
            error_msg = str(e)[:10]
            results.append(f"{t}:실패({error_msg})")
        time.sleep(0.5)
    
    final_text = " | ".join(results)
    return final_text if final_text else "데이터 수신 시도 안됨"

# --- 2. 백그라운드 엔진 ---
def background_scanner():
    while True:
        db = load_db()
        now = get_now()
        now_ts = now.timestamp()
        last_ts = db.get("last_scan_timestamp", 0)

        if (now_ts - last_ts >= 300):
            db["scan_count"] += 1
            db["last_scan"] = now.strftime('%Y-%m-%d %H:%M:%S')
            db["last_scan_timestamp"] = now_ts
            
            # 시세 가져오기
            price_output = get_prices()
            db['logs'].append(f"[{now.strftime('%H:%M')}] {price_output}")

            if len(db['logs']) > 30: db['logs'] = db['logs'][-30:]
            save_db(db)
            
        time.sleep(30)

if "scanner_started" not in st.session_state:
    thread = threading.Thread(target=background_scanner, daemon=True)
    thread.start()
    st.session_state["scanner_started"] = True

# --- 3. UI ---
st.set_page_config(page_title=f"AI Trading v{VERSION}", layout="wide")
db = load_db()
st.title(f"🚀 시세 진단 엔진 (v{VERSION})")
st.write(f"마지막 스캔: {db.get('last_scan')}")

st.divider()
st.subheader("📜 시스템 로그 (시세 확인용)")
logs = db.get('logs', [])
if not logs:
    st.write("아직 로그가 없습니다. 잠시만 기다려주세요.")
else:
    for log in list(reversed(logs))[:20]:
        st.write(log)
