import streamlit as st
import datetime
import json
import os
import requests

# --- 1. 설정 ---
VERSION = "7.4-FINAL-STABLE"
DB_FILE = "trading_db.json"

def get_now():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding='utf-8') as f:
                return json.load(f)
        except: pass
    return {"logs": [], "last_ts": 0}

def save_db(data):
    try:
        with open(DB_FILE, "w", encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except: pass

# --- 2. 뉴스 및 시세 수신 (멀티 채널) ---
def fetch_all():
    data = {"BTC": "수신불가", "NVDA": "수신불가", "삼성": "수신불가", "ISSUE": "평온"}
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    # 1. 코인 (업비트)
    try:
        res = requests.get("https://api.upbit.com/v1/ticker?markets=KRW-BTC", timeout=3).json()
        data["BTC"] = f"{res[0]['trade_price']:,.0f}"
    except: pass

    # 2. 주식 (경로 1: Yahoo 직접)
    for k, ticker in [("NVDA", "NVDA"), ("삼성", "005930.KS")]:
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1m&range=1d"
            r = requests.get(url, headers=headers, timeout=3).json()
            p = r['chart']['result'][0]['meta']['regularMarketPrice']
            data[k] = f"{p:,.1f}" if k == "NVDA" else f"{p:,.0f}"
        except: pass

    # 3. 뉴스 이슈 (전쟁/기술주)
    try:
        news_url = "https://news.google.com/rss/search?q=전쟁+반도체+엔비디아&hl=ko&gl=KR&ceid=KR:ko"
        n_res = requests.get(news_url, timeout=3).text
        issues = []
        if "전쟁" in n_res or "침공" in n_res: issues.append("⚠️지정학리스크")
        if "반도체" in n_res or "AI" in n_res: issues.append("💻기술주이슈")
        if issues: data["ISSUE"] = "/".join(issues)
    except: pass
    
    return data

# --- 3. 실행 엔진 ---
db = load_db()
now = get_now()

# 5분 주기 강제 실행 (또는 첫 실행)
if (now.timestamp() - db.get("last_ts", 0) >= 250) or not db["logs"]:
    info = fetch_all()
    log_msg = f"[{now.strftime('%H:%M')}] BTC:{info['BTC']} | NVDA:{info['NVDA']} | 삼성:{info['삼성']} | {info['ISSUE']}"
    
    db["logs"].append(log_msg)
    db["last_ts"] = now.timestamp()
    if len(db["logs"]) > 30: db["logs"] = db["logs"][-30:]
    save_db(db)

# --- 4. UI ---
st.set_page_config(page_title="AI 관제 v7.4", layout="wide")
st.title(f"🚀 AI 자동매매 관제소 v{VERSION}")

# 실시간 전광판
info = fetch_all()
c1, c2, c3 = st.columns(3)
c1.metric("비트코인", info["BTC"])
c2.metric("엔비디아", info["NVDA"])
c3.metric("삼성전자", info["삼성"])

st.info(f"🌐 현재 시장 이슈: {info['ISSUE']}")

st.divider()
st.subheader("📜 5분 주기 통합 로그")
for log in reversed(db.get("logs", [])):
    if "⚠️" in log: st.error(log)
    else: st.write(log)

if st.button("🔄 즉시 새로고침"):
    st.rerun()
