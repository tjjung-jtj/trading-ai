import streamlit as st
import yfinance as yf
import datetime
import json
import os

# --- 0. 버전 설정 ---
VERSION = "1.8.1"

def get_now():
    # 한국 시간 설정 (UTC+9)
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))

DB_FILE = "trading_db.json"

# 데이터 로드/저장 함수
def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding='utf-8') as f:
                return json.load(f)
        except: pass
    # 파일이 없거나 에러 시 기본값
    return {
        "balance_kr": 1000000, 
        "balance_us": 1000000, 
        "balance_coin": 1000000, 
        "portfolio": [], 
        "logs": [], 
        "scan_count": 0, 
        "last_scan": "없음",
        "last_scan_raw": ""
    }

def save_db(data):
    with open(DB_FILE, "w", encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# --- 1. 엔진 가동 함수 ---
def run_engine(reason="자동"):
    db = load_db()
    now = get_now()
    now_str = now.strftime('%Y-%m-%d %H:%M:%S')
    
    # 중복 실행 방지 (1분 내 중복 실행 차단)
    current_minute = now.strftime('%Y-%m-%d %H:%M')
    if db.get("last_scan_raw") == current_minute and reason == "자동":
        return db

    # [시세 스캔 로직] - 샘플로 BTC 조회
    try:
        yf.download("BTC-USD", period="1d", interval="1m", progress=False)
    except:
        pass
    
    db["scan_count"] += 1
    db["last_scan"] = now_str
    db["last_scan_raw"] = current_minute
    db['logs'].append(f"[{now_str}] 🤖 {reason} 스캔 완료 (v{VERSION})")
    
    # 로그가 너무 많아지면 성능 저하되므로 최근 100개만 유지
    if len(db['logs']) > 100:
        db['logs'] = db['logs'][-100:]
        
    save_db(db)
    return db

# --- 2. 자동 실행 감지 (URL 파라미터 체크) ---
# 주소 끝에 ?auto=true가 붙어 있으면 UI를 그리기 전에 엔진부터 돌립니다.
if st.query_params.get("auto") == "true":
    run_engine("자동")
    # 로봇에게는 가벼운 응답만 주고 실행 종료 (Render 자원 절약)
    st.write("ENGINE_WORKING")
    st.stop()

# --- 3. 메인 UI (여기서부터 화면에 보임) ---
st.set_page_config(page_title=f"AI Bot v{VERSION}", layout="wide")
db = load_db()

st.title("🤖 AI 자산 관리 시스템")

# 상태 요약 정보
st.info(f"📊 **엔진 상태 (v{VERSION})** | 마지막 스캔: {db.get('last_scan')} | **누적 스캔: {db.get('scan_count', 0)}회**")

# 잔고 표시 구간
c1, c2, c3 = st.columns(3)
with c1:
    st.metric("🇰🇷 국장 잔고", f"{db.get('balance_kr', 0):,.0f}원")
with c2:
    st.metric("🇺🇸 미장 잔고", f"{db.get('balance_us', 0):,.0f}$")
with c3:
    st.metric("🪙 코인 잔고", f"{db.get('balance_coin', 0):,.0f}원")

st.divider()

# 수동 조작 버튼
col1, col2 = st.columns(2)
with col1:
    if st.button("🚀 즉시 스캔 가동", use_container_width=True):
        db = run_engine("수동")
        st.rerun()
with col2:
    if st.button("🔄 데이터 초기화", use_container_width=True):
        if os.path.exists(DB_FILE):
            os.remove(DB_FILE)
        st.rerun()

# --- 4. 로그 출력 (에러 수정된 부분) ---
st.subheader("📜 최근 거래 로그 (최신 10개)")
logs = db.get('logs', [])
if logs:
    # reversed 결과를 list로 변환하여 에러 방지
    for log in list(reversed(logs))[:10]:
        st.write(log)
else:
    st.write("로그가 없습니다.")
