import streamlit as st
import datetime
import json
import os
import requests

# --- 1. 설정 및 자산 고정 ---
VERSION = "8.6-STABLE"
DB_FILE = "trading_db.json"

def get_now():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding='utf-8') as f:
                data = json.load(f)
                # 예산 데이터 100만 원 고정
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

# --- 2. 데이터 수집 엔진 (수신 실패 최소화) ---
def fetch_data():
    info = {"BTC": "N/A", "NVDA": "N/A", "삼성": "N/A", "ISSUE": "평온"}
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        # 업비트
        b_res = requests.get("https://api.upbit.com/v1/ticker?markets=KRW-BTC", timeout=5).json()
        info["BTC"] = f"{b_res[0]['trade_price']:,.0f}"
        # 야후 (단순화)
        for n, c in [("NVDA", "NVDA"), ("삼성", "005930.KS")]:
            r = requests.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{c}?interval=1m&range=1d", headers=headers, timeout=5).json()
            p = r['chart']['result'][0]['meta']['regularMarketPrice']
            info[n] = f"{p:,.1f}" if n == "NVDA" else f"{p:,.0f}"
        # 뉴스
        n = requests.get("https://news.google.com/rss/search?q=전쟁+반도체&hl=ko", timeout=5).text
        if "전쟁" in n: info["ISSUE"] = "⚠️지정학"
    except: pass
    return info

# --- 3. [핵심] 자동 실행 로직 ---
db = load_db()
now = get_now()

# 240초(4분) 이상 차이 나면 기록
if (now.timestamp() - db.get("last_ts", 0) >= 240) or not db["logs"]:
    data = fetch_data()
    log_msg = f"[{now.strftime('%H:%M')}] BTC:{data['BTC']} | NVDA:{data['NVDA']} | 삼성:{data['삼성']} | {data['ISSUE']}"
    db["logs"].append(log_msg)
    db["last_ts"] = now.timestamp()
    if len(db["logs"]) > 30: db["logs"] = db["logs"][-30:]
    save_db(db)

# --- 4. UI 구성 ---
st.set_page_config(page_title="Asset Manager", layout="wide")
st.title(f"📊 자산 관제소 v{VERSION}")

# 예산 고정
st.subheader("💰 자산 현황")
c1, c2, c3 = st.columns(3)
c1.metric("국장 예산", "100만 원")
c2.metric("미장 예산", "100만 원")
c3.metric("코인 예산", "100만 원")

st.divider()

# 로그 출력
st.subheader("📜 5분 주기 자동 스캔 로그")
if not db["logs"]:
    st.info("데이터를 수집 중입니다...")
else:
    for log in reversed(db["logs"]):
        if "⚠️" in log: st.error(log)
        else: st.write(log)

if st.button("🔄 새로고침"):
    st.rerun()
