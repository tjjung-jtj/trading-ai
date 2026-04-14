import streamlit as st
import datetime
import json
import os
import requests

# --- 1. 설정 및 데이터 로드 ---
VERSION = "7.6-STABLE-SCAN"
DB_FILE = "trading_db.json"

def get_now():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding='utf-8') as f:
                data = json.load(f)
                # 예산 데이터 보존 (각 100만원)
                if "balance_krw" not in data: data["balance_krw"] = 1000000
                if "balance_usd" not in data: data["balance_usd"] = 1000000
                if "balance_btc" not in data: data["balance_btc"] = 1000000
                if "logs" not in data: data["logs"] = []
                return data
        except: pass
    return {"balance_krw": 1000000, "balance_usd": 1000000, "balance_btc": 1000000, "logs": [], "last_ts": 0}

def save_db(data):
    try:
        with open(DB_FILE, "w", encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except: pass

# --- 2. 시세 및 이슈 수집 (개별 에러 처리) ---
def fetch_market_data():
    res = {"BTC": "N/A", "NVDA": "N/A", "삼성": "N/A", "ISSUE": "평온"}
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    # 코인
    try:
        btc = requests.get("https://api.upbit.com/v1/ticker?markets=KRW-BTC", timeout=5).json()
        res["BTC"] = f"{btc[0]['trade_price']:,.0f}"
    except: pass

    # 미장 (NVDA)
    try:
        nvda = requests.get("https://query1.finance.yahoo.com/v8/finance/chart/NVDA?interval=1m&range=1d", headers=headers, timeout=5).json()
        res["NVDA"] = f"{nvda['chart']['result'][0]['meta']['regularMarketPrice']:.1f}"
    except: pass

    # 국장 (삼성)
    try:
        ss = requests.get("https://query1.finance.yahoo.com/v8/finance/chart/005930.KS?interval=1m&range=1d", headers=headers, timeout=5).json()
        res["삼성"] = f"{ss['chart']['result'][0]['meta']['regularMarketPrice']:,.0f}"
    except: pass

    # 뉴스
    try:
        news = requests.get("https://news.google.com/rss/search?q=전쟁+반도체&hl=ko&gl=KR&ceid=KR:ko", timeout=5).text
        found = []
        if "전쟁" in news: found.append("⚠️지정학")
        if "반도체" in news or "AI" in news: found.append("💻기술주")
        if found: res["ISSUE"] = "/".join(found)
    except: pass
    
    return res

# --- 3. 메인 엔진 (시간 체크 로직 완화) ---
db = load_db()
now = get_now()
now_ts = now.timestamp()

# 마지막 스캔 후 270초(4.5분)가 지났으면 무조건 실행
if (now_ts - db.get("last_ts", 0) >= 270) or not db["logs"]:
    data = fetch_market_data()
    log_entry = f"[{now.strftime('%H:%M')}] BTC:{data['BTC']} | NVDA:{data['NVDA']} | 삼성:{data['삼성']} | {data['ISSUE']}"
    
    db["logs"].append(log_entry)
    db["last_ts"] = now_ts
    if len(db["logs"]) > 30: db["logs"] = db["logs"][-30:]
    save_db(db)

# --- 4. UI ---
st.set_page_config(page_title="Asset Monitor v7.6", layout="wide")
st.title(f"🚀 통합 자산 관제소 v{VERSION}")

# 예산 현황 상단 고정
st.subheader("💰 자산 현황 (예산)")
c1, c2, c3 = st.columns(3)
c1.metric("국장(KRW)", f"{db['balance_krw']/10000:,.0f}만")
c2.metric("미장(USD)", f"{db['balance_usd']/10000:,.0f}만")
c3.metric("코인(BTC)", f"{db['balance_btc']/10000:,.0f}만")

st.divider()

# 로그 출력
st.subheader("📜 5분 주기 통합 로그")
if not db["logs"]:
    st.info("데이터를 수집 중입니다. 5분만 기다려주세요.")
else:
    for log in reversed(db["logs"]):
        if "⚠️" in log: st.error(log)
        else: st.write(log)

if st.button("🔄 즉시 새로고침"):
    st.rerun()
