import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# 1. 앱 설정
st.set_page_config(page_title="AI Trading Simulator", layout="wide")
st.title("🤖 AI 통합 시뮬레이터 (삼성전자 티커 오류 해결)")

# 2. 투자금 설정
with st.sidebar:
    st.header("💰 설정")
    budget_stock = 100000000
    budget_coin = 100000000

# 3. 핵심 엔진
def run_simulation(ticker, budget, name):
    # 데이터 수집 (최근 6개월)
    df = yf.download(ticker, period="6mo", interval="1d", progress=False)
    
    if df.empty:
        return None, budget, []

    # [핵심] 데이터 구조 강제 재조립 (모든 티커 오류 방지)
    try:
        new_df = pd.DataFrame(index=df.index)
        # 'Close'라는 이름이 들어간 열 중 첫 번째를 가격으로 선택
        close_col = [col for col in df.columns if 'Close' in (col[0] if isinstance(col, tuple) else col)][0]
        # 'Volume'이라는 이름이 들어간 열 중 첫 번째를 거래량으로 선택
        vol_col = [col for col in df.columns if 'Volume' in (col[0] if isinstance(col, tuple) else col)][0]
        
        new_df['Close'] = df[close_col]
        new_df['Volume'] = df[vol_col]
        df = new_df
    except Exception as e:
        # 위 방법이 실패할 경우 최후의 수단으로 열 인덱스로 접근
        df.columns = df.columns.get_level_values(0) if isinstance(df.columns, pd.MultiIndex) else df.columns

    # 데이터 정리 및 지표 계산
    df = df.dropna()
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['Vol_Avg'] = df['Volume'].rolling(window=20).mean()
    
    cash = budget
    shares = 0
    history = []

    # 분석 루프 (20일치 데이터가 쌓인 후부터 시작)
    for i in range(20, len(df)):
        try:
            curr_p = float(df['Close'].iloc[i])
            curr_v = float(df['Volume'].iloc[i])
            avg_v = float(df['Vol_Avg'].iloc[i])
            ma20 = float(df['MA20'].iloc[i])
            
            # AI 매매 로직
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
        if df is not None and not df.empty:
            total_val += final
            profit_pct = ((final / a['b']) - 1) * 100
            st.metric(a['n'], f"{final:,.0f}원", f"{profit_pct:.2f}%")
            
            # 그래프
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name='가격'))
            fig.update_layout(margin=dict(l=0, r=0, t=30, b=0), height=200)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error(f"{a['n']} 데이터를 가져오는 중입니다...")

st.divider()
st.header(f"💰 합산 자산: {total_val:,.0f}원")
