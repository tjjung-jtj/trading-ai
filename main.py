import streamlit as st
import datetime
import json
import os
import requests

# --- 1. 설정 및 DB 관리 ---
VERSION = "8.0-TOTAL-COMPLETE"
DB_FILE = "trading_db.json"

def get_now():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding='utf-8') as f:
                data = json.load(f)
                # 예산 데이터 강제 고정 (사용자 요구사항)
                data.setdefault("balance_krw", 1000000)
                data.setdefault("balance_usd", 1000000)
                data.setdefault("balance_btc", 1000000)
                data.setdefault("logs", [])
                data.setdefault("last_ts", 0)
                return data
        except: pass
    # 파일 없으면 기본값 생성
    return {"balance_krw": 1000000, "balance_usd": 1000000, "balance_btc": 1000000, "logs": [], "last_ts": 0}

def save_db(data):
    try:
        with open(DB_FILE, "w", encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except: pass

# --- 2. 데이터 수집 엔진 (시세 + 뉴스 통합) ---
def fetch_everything():
    res = {"BTC": "수신실패", "NVDA": "수신실패", "삼성": "수신실패", "ISSUE": "평온"}
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    # 코인 (업비트)
    try:
        b = requests.get("https://api.upbit.com/v1/ticker?markets=KRW-BTC", timeout=5).json()
        res["BTC"] = f"{b[0]['trade_price']:,.0f}"
    except: pass

    # 미장/국장 (야후)
    for name, code in [("NVDA", "NVDA"), ("삼성", "005930.KS")]:
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{code}?interval=1m&range=1d"
            r = requests.get(url, headers=headers, timeout=5).json()
            p = r['chart']['result'][0]['meta']['regularMarketPrice']
            res[name] = f"{p:,.1f}" if name == "NVDA" else f"{p:,.0f}"
        except: pass

    # 뉴스 이슈 (전쟁/기술주)
    try:
        n = requests.get("https://news.google.com/rss/search?q=전쟁+반도체&hl=ko", timeout=5).text
        found = []
        if "전쟁" in n or "공격" in n: found.append("⚠️지정학")
        if "반도체" in n or "AI" in n: found.append("💻기술주")
        if found: res["ISSUE"] = "/".join(found)
    except: pass
    
    return res

# --- 3. [핵심] 백그라운드 오토 스캔 로직 ---
# 이 섹션은 웹 접속이 발생할 때마다 실행되며, 5분이 지났으면 기록을 남깁니다.
db = load_db()
now = get_now()
now_ts = now.timestamp()

# 240초(4분)를 기준으로 하여 크론잡 신호를 놓치지 않게 설계
if (now_ts - db.get("last_ts", 0) >= 240) or not db["logs"]:
    data = fetch_everything()
    log_text = f"[{now.strftime('%H:%M')}] BTC:{data['BTC']} | NVDA:{data['NVDA']} | 삼성:{data['삼성']} | {data['ISSUE']}"
    
    db["logs"].append(log_text)
    db["last_ts"] = now_ts
    if len(db["logs"]) > 30: db["logs"] = db["logs"][-30:]
    save_db(db)

# --- 4. UI 레이아웃 ---
st.set_page_config(page_title="AI Asset Monitoring", layout="wide")

# [A] 예산 현황 전광판
st.title("📱 실시간 자산 및 시세 관제")
st.subheader("💰 고정 예산 현황")
col1, col2, col3 = st.columns(3)
col1.metric("국장 예산", f"{db['balance_krw']/10000:,.0f}만 원")
col2.metric("미장 예산", f"{db['balance_usd']/10000:,.0f}만 원")
col3.metric("코인 예산", f"{db['balance_btc']/10000:,.0f}만 원")

st.divider()

# [B] 5분 자동 스캔 로그
st.subheader("📜 5분 주기 자동 관제 로그")
if not db["logs"]:
    st.info("데이터를 수집 중입니다. 크론잡이 서버를 깨울 때까지 기다려 주세요.")
else:
    for log in reversed(db["logs"]):
        if "⚠️" in log: st.error(log) # 전쟁 이슈는 빨간색으로!
        else: st.write(log)

if st.button("🔄 즉시 새로고침"):
    st.rerun()
