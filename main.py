import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# 1. 앱 설정
st.set_page_config(page_title="AI Trading Simulator", layout="wide")
st.title("🤖 AI 통합 시뮬레이터 (구조 전면 재배치)")

# 2. 투자금 설정
with st.sidebar:
    st.header("💰 설정")
    budget_stock = 100000000
    budget_coin = 100000000

# 3. 핵심 엔진
def run_simulation(ticker, budget, name):
    # 데이터를 가져올 때 'nothreading'과 'proxy' 영향을 배제하고 순수 데이터만 호출
    try:
        data = yf.download(ticker, period="6mo", interval="1d", progress=False)
        if data.empty:
            return None, budget, []
        
        # [핵심] 멀티인덱스가 발생하면 무조건 첫 번째 레벨(티커명)을 제거하고 평면화
        df = data.copy()
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        # 필요한 열만 추출 (가끔 중복 열이 생기는 경우 방지)
        df = df[['Close', 'Volume']].iloc[:, :2]
        df.columns = ['Close', 'Volume']
        
    except Exception as e:
        return None, budget, []

    # 지표 계산 (안전하게 계산하기 위해 데이터가 충분할 때만 진행)
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['Vol_Avg'] = df['Volume'].rolling(window=20).mean()
    df = df.dropna()
    
    cash = budget
    shares = 0
    history = []

    for i in range(len(df)):
        try:
            curr_p = float(df['Close'].iloc[i])
            curr_v = float(df['Volume'].iloc[i])
            avg_v = float(df['Vol_Avg'].iloc[i])
            ma20 = float(df['MA20'].iloc[i])
            
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

# 4. 화면 출력 (구조 단순화)
assets = [
    {"t": "005930.KS", "n": "🇰🇷 삼성전자", "b": budget_stock},
    {"t": "NVDA", "n": "🇺🇸 엔비디아", "b": budget_stock},
    {"t": "BTC-KRW", "n": "🪙 비트코인", "b": budget_coin}
]

cols = st.columns(3)
total_val = 0

for i, a in enumerate(assets):
    with cols[i]:
        df, final, hist = run_simulation(a['t'], a['b'], a['n'])
        if df is not None and not df.empty:
            total_val += final
            st.metric(a['n'], f"{final:,.0f}원", f"{((final/a['b'])-1)*100:.2f}%")
            st.line_chart(df['Close'])
        else:
            st.error(f"{a['n']} 데이터를 찾을 수 없음")

st.divider()
st.header(f"💰 전체 합산 자산: {total_val:,.0f}원")
