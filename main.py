import streamlit as st
import yfinance as yf
import datetime
import json
import os
import time
import threading

# --- 0. 설정 ---
VERSION = "4.0"
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

# --- 1. 백그라운드 엔진 (핵심) ---
def background_scanner():
    while True:
        db = load_db()
        now = get_now()
        now_ts = now.timestamp()
        last_ts = db.get("last_scan_timestamp", 0)

        # 5분(300초) 주기 체크
        if (now_ts - last_ts >= 300):
            db["scan_count"] += 1
            db["last_scan"] = now.strftime('%Y-%m-%d %H:%M:%S')
            db["last_scan_timestamp"] = now_ts
            
            try:
                data = yf.download(" ".join(WATCH_LIST), period="1d", interval="1m", progress=False, timeout=10, threads=False)
                if not data.empty:
                    prices = []
                    for t in WATCH_LIST:
                        try:
                            val = (data['Close'][t] if len(WATCH_LIST) > 1 else data['Close']).dropna().iloc[-1]
                            prices.append(f"{t}:{val:,.0f}")
                        except: prices.append(f"{t}:?")
                    db['logs'].append(f"[{now.strftime('%H:%M')}] 🚀 자동스캔: {' | '.join(prices)}")
                else:
                    db['logs'].append(f"[{now.strftime('%H:%M')}] ⚠️ 데이터 대기")
            except:
                db['logs'].append(f"[{now.strftime('%H:%M')}] ❌ 스캔 지연")

            if len(db['logs']) > 30: db['logs'] = db['logs'][-30:]
            save_db(db)
            print(f"Scan Completed: {db['last_scan']}") # Render 로그에서 확인 가능
            
        time.sleep(60) # 1분마다 주기 체크

# 서버 시작 시 백그라운드 스레드 딱 하나만 실행
if "scanner_started" not in st.session_state:
    thread = threading.Thread(target=background_scanner, daemon=True)
    thread.start()
    st.session_state["scanner_started"] = True

# --- 2. UI 구성 ---
st.set_page_config(page_title=f"AI Trading v{VERSION}", layout="wide")
db = load_db() # 최신 데이터 로드

st.title("🔥 AI 무한 동력 시스템")
st.info(f"이 엔진은 서버가 살아있는 동안 **백그라운드에서 5분마다** 스스로 작동합니다.")

st.success(f"**현재 버전: v{VERSION}** | 누적 스캔: **{db.get('scan_count', 0)}회**")

# (이하 UI 및 로그 출력 부분은 동일...)
st.subheader("📜 실시간 시스템 로그")
for log in list(reversed(db.get('logs', [])))[:15]:
    st.write(log)
