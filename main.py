import streamlit as st
import datetime
import json
import os
import requests

# --- 1. 설정 및 데이터 로드 ---
VERSION = "7.5-ASSET-FIX"
DB_FILE = "trading_db.json"

def get_now():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding='utf-8') as f:
                data = json.load(f)
                # 예산 데이터가 없으면 강제 주입
                if "balance_krw" not in data: data["balance_krw"] = 1000000
                if "balance_usd" not in data: data["balance_usd"] = 1000000
                if "balance_btc" not in data: data["balance_btc"] = 1000000
                return data
        except: pass
    return {"balance_krw": 1000000, "balance_usd": 1000000, "balance_btc": 1000000, "logs": [], "last_ts": 0}

def save_db(data):
    try:
        with open(DB_FILE, "w", encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except: pass

# --- 2. 통합 데이터 수집 (시세 + 뉴스) ---
def fetch_all():
    info = {"BTC": "N/A", "NVDA": "N/A", "삼성": "N/A", "ISSUE": "평온"}
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        # 코인 (업비트)
        res_btc = requests.get("https://api.upbit.com/v1/ticker?markets=KRW-BTC", timeout=3).json()
        info["BTC"] = f"{res_btc[0]['trade_price']:,.0f}"
        
        # 미장/국장 (Yahoo)
        tickers = {"NVDA": "NVDA", "삼성": "005930.KS"}
        for name, code in tickers.items():
            r = requests.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{code}?interval=1m&range=1d", headers=headers, timeout=3).json()
            p = r['chart']['result'][0]['meta']['regularMarketPrice']
            info[name] = f"{p:,.1f}" if name == "NVDA" else f"{p:,.0f}"
            
        # 뉴스 이슈
        n_res = requests.get("https://news.google.com/rss/search?q=전쟁+반도체&hl=ko&gl=KR&ceid=KR:ko", timeout=3).text
        issues = []
        if "전쟁" in n_res: issues.append("⚠️지정학")
        if "반도체" in n_res or "AI" in n_res: issues.append("💻기술주")
        if issues: info["ISSUE"] = "/".join(issues)
    except: pass
    return info

# --- 3. 실행 엔진 ---
db = load_db()
now = get_now()

# 5분 자동 스캔
if (now.timestamp() - db.get("last_ts", 0) >= 250) or not db["logs"]:
    data = fetch_all()
    log_entry = f"[{now.strftime('%H:%M')}] BTC:{data['BTC']} | NVDA:{data['NVDA']} | 삼성:{data['삼성']} | {data['ISSUE']}"
    db["logs"].append(log_entry)
    db["last_ts"] = now.timestamp()
    if len(db["logs"]) > 30: db["logs"] = db["logs"][-30:]
    save_db(db)

# --- 4. UI 구성 (모바일 최적화) ---
st.set_page_config(page_title="Asset Monitor", layout="wide")
st.title(f"📱 통합 자산 관제소 v{VERSION}")

# [예산 현황 섹션] - 사용자님 요청사항
st.subheader("💰 자산 현황 (예산)")
c1, c2, c3 = st.columns(3)
c1.metric("국장(KRW)", f"{db['balance_krw']/10000:,.0f}만")
c2.metric("미장(USD)", f"{db['balance_usd']/10000:,.0f}만")
c3.metric("코인(BTC)", f"{db['balance_btc']/10000:,.0f}만")

st.divider()

# [실시간 시세 전광판]
live = fetch_all()
st.info(f"📈 실시간: BTC {live['BTC']} / NVDA {live['NVDA']} / 삼성 {live['삼성']}")

st.divider()

# [로그 출력]
st.subheader("📜 5분 주기 통합 로그")
for log in reversed(db.get("logs", [])):
    if "⚠️" in log: st.error(log)
    else: st.write(log)

if st.button("🔄 즉시 새로고침"):
    st.rerun()
