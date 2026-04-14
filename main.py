import streamlit as st
import yfinance as yf
import datetime
import json
import os
import requests

# --- 1. 설정 ---
VERSION = "6.3-BYPASS"
DB_FILE = "trading_db.json"
WATCH_STOCK = ["005930.KS", "NVDA"] # 삼성전자, 엔비디아
WATCH_COIN = ["KRW-BTC", "KRW-ETH"] # 업비트 기준 비트코인, 이더리움

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

# --- 2. 시세 수신 (멀티 채널 방식) ---
def run_scan():
    db = load_db()
    now = get_now()
    now_ts = now.timestamp()
    
    if now_ts - db.get("last_ts", 0) < 270:
        return db

    results = []
    
    # [방법 1] 코인 시세 (업비트 직접 호출 - 차단 확률 거의 없음)
    for coin in WATCH_COIN:
        try:
            url = f"https://api.upbit.com/v1/ticker?markets={coin}"
            res = requests.get(url, timeout=5).json()
            price = res[0]['trade_price']
            results.append(f"{coin.split('-')[1]}:{price:,.0f}")
        except:
            results.append(f"{coin}:ERR")

    # [방법 2] 주식 시세 (야후 파이낸스 - 차단 우회 시도)
    for ticker in WATCH_STOCK:
        try:
            # Ticker 객체로 아주 가벼운 데이터만 요청
            t = yf.Ticker(ticker)
            p = t.fast_info['last_price']
            if p:
                results.append(f"{ticker.split('.')[0]}:{p:,.0f}")
            else:
                results.append(f"{ticker}:N/A")
        except:
            results.append(f"{ticker}:BLOCK")
            
    # 결과 저장
    db["scan_count"] += 1
    db["last_ts"] = now_ts
    log_entry = f"[{now.strftime('%H:%M')}] {' | '.join(results)}"
    db["logs"].append(log_entry)
    if len(db["logs"]) > 30: db["logs"] = db["logs"][-30:]
    save_db(db)
    return db

# --- 3. 실행 및 UI ---
db = run_scan()

st.set_page_config(page_title="모바일 트레이더", layout="centered")
st.title(f"📱 모바일 관제소 v{VERSION}")

# 상태 표시
c1, c2 = st.columns(2)
c1.metric("누적 스캔", f"{db['scan_count']}회")
c2.write(f"최종 업데이트: {get_now().strftime('%H:%M:%S')}")

st.divider()

# 로그 출력
if not db["logs"]:
    st.info("신호를 기다리는 중입니다 (5분 주기)")
else:
    for log in reversed(db["logs"]):
        st.write(log)

if st.button("🔄 즉시 새로고침"):
    st.rerun()
