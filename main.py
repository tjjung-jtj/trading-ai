import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# 1. 앱 설정
st.set_page_config(page_title="AI Trading Simulator", layout="wide")
st.title("🤖 AI 통합 시뮬레이터 (삼성전자 오류 해결판)")

# 2. 투자금 설정
with st.sidebar:
    st.header("💰 가상 투자 설정")
    budget_stock = 100000000
    budget_coin = 100000000

# 3. 핵심 엔진
def run_simulation(ticker, budget, name):
    # 데이터 수집 시 멀티인덱스 자동 방지 처리
    df = yf.download(ticker, period="6mo", interval="1d", progress=False, auto_adjust=True)
    
    if df.empty or len(df) < 20:
        return None, budget, []
    
    # 데이터 구조 평면화 (삼성전자 특유의 겹침 현상 해결)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # 데이터 정리 (NaN 값 제거)
    df = df.dropna(subset=['Close', 'Volume'])

    # 지표 생성
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['Vol_Avg'] = df['Volume'].rolling(window=20).mean()
    
    cash = budget
    shares = 0
    history = []

    # 데이터 분석 루프
    for i in range(20, len(df)):
        try:
            # .values[0] 혹은 float()를 사용하여 완벽한 단일 값 추출
            curr_p = float(df['Close'].iloc[i])
            curr_v = float(df['Volume'].iloc[i])
            avg_v = float(df['Vol_Avg'].iloc[i])
            ma20 = float(df['MA20'].iloc[i])
            
            # AI 매수/매도 로직
            if curr_v > (avg_v * 2.5) and curr_p > ma20 and cash > 0:
                shares = cash / curr_p
                cash = 0
                history.append((df.index[i], 'BUY', curr_p))
            elif shares > 0:
                buy_p = history[-1][2]
                profit = (curr_p - buy_p) / buy_p
                if profit > 0.05 or profit < -0.03:
                    cash = shares * curr_p
                    shares = 0
                    history.append((df.index[i], 'SELL', curr_p))
        except:
            continue

    final_val = cash + (shares * float(df['Close'].iloc[-1]))
    return df, final_val, history

# 4. 화면 출력
cols = st.columns(3)
assets = [
    {"t": "005930.KS", "n": "🇰🇷 삼성전자", "b": budget_stock, "c": cols[0]},
    {"t": "NVDA", "n": "🇺🇸 엔비디아", "b": budget_stock, "c": cols[1]},
    {"t": "BTC-KRW", "n": "🪙 비트코인", "b": budget_coin, "c": cols[2]}
]

total_val = 0
for a in assets:
    with a['c']:
        df, final, hist = run_simulation(a['t'], a['b'], a['n'])
        if df is not None:
            total_val += final
            profit_pct = ((final / a['b']) - 1) * 100
            st.metric(a['n'], f"{final:,.0f}원", f"{profit_pct:.2f}%")
            
            # 그래프 시각화 (더 세련된 방식)
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name='가격'))
            fig.update_layout(margin=dict(l=0, r=0, t=30, b=0), height=200)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning(f"{a['n']} 데이터를 현재 불러올 수 없습니다. 잠시 후 새로고침 해주세요.")

st.divider()
st.header(f"💰 전체 합산 자산: {total_val:,.0f}원")
