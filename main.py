import streamlit as st
import yfinance as yf
import pandas as pd
import time

# 1. 앱 설정
st.set_page_config(page_title="AI Live Scanner", layout="wide")

if 'balance_coin' not in st.session_state:
    st.session_state.balance_coin, st.session_state.balance_us, st.session_state.balance_kr = 1000000, 500000, 500000
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = []

st.title("🔥 AI 공격형 스캐너 (실시간 생중계 모드)")

# 2. 분석 함수
def get_analysis(ticker):
    try:
        df = yf.download(ticker, period="1mo", interval="1d", progress=False)
        if df.empty or len(df) < 5: return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        curr_p = float(df['Close'].iloc[-1])
        high_p = float(df['High'].max())
        drop_rate = (curr_p - high_p) / high_p * 100
        vol_ratio = float(df['Volume'].iloc[-1]) / float(df['Volume'].iloc[:-1].mean())
        
        return {'p': curr_p, 'drop': drop_rate, 'vol': vol_ratio}
    except:
        return None

# 3. 메인 로직
tab1, tab2 = st.tabs(["📺 실시간 스캔 방송", "💼 현재 포트폴리오"])

with tab1:
    if st.button("🎯 시장 스캔 및 자동매매 시작"):
        targets = {
            'coin': ['SOL-KRW', 'DOGE-KRW', 'PEPE-KRW', 'SHIB-KRW', 'XRP-KRW'],
            'us': ['SOXL', 'TQQQ', 'MSTR', 'COIN', 'TSLA', 'NVDA'],
            'kr': ['086520.KQ', '277810.KQ', '465320.KS', '066570.KS', '003670.KS']
        }
        
        st.subheader("📡 AI 실시간 분석 로그")
        log_container = st.container()
        
        for cat, tickers in targets.items():
            for t in tickers:
                with log_container:
                    # 이미 보유 중인 종목은 패스
                    if any(s['ticker'] == t for s in st.session_state.portfolio):
                        st.write(f"ℹ️ {t}: 이미 보유 중입니다.")
                        continue
                    
                    res = get_analysis(t)
                    if res:
                        # 분석 수치 생중계
                        status = "✅ 조건 부합!" if (res['drop'] < -15 and res['vol'] > 1.5) else "❌ 조건 미달"
                        st.write(f"🔍 **{t}** 분석: 낙폭 `{res['drop']:.1f}%` | 거래량 `{res['vol']:.2f}배` -> {status}")
                        
                        # 실제 매수 실행
                        if res['drop'] < -15 and res['vol'] > 1.5:
                            buy_limit = 500000 if cat == 'coin' else 250000
                            balance = getattr(st.session_state, f'balance_{cat}')
                            
                            if balance >= buy_limit:
                                st.session_state.portfolio.append({
                                    'ticker': t, 'buy_p': res['p'], 'qty': buy_limit/res['p'], 'cat': cat
                                })
                                setattr(st.session_state, f'balance_{cat}', balance - buy_limit)
                                st.success(f"🚀 {t} 매수 체결!")
                    time.sleep(0.1) # 생중계 느낌을 위해 살짝 딜레이
        st.success("스캔 완료!")

with tab2:
    if not st.session_state.portfolio:
        st.write("보유 종목이 없습니다.")
    else:
        for s in st.session_state.portfolio:
            st.write(f"**[{s['cat'].upper()}] {s['ticker']}** | 매수가: {s['buy_p']:,.2f}")

if st.sidebar.button("🔄 원금 리셋"):
    st.session_state.clear()
    st.rerun()
