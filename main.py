import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# 1. 앱 설정
st.set_page_config(page_title="AI Trading Simulator", layout="wide")
st.title("🤖 AI 통합 시뮬레이터 (삼성전자 복구 최종)")

# 2. 투자금 설정
with st.sidebar:
    st.header("💰 설정")
    budget_stock = 100000000
    budget_coin = 100000000

# 3. 핵심 엔진
def run_simulation(ticker, budget, name):
    # 데이터를 가져올 때 구조가 꼬이지 않도록 수동 설정
    data = yf.download(ticker, period="6mo", interval="1d", progress=False)
    
    if data.empty:
        return None, budget, []

    # [마지막 수단] 데이터 구조를 완전히 무시하고 '첫 번째' 가격 데이터만 추출
    try:
        # 1. 가격(Close) 추출
        if 'Close' in data.columns:
            df_close = data['Close']
            # 만약 Series가 아니라 DataFrame이면 첫 번째 열 선택
            if isinstance(df_close, pd.DataFrame):
                df_close = df_close.iloc[:, 0]
        else:
            df_close = data.iloc[:, 0] # 이름이 없으면 그냥 첫 번째 열

        # 2. 거래량(Volume) 추출
        if 'Volume' in data.columns:
            df_vol = data['Volume']
            if isinstance(df_vol, pd.DataFrame):
                df_vol = df_vol.iloc[:, 0]
        else:
            df_vol = data.iloc[:, -1] # 이름이 없으면 가장 마지막 열

        # 3. 새 데이터프레임으로 깨끗하게 재구성
        df = pd.DataFrame({'Close': df_close, 'Volume': df_vol}, index=data.index)
        df = df.dropna()
    except Exception as e:
        st.error(f"{name} 구조 분석 실패: {e}")
        return None, budget, []

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
            avg_v = float(df['Vol_Avg'].iloc[i])
            ma20 = float(df['MA20'].iloc[i])
            
            # AI 매수 조건 (거래량 폭증 + 이평선 돌파)
            if curr_v > (avg_v * 2.5) and curr_p > ma20 and cash > 0:
                shares = cash / curr_p
                cash = 0
                history.append((df.index[i], 'BUY', curr_p))
            elif shares > 0:
                buy_p = history[-1][2]
                profit = (curr_p - buy_p) / buy_p
                # 5% 익절 / 3% 손절
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
            st.line_chart(df['Close'])
        else:
            st.warning(f"{a['n']} 데이터를 불러오는 중...")

st.divider()
st.header(f"💰 전체 합산 자산: {total_val:,.0f}원")
