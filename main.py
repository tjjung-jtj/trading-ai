import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# 1. 앱 설정
st.set_page_config(page_title="AI Trading Simulator", layout="wide")
st.title("🤖 AI 통합 시뮬레이터 (삼성전자 완벽 복구)")

# 2. 투자금 설정
with st.sidebar:
    st.header("💰 설정")
    budget_stock = 100000000
    budget_coin = 100000000

# 3. 핵심 엔진
def run_simulation(ticker, budget, name):
    # 데이터를 가져올 때 'group_by' 설정을 꺼서 구조를 단순화
    df = yf.download(ticker, period="6mo", interval="1d", progress=False, group_by='column')
    
    if df.empty:
        return None, budget, []

    # [최종 무기] 이름 대신 '위치'로 데이터를 강제 재구성
    try:
        new_df = pd.DataFrame(index=df.index)
        
        # 'Close' 열과 'Volume' 열이 포함된 데이터를 위치 기반으로 추출
        # 보통 Close는 0~4번 사이, Volume은 5번 근처에 위치함
        if 'Close' in df.columns:
            new_df['Close'] = df['Close'].iloc[:, 0] if len(df['Close'].shape) > 1 else df['Close']
        if 'Volume' in df.columns:
            new_df['Volume'] = df['Volume'].iloc[:, 0] if len(df['Volume'].shape) > 1 else df['Volume']
            
        df = new_df.dropna()
    except:
        # 위 방법도 실패 시 데이터프레임을 완전히 새로 고침
        df.columns = df.columns.get_level_values(0)
        df = df[['Close', 'Volume']].copy()

    # 지표 계산
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
            avg_v = float(df['Vol_Avg'].iloc[i]) if not pd.isna(df['Vol_Avg'].iloc[i]) else 0
            ma20 = float(df['MA20'].iloc[i]) if not pd.isna(df['MA20'].iloc[i]) else 0
            
            if curr_v > (avg_v * 2.5) and curr_p > ma20 and cash > 0 and avg_v > 0:
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
        if df is not None and len(df) > 0:
            total_val += final
            st.metric(a['n'], f"{final:,.0f}원", f"{((final/a['b'])-1)*100:.2f}%")
            st.line_chart(df['Close'])
        else:
            st.error(f"{a['n']} 데이터 로드 중...")

st.divider()
st.header(f"💰 전체 합산 자산: {total_val:,.0f}원")
