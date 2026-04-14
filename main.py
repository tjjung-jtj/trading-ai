import streamlit as st
import datetime
import json
import os
import requests

# --- 1. 설정 및 자산 고정 ---
VERSION = "8.4-FIX-COMPLETE"
DB_FILE = "trading_db.json"

def get_now():
    # 한국 시간 강제 설정
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding='utf-8') as f:
                data = json.load(f)
                # 예산 데이터 100만 원 고정 (사용자 요청)
                data.setdefault("balance_krw", 1000000)
                data.setdefault("balance_usd", 1000000)
                data.setdefault("balance_btc", 1000000)
                data.setdefault("logs", [])
                data.setdefault("last_ts", 0)
                return data
        except:
            pass
    return {"balance_krw": 1000000, "balance_usd": 1000000, "balance_btc": 1000000, "logs": [], "last_ts": 0}

def save_db(data):
    try:
        with open(DB_FILE, "w", encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except:
        pass

# --- 2. 데이터 수집 엔진 ---
def fetch_data():
    info = {"BTC": "수신실패", "NVDA": "수신실패", "삼성": "수신실패", "ISSUE": "평온"}
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        # 1. 코인 (업비트)
        b_res = requests.get("https://api.upbit.com/v1/ticker?markets=KRW-BTC", timeout=5).json()
        info["BTC"] = f"{b_res[0]['trade_price']:,.0f}"

        # 2. 주식 (야후)
        for n, c in [("NVDA", "NVDA"), ("삼성", "005930.KS")]:
            r = requests.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{c}?interval=1m&range=1d", headers=headers, timeout=5).json()
            p = r['chart']['result'][0]['meta']['regularMarketPrice']
            info[n] = f"{p:,.1f}" if n == "NVDA" else f"{p:,.0f}"

        # 3. 뉴스 이슈
        news = requests.get("https://news.google.com/rss/search?q=전쟁+반도체&hl=ko&gl=KR&ceid=KR:ko", timeout=5).text
        found = []
        if "전쟁" in news: found.append("⚠️지정학")
        if "반도체" in news or "AI" in news: found.append("💻기술주")
        if found: info["ISSUE"] = "/".join(found)
    except: pass
    
    return info

# --- 3. [핵심] 자동 실행 로직 ---
db = load_db()
now = get_now()
now_ts = now.timestamp()

# 핵심 포인트: 4분(240초)만 지나면 누가 접속하든(크론잡 포함) 무조건 시세 기록
if (now_ts - db.get("last_ts", 0) >= 240) or not db["logs"]:
    market = fetch_data()
    log_entry = f"[{now.strftime('%H:%M')}] BTC:{market['BTC']} | NVDA:{market['NVDA']} | 삼성:{market['삼성']} | {market['ISSUE']}"
    db["logs"].append(log_entry)
    db["last_ts"] = now_ts
    if len(db["logs"]) > 30: db["logs"] = db["logs"][-30:]
    save_db(db)

# --- 4. 화면 UI ---
st.set_page_config(page_title="Asset Guard", layout="wide")
st.title("📊 통합 자산 관제소 v8.4")

# [상단] 예산 고정
st.subheader("💰 고정 예산 현황")
c1, c2, c3 = st.columns(3)
c1.metric("국장 예산", "100만 원")
c2.metric("미장 예산", "100만 원")
c3.metric("코인 예산", "100만 원")

st.divider()

# [하단] 로그 출력
st.subheader("📜 5분 주기 자동 스캔 로그")
if not db["logs"]:
    st.info("데이터 수집 중입니다... 5분만 기다려주세요.")
else:
    for log in reversed(db["logs"]):
        if "⚠️" in log: st.error(log)
        else: st.write(log)

if st.button("🔄 즉시 새로고침"):
    st.rerun()
