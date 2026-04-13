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
    st.header("💰 가상 투자 설정")
    budget_stock = 100000000
    budget_coin = 100000000

# 3. 핵심 엔진
def run_simulation(ticker, budget, name):
    # 데이터를 가져올 때 가장 원시적인 형태로 가져옴
    data = yf.download(ticker, period="6mo", interval="1d", progress=False)
    
    if data.empty:
        return None, budget, []

    try:
        # [최종 해결책] 데이터가 어떻게 꼬여있든 'Close'와 'Volume' 글자가 들어간 열을 강제로 추출
        # Multi-index 구조를 완전히 파괴하고 평면화함
        df = data.copy()
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = ['_'.join(col).strip() for col in df.columns.values]
        
        # 'Close'라는 단어가 포함된 첫 번째 열 찾기
        close_col = [c for c in df.columns if 'Close' in c][0]
        # 'Volume'이라는 단어가 포함된 첫 번째 열 찾기
        vol_col = [c for c in df.columns if 'Volume' in c][0]
        
        # 새로운 깨끗한 데이터프레임 생성
        clean_df = pd.DataFrame(index=df.index)
        clean_df['Close'] = df[close_col]
        clean_df['Volume'] = df[vol_col]
        df = clean_df.dropna()
    except:
        # 위 방법 실패 시, 인덱스 번호로 강제 지정 (가장 원시적인 방법)
        try:
            df = pd.DataFrame({
                'Close': data.iloc[:, 0], 
                'Volume': data.iloc[:, 4 if data.shape[1] > 4 else -1]
            }, index=data.index)
        except:
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
            
            # AI 매수 로직
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
            st.metric(a['n'], f"{final:,.0f}원", f"{((final/a['b'])-1)*100:.2f}%")
            st.line_chart(df['Close'])
        else:
            st.error(f"{a['n']} 데이터를 찾을 수 없음")

st.divider()
st.header(f"💰 전체 합산 자산: {total_val:,.0f}원")
