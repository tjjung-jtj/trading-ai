import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

# 1. 앱 기본 설정 및 디자인
st.set_page_config(page_title="AI Trading Simulator", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    h1 { color: #1E1E1E; font-family: 'Pretendard', sans-serif; }
    </style>
    """, unsafe_allow_html=True)

st.title("🤖 AI 통합 자산 시뮬레이터 (Pro)")
st.caption(f"최종 업데이트: 2026-04-13 | 국내/미국 주식 & 빗썸 코인 실시간 연동")

# 2. 투자금 설정 (사이드바)
with st.sidebar:
    st.header("💰 가상 투자 설정")
    st.info("각 자산별로 초기 자본금 1억 원을 투입하여 AI가 운용을 시작합니다.")
    budget_stock = 100000000
    budget_coin = 100000000
    st.divider()
    st.subheader("⚙️ AI 매매 로직")
    st.write("- **매수**: 거래량이 20일 평균의 2.5배 폭증 + 주가가 20일 이동평균선 돌파")
    st.write("- **매도**: 5% 익절 또는 3% 손절 (자동 대응)")

# 3. AI 시뮬레이션 엔진 함수
def run_simulation(ticker, budget, name):
    # 데이터 수집 (최근 6개월)
    df = yf.download(ticker, period="6mo", interval="1d", progress=False)
    if df.empty:
        return None, budget, []

    # 지표 계산
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['Vol_Avg'] = df['Volume'].rolling(window=20).mean()
    
    cash = budget
    shares = 0
    history = []

    # 시뮬레이션 루프 (에러 수정 완료)
    for i in range(20, len(df)):
        current_price = df['Close'].iloc[i]
        volume = df['Volume'].iloc[i]
        avg_vol = df['Vol_Avg'].iloc[i]
        
        # [수정 포인트] avg_vol.iloc[i]로 특정 시점의 단일 값을 비교
        if volume > (avg_vol * 2.5) and current_price > df['MA20'].iloc[i] and cash > 0:
            shares = cash / current_price
            cash = 0
            history.append((df.index[i], 'BUY', current_price))
            
        elif shares > 0:
            buy_price = history[-1][2]
            profit_rate = (current_price - buy_price) / buy_price
            
            # 익절 5% 또는 손절 3% 로직
            if profit_rate > 0.05 or profit_rate < -0.03:
                cash = shares * current_price
                shares = 0
                history.append((df.index[i], 'SELL', current_price))

    final_val = cash + (shares * df['Close'].iloc[-1])
    return df, final_val, history

# 4. 메인 대시보드 화면 구성
col1, col2, col3 = st.columns(3)

assets = [
    {"ticker": "005930.KS", "name": "🇰🇷 삼성전자 (KOSPI)", "budget": budget_stock, "col": col1},
    {"ticker": "NVDA", "name": "🇺🇸 엔비디아 (NASDAQ)", "budget": budget_stock, "col": col2},
    {"ticker
