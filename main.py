import streamlit as st
import datetime
import json
import os
import requests

# 1. 설정 (예산 100만 원은 코드에 고정)
VERSION = "9.1-MEMORY-FIX"
DB_FILE = "trading_db.json"

def get_now():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))

# 세션 메모리 초기화 (서버가 깨어있는 동안 로그 유지 보조)
if "temp_logs" not in st.session_state:
    st.session_state.temp_logs = []

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding='utf-8') as f:
                data = json.load(f)
                # 예산 강제 주입
                data["balance_krw"] = 1000000
                data["balance_usd"] = 1000000
                data["balance_btc"] = 1000000
                return data
        except: pass
    return {"logs": [], "last_ts": 0}

def save_db(data):
    try:
        with open(DB_FILE, "w", encoding='utf-8') as f:
            json.dump(data, f)
    except: pass

# 2. 데이터 수집 (최적화)
def fetch_all():
    res = {"BTC": "ERR", "NVDA": "ERR", "삼성": "ERR", "ISSUE": "평온"}
    h = {'User-Agent': 'Mozilla/5.0'}
    try:
        # 코인
        b = requests.get("https://api.upbit.com/v1/ticker?markets=KRW-BTC", timeout=3).json()
        res["BTC"] = f"{b[0]['trade_price']:,.0f}"
        # 주식
        n_r = requests.get("https://query1.finance.yahoo.com/v8/finance/chart/NVDA?interval=1m&range=1d", headers=h, timeout=3).json()
        res["NVDA"] = f"{n_r['chart']['result'][0]['meta']['regularMarketPrice']:.1f}"
        s_r = requests.get("https://query1.finance.yahoo.com/v8/finance/chart/005930.KS?interval=1m&range=1d", headers=h, timeout=3).json()
        res["삼성"] = f"{s_r['chart']['result'][0]['meta']['regularMarketPrice']:,.0f}"
    except: pass
    return res

# 3. 자동 실행 엔진
db = load_db()
now = get_now()

# 4분(240초) 주기 체크
if (now.timestamp() - db.get("last_ts", 0) >= 240) or not db["logs"]:
    data = fetch_all()
    log_msg = f"[{now.strftime('%H:%M')}] BTC:{data['BTC']} | NVDA:{data['NVDA']} | 삼성:{data['삼성']}"
    db["logs"].append(log_msg)
    db["last_ts"] = now.timestamp()
    db["logs"] = db["logs"][-30:] # 최근 30개 유지
    save_db(db)
    st.session_state.temp_logs = db["logs"]

# 4. 화면 구성
st.set_page_config(page_title="Asset Watcher", layout="wide")
st.title(f"🚀 자산 관제소 v{VERSION}")

# 예산 상단 고정
st.subheader("💰 자산 현황")
c1, c2, c3 = st.columns(3)
c1.metric("국장 예산", "100만 원")
c2.metric("미장 예산", "100만 원")
c3.metric("코인 예산", "100만 원")

st.divider()

# 로그 출력 (파일 로그와 세션 로그 중 더 많은 것을 출력)
display_logs = db["logs"] if len(db["logs"]) >= len(st.session_state.temp_logs) else st.session_state.temp_logs

if not display_logs:
    st.info("데이터를 수집하고 있습니다. 1분만 기다려주세요.")
else:
    for l in reversed(display_logs):
        st.write(l)

if st.button("🔄 즉시 새로고침"):
    st.rerun()
