import streamlit as st
import datetime
import json
import os
import requests

# --- 1. 기본 설정 ---
VERSION = "7.7-FORCE-LOG"
DB_FILE = "trading_db.json"

def get_now():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))

# [세션 메모리] 서버 재시작 시 파일 누락 방지용
if "backup_logs" not in st.session_state:
    st.session_state.backup_logs = []

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding='utf-8') as f:
                data = json.load(f)
                # 예산 데이터 초기화 방지
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

# --- 2. 데이터 수집 (시세 + 이슈) ---
def fetch_info():
    info = {"BTC": "N/A", "NVDA": "N/A", "삼성": "N/A", "ISSUE": "평온"}
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        # 코인
        b = requests.get("https://api.upbit.com/v1/ticker?markets=KRW-BTC", timeout=3).json()
        info["BTC"] = f"{b[0]['trade_price']:,.0f}"
        # 주식 (야후)
        for k, c in [("NVDA", "NVDA"), ("삼성", "005930.KS")]:
            r = requests.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{c}?interval=1m&range=1d", headers=headers, timeout=3).json()
            p = r['chart']['result'][0]['meta']['regularMarketPrice']
            info[k] = f"{p:,.1f}" if k == "NVDA" else f"{p:,.0f}"
        # 뉴스
        n = requests.get("https://news.google.com/rss/search?q=전쟁+반도체&hl=ko", timeout=3).text
        found = []
        if "전쟁" in n: found.append("⚠️지정학")
        if "반도체" in n or "AI" in n: found.append("💻기술주")
        if found: info["ISSUE"] = "/".join(found)
    except: pass
    return info

# --- 3. 실행 엔진 (4분 주기로 완화) ---
db = load_db()
now = get_now()
now_ts = now.timestamp()

# 마지막 기록 후 240초(4분)만 지나면 새 로그 생성
if (now_ts - db.get("last_ts", 0) >= 240) or not db["logs"]:
    data = fetch_info()
    log_entry = f"[{now.strftime('%H:%M')}] BTC:{data['BTC']} | NVDA:{data['NVDA']} | 삼성:{data['삼성']} | {data['ISSUE']}"
    db["logs"].append(log_entry)
    db["last_ts"] = now_ts
    if len(db["logs"]) > 30: db["logs"] = db["logs"][-30:]
    save_db(db)
    st.session_state.backup_logs = db["logs"]

# --- 4. UI 구성 ---
st.set_page_config(page_title="AI Asset Monitor", layout="wide")
st.title(f"🚀 통합 자산 관제소 v{VERSION}")

# [1] 예산 현황 상단 고정
st.subheader("💰 자산 현황 (예산)")
c1, c2, c3 = st.columns(3)
c1.metric("국장(KRW)", f"{db['balance_krw']/10000:,.0f}만")
c2.metric("미장(USD)", f"{db['balance_usd']/10000:,.0f}만")
c3.metric("코인(BTC)", f"{db['balance_btc']/10000:,.0f}만")

st.divider()

# [2] 통합 로그 출력
st.subheader("📜 5분 주기 통합 시세/이슈 로그")
all_logs = db["logs"] if db["logs"] else st.session_state.backup_logs
if not all_logs:
    st.info("데이터 수집 중... 잠시 후 자동으로 나타납니다.")
else:
    for log in reversed(all_logs):
        if "⚠️" in log: st.error(log)
        else: st.write(log)

if st.button("🔄 즉시 새로고침"):
    st.rerun()
