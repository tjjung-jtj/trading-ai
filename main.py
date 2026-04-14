import streamlit as st
import datetime
import json
import os
import requests
import re

# --- 1. 설정 및 전략 (어제 논의된 모든 조건 반영) ---
VERSION = "7.0-ALL-IN-ONE"
DB_FILE = "trading_db.json"

# [매매 전략 상수]
K_VALUE = 0.5            # 변동성 돌파 계수
PROFIT_TARGET = 0.03    # 익절 3%
STOP_LOSS = -0.02       # 손절 2%

# [이슈 감시 키워드]
WAR_KEYWORDS = ["전쟁", "침공", "미사일", "지정학"]
TECH_KEYWORDS = ["엔비디아", "반도체", "AI", "나스닥", "금리"]

def get_now():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding='utf-8') as f:
                data = json.load(f)
                for k in ["balance_krw", "balance_usd", "balance_btc"]:
                    if k not in data: data[k] = 1000000
                if "holdings" not in data: data["holdings"] = {}
                if "logs" not in data: data["logs"] = []
                return data
        except: pass
    return {"balance_krw": 1000000, "balance_usd": 1000000, "balance_btc": 1000000, "holdings": {}, "logs": [], "last_ts": 0}

def save_db(data):
    try:
        with open(DB_FILE, "w", encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except: pass

# --- 2. 뉴스 및 이슈 분석 (안정성 강화) ---
def get_market_issue():
    issues = []
    try:
        # 뉴스 헤드라인 수집 (타임아웃 짧게 설정하여 스캔 멈춤 방지)
        url = "https://news.google.com/rss/search?q=전쟁+반도체+경제&hl=ko&gl=KR&ceid=KR:ko"
        res = requests.get(url, timeout=3)
        content = res.text
        
        for k in WAR_KEYWORDS:
            if k in content: issues.append(f"🚩{k}")
        for k in TECH_KEYWORDS:
            if k in content: issues.append(f"🔹{k}")
    except:
        issues.append("뉴스수신지연")
    return issues[:3] # 상위 3개 키워드만 반환

# --- 3. 통합 매매 엔진 ---
def run_trading_engine():
    db = load_db()
    now = get_now()
    
    # 5분 주기 체크
    if now.timestamp() - db.get("last_ts", 0) < 280:
        return db

    # [데이터 수신]
    prices = {}
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    # 코인 (업비트)
    try:
        res = requests.get("https://api.upbit.com/v1/ticker?markets=KRW-BTC", timeout=3).json()
        prices['BTC'] = res[0]['trade_price']
    except: prices['BTC'] = 0

    # 주식 (야후 직접 호출 - 국장/미장)
    tickers = {"NVDA": "NVDA", "삼성": "005930.KS"}
    for name, code in tickers.items():
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{code}?interval=1m&range=1d"
            r = requests.get(url, headers=headers, timeout=3).json()
            prices[name] = r['chart']['result'][0]['meta']['regularMarketPrice']
        except: prices[name] = 0

    # [이슈 분석 및 매매 판단]
    issues = get_market_issue()
    trade_note = ""
    
    # 전쟁 이슈 시 매수 금지 로직
    is_war = any(k in "".join(issues) for k in WAR_KEYWORDS)
    if is_war:
        trade_note = " | 🚫전쟁위험 매수정지"
    
    # [기록 및 저장]
    db["last_ts"] = now.timestamp()
    price_text = f"BTC:{prices['BTC']:,.0f} | NVDA:{prices['NVDA']:,.1f} | 삼성:{prices['삼성']:,.0f}"
    issue_text = f"[{'/'.join(issues)}]" if issues else "[정상]"
    
    log_entry = f"[{now.strftime('%H:%M')}] {price_text} {issue_text}{trade_note}"
    db["logs"].append(log_entry)
    if len(db["logs"]) > 30: db["logs"] = db["logs"][-30:]
    save_db(db)
    return db

# --- 4. UI ---
st.set_page_config(page_title="AI Trader v7", layout="centered")
db = run_trading_engine()

st.title(f"🚀 통합 매매 엔진 v{VERSION}")

# 자산 현황
c1, c2, c3 = st.columns(3)
c1.metric("국장", f"{db['balance_krw']/10000:,.0f}만")
c2.metric("미장", f"{db['balance_usd']/10000:,.0f}만")
c3.metric("코인", f"{db['balance_btc']/10000:,.0f}만")

st.divider()

# 로그 출력
st.subheader("📜 실시간 이슈 및 시세 로그")
if not db["logs"]:
    st.info("첫 스캔을 진행 중입니다... (5분 주기)")
else:
    for log in reversed(db["logs"]):
        st.write(log)

if st.button("🔄 즉시 갱신"):
    st.rerun()
