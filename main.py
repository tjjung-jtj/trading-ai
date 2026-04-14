import streamlit as st
import datetime
import json
import os
import requests

# --- 1. 설정 ---
VERSION = "6.5-FIXED"
DB_FILE = "trading_db.json"

def get_now():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))

# --- 2. 시세 수신 (야후 대신 직접 호출) ---
def get_data():
    results = []
    
    # [코인] 업비트 - 아주 잘 됨
    try:
        res = requests.get("https://api.upbit.com/v1/ticker?markets=KRW-BTC", timeout=5)
        price = res.json()[0]['trade_price']
        results.append(f"BTC:{price:,.0f}")
    except:
        results.append("BTC:Err")

    # [주식] 야후 차단을 피해 다른 방식으로 수신 시도
    # (엔비디아 시세를 가져오는 예비 경로)
    try:
        # yfinance 대신 브라우저인 척 속여서 가져오기
        headers = {'User-Agent': 'Mozilla/5.0'}
        url = "https://query1.finance.yahoo.com/v8/finance/chart/NVDA?interval=1m&range=1d"
        res = requests.get(url, headers=headers, timeout=5)
        data = res.json()
        price = data['chart']['result'][0]['meta']['regularMarketPrice']
        results.append(f"NVDA:{price:,.1f}")
    except:
        results.append("NVDA:Wait") # 차단 시 대기 표시
        
    return " | ".join(results)

# --- 3. 실행 로직 ---
db = {"logs": []}
if os.path.exists(DB_FILE):
    try:
        with open(DB_FILE, "r", encoding='utf-8') as f:
            db = json.load(f)
    except: pass

# 5분마다 자동 기록 (크론잡 대응)
now = get_now()
last_ts = db.get("last_ts", 0)
if now.timestamp() - last_ts >= 300:
    current_data = get_data()
    db["last_ts"] = now.timestamp()
    db["logs"].append(f"[{now.strftime('%H:%M')}] {current_data}")
    if len(db["logs"]) > 30: db["logs"] = db["logs"][-30:]
    
    try:
        with open(DB_FILE, "w", encoding='utf-8') as f:
            json.dump(db, f, indent=4, ensure_ascii=False)
    except: pass

# --- 4. UI ---
st.set_page_config(page_title="모바일 관제소", layout="centered")
st.title(f"📱 실시간 관제소 v{VERSION}")

# 현재가 한눈에 보기
st.subheader("💡 현재 시세 확인")
st.info(get_data()) 

st.divider()
st.subheader("📜 5분 주기 기록")
for log in reversed(db.get("logs", [])):
    st.write(log)

if st.button("🔄 새로고침"):
    st.rerun()
