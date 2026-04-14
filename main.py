import streamlit as st
import datetime
import json
import os
import requests

# --- 1. 설정 및 자산 고정 ---
VERSION = "8.3-STABLE"
DB_FILE = "trading_db.json"

def get_now():
    # 한국 시간 설정 (UTC+9)
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding='utf-8') as f:
                data = json.load(f)
                # 예산 데이터 100만 원 고정 (휘발 방지)
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

# --- 2. 시세 수신 (에러 방어형) ---
def fetch_all():
    res = {"BTC": "ERR", "NVDA": "ERR", "삼성": "ERR", "ISSUE": "평온"}
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    # 1. 업비트 코인
    try:
        btc_url = "https://api.upbit.com/v1/ticker?markets=KRW-BTC"
        b_res = requests.get(btc_url, timeout=5).json()
        res["BTC"] = f"{b_res[0]['trade_price']:,.0f}"
    except: pass

    # 2. 야후 파이낸스 (NVDA, 삼성전자)
    for n, c in [("NVDA", "NVDA"), ("삼성", "005930.KS")]:
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{c}?interval=1m&range=1d"
            r = requests.get(url, headers=headers, timeout=5).json()
            p = r['chart']['result'][0]['meta']['regularMarketPrice']
            res[n] = f"{p:,.1f}" if n == "NVDA" else f"{p:,.0f}"
        except: pass

    # 3. 구글 뉴스 (전쟁/기술주)
    try:
        n_url = "https://news.google.com/rss/search?q=전쟁+반도체&hl=ko&gl=KR&ceid=KR:ko"
        news = requests.get(n_url, timeout=5).text
        found = []
        if "전쟁" in news: found.append("⚠️지정학")
        if "반도체" in news or "AI" in news: found.append("💻기술주")
        if found: res["ISSUE"] = "/".join(found)
    except: pass
    
    return res

# --- 3. [핵심] 자동 기록 엔진 ---
db = load_db()
now = get_now()
now_ts = now.timestamp()

# 240초(4분) 주기로 자동 기록
if (now_ts - db.get("last_ts", 0) >= 240) or not db["logs"]:
    info = fetch_all()
    log_msg = f"[{now.strftime('%H:%M')}] BTC:{info['BTC']} | NVDA:{info['NVDA']} | 삼성:{info['삼성']} | {info['ISSUE']}"
    db["logs"].append(log_msg)
    db["last_ts"] = now_ts
    if len(db["logs"]) > 30: db["logs"] = db["logs"][-30:]
    save_db(db)

# --- 4. UI 화면 ---
st.set_page_config(page_title="Trading AI", layout="wide")
st.title("📊 통합 자산 관제소 v8.3")

# 상단 예산 현황 고정
st.subheader("💰 자산 현황")
c1, c2, c3 = st.columns(3)
c1.metric("국장 예산", "100만 원")
c2.metric("미장 예산", "100만 원")
c3.metric("코인 예산", "100만 원")

st.divider()

# 하단 로그 출력
st.subheader("📜 5분 주기 자동 스캔 로그")
if not db["logs"]:
    st.write("데이터 수집 중...")
else:
    for log in reversed(db["logs"]):
        if "⚠️" in log: st.error(log)
        else: st.write(log)

if st.button("🔄 새로고침"):
    st.rerun()
