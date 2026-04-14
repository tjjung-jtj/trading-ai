import streamlit as st
import datetime
import json
import os
import requests

# --- 1. 설정 ---
VERSION = "6.6-FINAL"
DB_FILE = "trading_db.json"

def get_now():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding='utf-8') as f:
                data = json.load(f)
                # 잔고 설정이 없으면 초기화 (각 백만원)
                if "balance_krw" not in data: data["balance_krw"] = 1000000
                if "balance_usd" not in data: data["balance_usd"] = 1000000
                if "balance_btc" not in data: data["balance_btc"] = 1000000
                return data
        except: pass
    return {
        "balance_krw": 1000000, 
        "balance_usd": 1000000, 
        "balance_btc": 1000000, 
        "logs": [], 
        "scan_count": 0, 
        "last_ts": 0
    }

def save_db(data):
    try:
        with open(DB_FILE, "w", encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except: pass

# --- 2. 시세 수신 (국장 포함 강화형) ---
def get_data():
    results = []
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    # [코인] 업비트
    try:
        res = requests.get("https://api.upbit.com/v1/ticker?markets=KRW-BTC", timeout=5)
        price = res.json()[0]['trade_price']
        results.append(f"BTC:{price:,.0f}")
    except: results.append("BTC:Err")

    # [미장] 엔비디아 (직접 쿼리)
    try:
        url_nvda = "https://query1.finance.yahoo.com/v8/finance/chart/NVDA?interval=1m&range=1d"
        res_nvda = requests.get(url_nvda, headers=headers, timeout=5).json()
        price_nvda = res_nvda['chart']['result'][0]['meta']['regularMarketPrice']
        results.append(f"NVDA:{price_nvda:,.1f}")
    except: results.append("NVDA:Err")

    # [국장] 삼성전자 (차단 우회용 전용 경로)
    try:
        url_samsung = "https://query1.finance.yahoo.com/v8/finance/chart/005930.KS?interval=1m&range=1d"
        res_samsung = requests.get(url_samsung, headers=headers, timeout=5).json()
        price_samsung = res_samsung['chart']['result'][0]['meta']['regularMarketPrice']
        results.append(f"삼성:{price_samsung:,.0f}")
    except: results.append("삼성:Wait")
        
    return " | ".join(results)

# --- 3. 메인 실행 로직 ---
db = load_db()
now = get_now()

# 5분 자동 스캔 (크론잡 대응)
if now.timestamp() - db.get("last_ts", 0) >= 300:
    current_data = get_data()
    db["scan_count"] += 1
    db["last_ts"] = now.timestamp()
    db["logs"].append(f"[{now.strftime('%H:%M')}] {current_data}")
    if len(db["logs"]) > 30: db["logs"] = db["logs"][-30:]
    save_db(db)

# --- 4. UI 구성 (모바일 최적화) ---
st.set_page_config(page_title="AI Trading", layout="centered")
st.title(f"📱 모바일 통합 관제소 v{VERSION}")

# 잔고 표시 섹션 (각 백만원)
st.subheader("💰 내 자산 현황")
c1, c2, c3 = st.columns(3)
c1.metric("국장(KRW)", f"{db['balance_krw']//10000}만")
c2.metric("미장(USD)", f"{db['balance_usd']//10000}만")
c3.metric("코인(BTC)", f"{db['balance_btc']//10000}만")

st.divider()

# 실시간 시세 (새로고침 시 즉시 반영)
st.subheader("📈 실시간 시세")
st.success(get_data())

st.divider()

# 로그 표시
st.subheader("📜 5분 주기 스캔 로그")
for log in reversed(db.get("logs", [])):
    st.write(log)

if st.button("🔄 즉시 새로고침"):
    st.rerun()
