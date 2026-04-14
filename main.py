import streamlit as st
import datetime
import json
import os
import requests

# --- 1. 설정 및 데이터 관리 ---
VERSION = "7.9-FINAL-AUTO"
DB_FILE = "trading_db.json"

def get_now():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding='utf-8') as f:
                data = json.load(f)
                # 예산 데이터 강제 고정 (각 100만원)
                data.setdefault("balance_krw", 1000000)
                data.setdefault("balance_usd", 1000000)
                data.setdefault("balance_btc", 1000000)
                data.setdefault("logs", [])
                data.setdefault("last_ts", 0)
                return data
        except: pass
    return {"balance_krw": 1000000, "balance_usd": 1000000, "balance_btc": 1000000, "logs": [], "last_ts": 0}

def save_db(data):
    try:
        with open(DB_FILE, "w", encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except: pass

# --- 2. 시세 및 이슈 수집 함수 ---
def fetch_market_info():
    info = {"BTC": "N/A", "NVDA": "N/A", "삼성": "N/A", "ISSUE": "평온"}
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    # 1. 코인 (업비트)
    try:
        btc_res = requests.get("https://api.upbit.com/v1/ticker?markets=KRW-BTC", timeout=5).json()
        info["BTC"] = f"{btc_res[0]['trade_price']:,.0f}"
    except: info["BTC"] = "수신실패"

    # 2. 미장/국장 (야후)
    tickers = {"NVDA": "NVDA", "삼성": "005930.KS"}
    for name, code in tickers.items():
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{code}?interval=1m&range=1d"
            r = requests.get(url, headers=headers, timeout=5).json()
            p = r['chart']['result'][0]['meta']['regularMarketPrice']
            info[name] = f"{p:,.1f}" if name == "NVDA" else f"{p:,.0f}"
        except: info[name] = "수신실패"

    # 3. 뉴스 이슈
    try:
        news_url = "https://news.google.com/rss/search?q=전쟁+반도체&hl=ko&gl=KR&ceid=KR:ko"
        n_res = requests.get(news_url, timeout=5).text
        found = []
        if "전쟁" in n_res or "공격" in n_res: found.append("⚠️지정학")
        if "반도체" in n_res or "AI" in n_res: found.append("💻기술주")
        info["ISSUE"] = "/".join(found) if found else "평온"
    except: pass
    
    return info

# --- 3. 백그라운드 자동 실행 로직 ---
db = load_db()
now = get_now()
now_ts = now.timestamp()

# 마지막 기록 후 240초(4분) 이상 지났다면 무조건 기록 수행
if (now_ts - db.get("last_ts", 0) >= 240) or not db["logs"]:
    data = fetch_market_info()
    log_entry = f"[{now.strftime('%H:%M')}] BTC:{data['BTC']} | NVDA:{data['NVDA']} | 삼성:{data['삼성']} | {data['ISSUE']}"
    
    db["logs"].append(log_entry)
    db["last_ts"] = now_ts
    if len(db["logs"]) > 30: db["logs"] = db["logs"][-30:] # 최근 30개 유지
    save_db(db)

# --- 4. UI 구성 ---
st.set_page_config(page_title="AI Asset Monitor v7.9", layout="wide")

# [상단] 예산 현황 고정 표시
st.title("📊 통합 자산 및 시세 관제")
st.subheader("💰 자산 예산 현황")
c1, c2, c3 = st.columns(3)
c1.metric("국장 예산", f"{db['balance_krw']/10000:,.0f}만 원")
c2.metric("미장 예산", f"{db['balance_usd']/10000:,.0f}만 원")
c3.metric("코인 예산", f"{db['balance_btc']/10000:,.0f}만 원")

st.divider()

# [하단] 5분 주기 로그 리스트
st.subheader("📜 5분 주기 자동 스캔 로그")
if not db["logs"]:
    st.info("크론잡이 첫 데이터를 수집할 때까지 잠시만 기다려주세요.")
else:
    for log in reversed(db["logs"]):
        if "⚠️" in log:
            st.error(log) # 전쟁 이슈 시 빨간색 강조
        else:
            st.write(log)

if st.button("🔄 수동 새로고침"):
    st.rerun()
