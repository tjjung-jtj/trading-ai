import streamlit as st
import datetime
import json
import os
import requests

# --- 1. 설정 및 자산 고정 ---
VERSION = "8.8-FINAL-SCAN"
DB_FILE = "trading_db.json"

def get_now():
    # 한국 시간(KST) 설정
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding='utf-8') as f:
                data = json.load(f)
                # 예산 데이터 100만 원 강제 고정
                data["balance_krw"] = 1000000
                data["balance_usd"] = 1000000
                data["balance_btc"] = 1000000
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

# --- 2. 시세 데이터 수집 ---
def fetch_info():
    res = {"BTC": "ERR", "NVDA": "ERR", "삼성": "ERR", "ISSUE": "평온"}
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        # 코인 (업비트)
        b = requests.get("https://api.upbit.com/v1/ticker?markets=KRW-BTC", timeout=5).json()
        res["BTC"] = f"{b[0]['trade_price']:,.0f}"
        
        # 주식 (야후)
        for n, c in [("NVDA", "NVDA"), ("삼성", "005930.KS")]:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{c}?interval=1m&range=1d"
            r = requests.get(url, headers=headers, timeout=5).json()
            p = r['chart']['result'][0]['meta']['regularMarketPrice']
            res[n] = f"{p:,.1f}" if n == "NVDA" else f"{p:,.0f}"
            
        # 뉴스 이슈
        news = requests.get("https://news.google.com/rss/search?q=전쟁+반도체&hl=ko", timeout=5).text
        if "전쟁" in news: res["ISSUE"] = "⚠️지정학"
    except:
        pass
    return res

# --- 3. [핵심] 자동 스캔 엔진 ---
db = load_db()
now = get_now()
now_ts = now.timestamp()

# 210초(3.5분)만 지나면 누가 접속하든(크론잡 포함) 기록하도록 기준 완화
if (now_ts - db.get("last_ts", 0) >= 210) or not db["logs"]:
    data = fetch_info()
    log_msg = f"[{now.strftime('%H:%M')}] BTC:{data['BTC']} | NVDA:{data['NVDA']} | 삼성:{data['삼성']} | {data['ISSUE']}"
    db["logs"].append(log_msg)
    db["last_ts"] = now_ts
    if len(db["logs"]) > 30: db["logs"] = db["logs"][-30:]
    save_db(db)

# --- 4. 사용자 화면 ---
st.set_page_config(page_title="AI Asset Monitor")
st.title(f"📊 통합 자산 관제소 v{VERSION}")

# 예산 상단 고정 (100만 원)
st.subheader("💰 자산 현황")
c1, c2, c3 = st.columns(3)
c1.metric("국장 예산", "100만 원")
c2.metric("미장 예산", "100만 원")
c3.metric("코인 예산", "100만 원")

st.divider()

# 로그 출력
st.subheader("📜 자동 스캔 로그 (5분 주기)")
if not db["logs"]:
    st.info("데이터를 수집 중입니다...")
else:
    for log in reversed(db["logs"]):
        if "⚠️" in log: st.error(log)
        else: st.write(log)

if st.button("🔄 새로고침"):
    st.rerun()
