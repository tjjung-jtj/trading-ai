import streamlit as st
import datetime
import json
import os
import requests

# --- 1. 설정 및 전략 (이슈 키워드 추가) ---
VERSION = "6.9-ISSUE-AWARE"
DB_FILE = "trading_db.json"

# [감시 키워드] 뉴스에 아래 단어가 뜨면 매수 신중 (리스크 관리)
RISK_KEYWORDS = ["전쟁", "금리인상", "폭락", "제재", "인플레이션"]
BOOST_KEYWORDS = ["반도체", "AI", "실적발표", "공급계약"]

def get_now():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))

# --- 2. 뉴스 이슈 감지 함수 ---
def get_market_sentiment():
    try:
        # 뉴스 피드에서 헤드라인 수집 (Google News RSS 등 활용 가능)
        # 여기서는 가장 간단하고 차단이 적은 방식으로 구현
        url = "https://news.google.com/rss/search?q=주식+반도체+전쟁&hl=ko&gl=KR&ceid=KR:ko"
        res = requests.get(url, timeout=5)
        text = res.text
        
        score = 0
        found_risks = [w for w in RISK_KEYWORDS if w in text]
        found_boosts = [w for w in BOOST_KEYWORDS if w in text]
        
        # 리스크 키워드가 많으면 음수, 호재가 많으면 양수
        score = len(found_boosts) - len(found_risks)
        return score, found_risks + found_boosts
    except:
        return 0, []

# --- 3. 시세 및 매매 엔진 (이슈 반영) ---
def run_trading_engine():
    db = load_db() # 기존 load_db 함수 사용
    now = get_now()
    if now.timestamp() - db.get("last_ts", 0) < 270: return db

    # 1. 뉴스 심리 파악
    sentiment_score, active_issues = get_market_sentiment()
    
    # 2. 시세 수신 (v6.8과 동일)
    headers = {'User-Agent': 'Mozilla/5.0'}
    results = []
    trade_note = ""
    
    # [예시: NVDA 기술주 전쟁 대응 로직]
    try:
        url_nvda = "https://query1.finance.yahoo.com/v8/finance/chart/NVDA?interval=1m&range=1d"
        res = requests.get(url_nvda, headers=headers, timeout=5).json()
        curr_nvda = res['chart']['result'][0]['meta']['regularMarketPrice']
        
        # 이슈가 너무 안 좋으면(score < -2) 매수 보류, 좋으면 변동성 K값 완화
        if sentiment_score < -2:
            trade_note += " | ⚠️ 뉴스 악재로 매수 보류"
        elif "NVDA" not in db['holdings'] and sentiment_score > 1:
            # 호재 발생 시 공격적 매수 로직 추가 가능
            pass
    except: pass

    # 기록 및 저장 (UI 표시용)
    db["last_ts"] = now.timestamp()
    issue_text = f"이슈: {', '.join(active_issues[:3])}" if active_issues else "이슈 없음"
    db["logs"].append(f"[{now.strftime('%H:%M')}] {issue_text}{trade_note}")
    # ... (DB 저장 로직)
    return db

# --- 4. UI (뉴스 섹션 추가) ---
st.title(f"🤖 기술주/이슈 대응 엔진 v{VERSION}")
score, issues = get_market_sentiment()

st.subheader("🌐 실시간 시장 이슈")
if issues:
    st.warning(f"감지된 키워드: {', '.join(issues)}")
    st.info(f"시장 심리 점수: {score} (낮을수록 위험)")
else:
    st.success("특이 이슈 없음 - 정상 가동")

# ... (기존 잔고 및 로그 표시 UI)
