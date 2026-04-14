import streamlit as st
import yfinance as yf
import datetime
import json
import os
import requests

# --- 1. 설정 ---
VERSION = "6.4-DIAG"
DB_FILE = "trading_db.json"

def get_now():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))

# --- 2. 시세 수신 (가장 단순화) ---
def get_data():
    results = []
    
    # 코인 테스트 (업비트)
    try:
        res = requests.get("https://api.upbit.com/v1/ticker?markets=KRW-BTC", timeout=5)
        if res.status_code == 200:
            price = res.json()[0]['trade_price']
            results.append(f"BTC:{price:,.0f}")
        else:
            results.append(f"Upbit:HTTP-{res.status_code}")
    except Exception as e:
        results.append(f"Upbit:Err-{str(e)[:10]}")

    # 주식 테스트 (야후)
    try:
        ticker = yf.Ticker("NVDA")
        # 가장 기초적인 info 호출
        price = ticker.fast_info['last_price']
        if price:
            results.append(f"NVDA:{price:,.1f}")
        else:
            results.append("NVDA:NoData")
    except Exception as e:
        results.append(f"NVDA:Err-{str(e)[:10]}")
        
    return " | ".join(results)

# --- 3. 실행 로직 ---
st.set_page_config(page_title="진단 모드", layout="centered")
st.title(f"🔍 긴급 진단 v{VERSION}")

# 버튼 누르면 즉시 시도
if st.button("🚨 지금 당장 시세 가져오기 시도"):
    with st.spinner("데이터 수신 중..."):
        current_data = get_data()
        st.success(f"결과: {current_data}") # 화면에 직접 출력
        
        # 로그 저장 시도
        try:
            if os.path.exists(DB_FILE):
                with open(DB_FILE, "r", encoding='utf-8') as f:
                    db = json.load(f)
            else:
                db = {"logs": []}
            
            log_msg = f"[{get_now().strftime('%H:%M:%S')}] {current_data}"
            db["logs"].append(log_msg)
            if len(db["logs"]) > 20: db["logs"] = db["logs"][-20:]
            
            with open(DB_FILE, "w", encoding='utf-8') as f:
                json.dump(db, f, indent=4, ensure_ascii=False)
            st.write("✅ 로그 파일 저장 성공")
        except Exception as e:
            st.error(f"❌ 저장 실패: {e}")

st.divider()

# 로그 표시
if os.path.exists(DB_FILE):
    try:
        with open(DB_FILE, "r", encoding='utf-8') as f:
            db = json.load(f)
            for log in reversed(db.get("logs", [])):
                st.text(log)
    except:
        st.write("로그 파일을 읽을 수 없습니다.")
else:
    st.write("저장된 로그 파일이 없습니다.")
