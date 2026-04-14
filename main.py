import streamlit as st
import datetime
import json
import os
import requests

# --- 1. 설정 및 DB 관리 ---
VERSION = "8.1-CRON-FIX"
DB_FILE = "trading_db.json"

def get_now():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding='utf-8') as f:
                data = json.load(f)
                # 예산 데이터 고정 (100만원)
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

# --- 2. 통합 시세 수집 엔진 ---
def fetch_market_data():
    res = {"BTC": "불러오기 실패", "NVDA": "불러오기 실패", "삼성": "불러오기 실패", "ISSUE": "평온"}
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        # 1. 코인 (업비트)
        btc = requests.get("https://api.upbit.com/v1/ticker?markets=KRW-BTC", timeout=5).json()
        res["BTC"] = f"{btc[0]['trade_price']:,.0f}"

        # 2. 주식 (야후)
        for name, ticker in [("NVDA", "NVDA"), ("삼성", "005930.KS")]:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1m&range=1d"
            r = requests.get(url, headers=headers, timeout=5).json()
            p = r['chart']['result'][0]['meta']['regularMarketPrice']
            res[name] = f"{p:,.1f}" if name == "NVDA" else f"{p:,.0f}"

        # 3. 뉴스 이슈
        n = requests.get("https://news.google.com/rss/search?q=전쟁+반도체&hl=ko", timeout=5).text
        found = []
        if "전쟁" in n: found.append("⚠️지정학")
        if "반도체" in n or "AI" in n: found.append("💻기술주")
        res["ISSUE"] = "/".join(found) if found else "평온"
    except: pass
    return res

# --- 3. 실행 로직 (접속 시 무조건 작동) ---
db = load_db()
now = get_now()
now_ts = now.timestamp()

# 핵심: 마지막 기록 후 240초(4분)만 지나면 "누가 접속하든(크론잡 포함)" 기록함
if (now_ts - db.get("last_ts", 0) >= 240) or not db["logs"]:
    data = fetch_market_data()
    # 사용자 요구대로 시세를 한 줄에 통합
    log_text = f"[{now.strftime('%H:%M')}] BTC:{data['BTC']} | NVDA:{data['NVDA']} | 삼성:{data['삼성']} | {data['ISSUE']}"
    db["logs"].append(log_text)
    db["last_ts"] = now_ts
    if len(db["logs"]) > 30: db["logs"] = db["logs"][-30:]
    save_db(db)

# --- 4. UI 출력 ---
st.set_page_config(page_title="Asset Monitor v8.1", layout="wide")

# [상단] 예산 현황
st.title("📊 통합 자산 관제 센터")
st.subheader("💰 고정 예산 현황")
c1, c2, c3 = st.columns(3)
c1.metric("국장 예산", "100만 원")
c2.metric("미장 예산", "100만 원")
c3.metric("코인 예산", "100만 원")

st.divider()

# [하단] 로그 목록
st.subheader("📜 5분 주기 자동 관제 로그")
if not db["logs"]:
    st.write("데이터를 불러오는 중입니다...")
else:
    for log in reversed(db["logs"]):
        if "⚠️" in log: st.error(log)
        else: st.write(log)

if st.button("🔄 즉시 새로고침"):
    st.rerun()
