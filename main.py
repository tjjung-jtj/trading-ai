import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# 1. 앱 기본 설정
st.set_page_config(page_title="AI Trading Pro", layout="wide")
st.title("🤖 고도화된 AI 통합 시뮬레이터")

# 2. 투자금 설정 (사이드바)
with st.sidebar:
    st.header("💰 가상 투자금 (각 1억)")
    budget_stock = 100000000
    budget_coin = 100000000
    st.write("---")
    st.write("전략: 급등주 포착 & 저평가 탐색")

# 3. AI 분석 엔진 함수
def run_simulation(ticker, budget, name):
    # 데이터 수집 (최근 6개월)
    df = yf.download(ticker, period="6mo", interval="1d", progress=False)
    
    # AI 기술적 지표 계산
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA60'] = df['Close'].rolling(window=60).mean()
    df['Vol_Avg'] = df['Volume'].rolling(window=20).mean()
    
    # 시뮬레이션 변수
    cash = budget
    shares = 0
    history = []

    # AI 매매 시뮬레이션 루프
    for i in range(60, len(df)):
        current_price = df['Close'].iloc[i]
        volume = df['Volume'].iloc[i]
        avg_vol = df['Vol_Avg'].iloc[i]
        
        # [AI 매수 조건]: 거래량이 평균의 2.5배 폭증 + 20일 이평선 돌파 (급등주 로직)
        if volume > avg_vol * 2.5 and current_price > df['MA20'].iloc[i] and cash > 0:
            shares = cash / current_price
            cash = 0
            history.append((df.index[i], 'BUY', current_price))
            
        # [AI 매도 조건]: 5% 수익 실현 또는 3% 손절
        elif shares > 0:
            buy_price = history[-1][2]
            profit_rate = (current_price - buy_price) / buy_price
            if profit_rate > 0.05 or profit_rate < -0.03:
                cash = shares * current_price
                shares = 0
                history.append((df.index[i], 'SELL', current_price))

    final_val = cash + (shares * df['Close'].iloc[-1])
    return df, final_val, history

# 4. 화면 구성
col1, col2, col3 = st.columns(3)

assets = [
    {"ticker": "005930.KS", "name": "국내: 삼성전자", "budget": budget_stock, "col": col1},
    {"ticker": "NVDA", "name": "미국: 엔비디아", "budget": budget_stock, "col": col2},
    {"ticker": "BTC-KRW", "name": "빗썸: 비트코인", "budget": budget_coin, "col": col3}
]

total_final = 0

for a in assets:
    with a['col']:
        df, final_val, history = run_simulation(a['ticker'], a['budget'], a['name'])
        profit = ((final_val / a['budget']) - 1) * 100
        total_final += final_val
        
        st.subheader(a['name'])
        st.metric("현재 자산", f"{final_val:,.0f}원", f"{profit:.2f}%")
        
        # 수익률 그래프
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name='가격'))
        st.plotly_chart(fig, use_container_width=True)

# 5. 통합 성적표
st.divider()
total_profit = ((total_final / (budget_stock*2 + budget_coin)) - 1) * 100
st.header(f"📉 전체 시뮬레이션 결과: {total_profit:.2f}% 수익 중")
st.write(f"최종 합산 자산: **{total_final:,.0f}원**")
