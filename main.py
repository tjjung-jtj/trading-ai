import streamlit as st
import datetime
import json
import os
import requests

# --- 1. 환경 설정 ---
VERSION = "8.5-FINAL-RELIABLE"
DB_FILE = "trading_db.json"

def get_now():
    # 한국 시간 강제 고정
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))

def load_db():
    # 파일이 있으면 읽고, 없으면 사용자 요청대로 예산 100만 원 초기화
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding='utf-8') as f:
                data = json.load(f)
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
def fetch_market():
    res = {"BTC": "수신실패", "NVDA": "수신실패", "삼성": "수신실패", "ISSUE": "평온"}
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        # 1. 코인
        btc_res = requests.get("https://api.upbit.com/v1/ticker?markets=KRW-BTC", timeout=5).json()
        res["BTC"] = f"{btc_res[0]['trade_price']:,.0f}"

        # 2. 야후 파이낸스
        for n, c in [("NVDA", "NVDA"), ("삼성", "005930.KS")]:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{c}?interval=1m&range=1d"
            r = requests.get(url, headers=headers, timeout=5).json()
            p = r['chart']['result'][0]['meta']['regularMarketPrice']
            res[n] = f"{p:,.1f}" if n == "NVDA" else f"{p:,.0f}"

        # 3. 뉴스
        news = requests.get("https://news.google.com/rss/search?q=전쟁+반도체&hl=ko&gl=KR&ceid=KR:ko", timeout=5).text
        found = []
        if "전쟁" in news: found.append("⚠️지정학")
        if "반도체" in news or "AI" in news: found.append("💻기술주")
        if found: res["ISSUE"] = "/".join(found)
    except: pass
    
    return res

# --- 3. 자동 실행 로직 (핵심) ---
db = load_db()
now = get_now()
now_ts = now.timestamp()

# 누가 접속하든(사용자든 크론잡이든) 4분(240초)이 지났으면 로그 생성
if (now_ts - db.get("last_ts", 0) >= 240) or not db["logs"]:
    market = fetch_market()
    log_msg = f"[{now.strftime('%H:%M')}] BTC:{market['BTC']} | NVDA:{market['NVDA']} | 삼성:{market['삼성']} | {market['ISSUE']}"
    db["logs"].append(log_msg)
    db["last_ts"] = now_ts
    if len(db["logs"]) > 30: db["logs"] = db["logs"][-30:]
    save_db(db)

# --- 4. 사용자 화면 구성 ---
st.set_page_config(page_title="Asset Manager", layout="wide")
st.title(f"📊 통합 자산 관제소 v{VERSION}")

# [상단] 예산 고정
st.subheader("💰 자산 현황")
c1, c2, c3 = st.columns(3)
c1.metric("국장 예산", "100만 원")
c2.metric("미장 예산", "100만 원")
c3.metric("코인 예산", "100만 원")

st.divider()

# [하단] 로그 출력
st.subheader("📜 5분 주기 자동 스캔 로그")
if not db["logs"]:
    st.info("데이터 수집을 시작합니다. 잠시 후 새로고침 해주세요.")
else:
    for log in reversed(db["logs"]):
        if "⚠️" in log: st.error(log)
        else: st.write(log)

if st.button("🔄 즉시 새로고침"):
    st.rerun()
