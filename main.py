import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# 1. 앱 설정
st.set_page_config(page_title="AI Trading Simulator", layout="wide")
st.title("🤖 AI 통합 시뮬레이터 (삼성전자 복구 완료)")

# 2. 투자금 설정
with st.sidebar:
    st.header("💰 설정")
    budget_stock = 100000000
    budget_coin = 100000000

# 3. 핵심 엔진
def run_simulation(ticker, budget, name):
    # 데이터 수집
    df = yf.download(ticker, period="6mo", interval="1d", progress=False)
    
    if df.empty:
        return None, budget, []

    # [핵심] 삼성전자 등 멀티인덱스 데이터를 강제로 단일화하는 가장 강력한 방법
    if isinstance(df.columns, pd.MultiIndex):
        # 'Close'와 'Volume' 열만 선택해서 가져옴
        try:
            temp_df = pd.DataFrame(index=df.index)
            temp_df['Close'] = df['Close'][ticker] if ticker in df['Close'] else df['Close'].iloc[:, 0]
            temp_df['Volume'] = df['Volume'][ticker] if ticker in df['Volume'] else df['Volume'].iloc[:, 0]
            df = temp_df
        except:
            df.columns = df.columns.get_level_values(0)

    # 데이터 정리
    df = df.dropna()

    # 지표 계산
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['Vol_Avg'] = df['Volume'].rolling(window=20).mean()
    
    cash = budget
    shares = 0
    history = []

    # 분석 루프
    for i in range(20, len(df)):
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
            st.metric(a['n'], f"{final:,.0f}원", f"{((final/a['b'])-1)*100:.2f}%")
            st.line_chart(df['Close'])
        else:
            st.error(f"{a['n']} 데이터 로드 실패")

st.divider()
st.header(f"💰 합산 자산: {total_val:,.0f}원")
