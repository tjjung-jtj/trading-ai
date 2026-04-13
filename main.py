import streamlit as st
import yfinance as yf
import datetime
import json
import os

# --- 0. 버전 설정 ---
VERSION = "1.6.2"

def get_now():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))

DB_FILE = "trading_db.json"

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding='utf-8') as f:
                return json.load(f)
        except: pass
    return {"balance_kr": 1000000, "balance_us": 1000000, "balance_coin": 1000000, "portfolio": [], "logs": [], "scan_count": 0, "last_scan": "없음"}

def save_db(data):
    with open(DB_FILE, "w", encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# --- 1. [최후의 수단] st.context 사용 ---
# query_params가 안 먹힐 때 직접 주소창의 인자를 낚아챕니다.
is_auto = False
try:
    # 1순위: 최신 st.context 방식
    if "auto" in st.context.query_params:
        if st.context.query_params["auto"] == "true":
            is_auto = True
    # 2순위: 구형 방식 보조
    elif st.query_params.get("auto") == "true":
        is_auto = True
except:
    # 3순위: 전통적 방식
    if st.query_params.to_dict().get("auto") == "true":
        is_auto = True

if is_auto:
    db = load_db()
    now_str = get_now().strftime('%Y-%m-%d %H:%M:%S')
    
    # [핵심 엔진 실행]
    # 여기에 실제 yfinance 매매 로직이 포함됩니다.
    
    db["scan_count"] += 1
    db["last_scan"] = now_str
    db['logs'].append(f"[{now_str}] 🤖 v{VERSION} 자동 스캔 성공")
    save_db(db)
    
    # 크론잡에게 텍스트로만 응답 (HTML 방지)
    st.write(f"V{VERSION}_SUCCESS")
    st.stop()

# --- 2. 메인 UI (여기서부터는 기존과 동일) ---
st.set_page_config(page_title="AI 자산관리 v1.6.2", layout="wide")
db = load_db()

st.title("🤖 AI 자산 관리 시스템")
st.info(f"📊 **엔진 상태 (v{VERSION})** | 마지막 스캔: {db.get('last_scan')} | **누적 스캔: {db.get('scan_count')}회**")

# ... (이하 버튼 및 잔고 코드 생략) ...
