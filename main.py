import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# 1. 앱 기본 설정
st.set_page_config(page_title="AI Trading Simulator", layout="wide")

st.title("🤖 AI 통합 자산 시뮬레이터 (Pro)")
st.caption("최종 업데이트: 2026-04-13 | 국내/미국 주식 & 빗썸 코인 실시간 연동")

# 2. 투자금 설정
with st.sidebar:
    st.header("💰 가상 투자 설정")
    budget_stock = 100000000
    budget_coin = 100000000
    st.divider()
    st.subheader("⚙️ AI 매매 로직")
    st.write("- **매수**: 거래량 2.5배 폭증 + 20일 이평선 돌파")
    st.write("- **매도**: 5% 익절 또는 3% 손절")

# 3. AI 시뮬레이션 엔진 함수
def run_simulation(ticker, budget, name):
    df = yf.download(ticker, period="6mo", interval="1d", progress=False)
    if df.empty:
        return None, budget, []

    # 지표 계산
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['Vol_Avg'] = df['Volume'].rolling(window=20).mean()
    
    cash = budget
    shares = 0
    history = []

    # 데이터 분석 루프
    for i in range(20, len(df)):
        current_price = df['Close'].iloc[i]
        volume = df['Volume'].iloc[i]
        
        # [중요] 특정 시점(i)의 평균 거래량 값을 단일 값으로 미리 추출
        current_avg_vol = df['Vol_Avg'].iloc[i]
        current_ma20 = df['MA20'].iloc[i]
        
        # [에러 해결] 단일 값(Scalar)끼리만 비교하도록 수정
        if volume > (current_avg_vol * 2.5) and current_price > current_ma20 and cash > 0:
            shares = cash / current_price
            cash = 0
            history.append((df.index[i], 'BUY', current_price))
            
        elif shares > 0:
            buy_price = history[-1][2]
            profit_rate = (current_price - buy_price) / buy_price
            if profit_rate > 0.05 or profit_rate < -0.03:
                cash = shares * current_price
                shares = 0
                history.append((df.index[i], 'SELL', current_price))

    final_val = cash + (shares * df['Close'].iloc[-1])
    return df, final_val, history

# 4. 메인 화면 구성
col1, col2, col3 = st.columns(3)

assets = [
    {"ticker": "005930.KS", "name": "🇰🇷 삼성전자", "budget": budget_stock, "col": col1},
    {"ticker": "NVDA", "name": "🇺🇸 엔비디아", "budget": budget_stock, "col": col2},
    {"ticker": "BTC-KRW", "name": "🪙 비트코인", "budget": budget_coin, "col": col3}
]

total_final_assets = 0

for a in assets:
    with a['col']:
        df, final_val, history = run_simulation(a['ticker'], a['budget'], a['name'])
        if df is not None:
            profit = ((final_val / a['budget']) - 1) * 100
            total_final_assets += final_val
            st.subheader(a['name'])
            st.metric("최종 평가자산", f"{final_val:,.0f}원", f"{profit:.2f}%")
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name='가격'))
            fig.update_layout(margin=dict(l=0, r=0, t=30, b=0), height=250)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error(f"{a['name']} 데이터 불러오기 실패")

# 5. 하단 리포트
st.divider()
total_initial = (budget_stock * 2) + budget_coin
total_profit_rate = ((total_final_assets / total_initial) - 1) * 100
st.header(f"📈 총 수익률: {total_profit_rate:.2f}%")
st.write(f"최종 합산 자산: **{total_final_assets:,.0f}원**")
