import streamlit as st
import datetime
import json
import os
import requests

# --- 1. 설정 및 전략 (사용자님 요구사항 집약) ---
VERSION = "7.1-TOTAL-CONTROL"
DB_FILE = "trading_db.json"

# 매매 전략 상수
K_VALUE = 0.5
RISK_STOP = True # 전쟁 이슈 시 매수 전면 중단

def get_now():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding='utf-8') as f:
                data = json.load(f)
                return data
        except: pass
    return {"balance_krw": 1000000, "balance_usd": 1000000, "balance_btc": 1000000, "holdings": {}, "logs": [], "last_ts": 0}

def save_db(data):
    try:
        with open(DB_FILE, "w", encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except: pass

# --- 2. 뉴스 이슈 분석 (기술주 전쟁 및 거시 경제) ---
def analyze_market_issues():
    issues = []
    try:
        # 주요 키워드 기반 뉴스 스캔
        query = "전쟁+반도체+엔비디아+금리"
        url = f"https://news.google.com/rss/search?q={query}&hl=ko&gl=KR&ceid=KR:ko"
        res = requests.get(url, timeout=5)
        content = res.text
        
        # 이슈 매칭
        if any(w in content for w in ["전쟁", "공격", "침공"]): issues.append("⚠️지정학리스크")
        if any(w in content for w in ["금리", "인상", "파월"]): issues.append("🏦거시경제")
        if any(w in content for w in ["반도체", "엔비디아", "AI"]): issues.append("💻기술주전쟁")
    except:
        issues.append("뉴스지연")
    return issues

# --- 3. 통합 스캔 및 매매 엔진 ---
def execute_trading_cycle():
    db = load_db()
    now = get_now()
    
    # 5분 주기 체크 (강제 실행 방어)
    if now.timestamp() - db.get("last_ts", 0) < 280:
        return db

    # [시세 수신] - 실패해도 N/A로 기록하여 "안 보이는 현상" 방지
    prices = {"BTC": "N/A", "NVDA": "N/A", "삼성": "N/A"}
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        # 코인
        btc_res = requests.get("https://api.upbit.com/v1/ticker?markets=KRW-BTC", timeout=3).json()
        prices["BTC"] = f"{btc_res[0]['trade_price']:,.0f}"
        
        # 미장/국장
        tickers = {"NVDA": "NVDA", "삼성": "005930.KS"}
        for name, code in tickers.items():
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{code}?interval=1m&range=1d"
            r = requests.get(url, headers=headers, timeout=3).json()
            p = r['chart']['result'][0]['meta']['regularMarketPrice']
            prices[name] = f"{p:,.1f}" if name == "NVDA" else f"{p:,.0f}"
    except: pass

    # [이슈 분석 및 로직 적용]
    current_issues = analyze_market_issues()
    trade_status = "대기"
    
    if "⚠️지정학리스크" in current_issues and RISK_STOP:
        trade_status = "🚨매수금지(전쟁)"
    elif "💻기술주전쟁" in current_issues:
        trade_status = "🔥기술주집중"

    # [로그 생성 및 DB 저장]
    db["last_ts"] = now.timestamp()
    price_str = f"BTC:{prices['BTC']} | NVDA:{prices['NVDA']} | 삼성:{prices['삼성']}"
    issue_str = f"[{'/'.join(current_issues)}]" if current_issues else "[평온]"
    
    log_entry = f"[{now.strftime('%H:%M')}] {price_str} {issue_str} -> {trade_status}"
    db["logs"].append(log_entry)
    if len(db["logs"]) > 30: db["logs"] = db["logs"][-30:]
    save_db(db)
    return db

# --- 4. UI 레이아웃 ---
st.set_page_config(page_title="AI Trader v7.1", layout="wide")
db = execute_trading_cycle()

st.title(f"🚀 AI 이슈 대응 엔진 v{VERSION}")

# 상단 자산 현황
c1, c2, c3 = st.columns(3)
c1.metric("국장(KRW)", "100만", "0%")
c2.metric("미장(USD)", "100만", "0%")
c3.metric("코인(BTC)", "100만", "0%")

st.divider()

# 로그 출력 (반드시 최신순으로 화면에 보임)
st.subheader("📜 5분 주기 통합 관제 로그")
if db["logs"]:
    for log in reversed(db["logs"]):
        # 이슈에 따른 색상 강조
        if "⚠️" in log or "🚨" in log:
            st.error(log)
        elif "🔥" in log:
            st.warning(log)
        else:
            st.write(log)
else:
    st.info("데이터 수집을 시작합니다. 잠시만 기다려주세요.")

if st.button("🔄 강제 새로고침"):
    st.rerun()
