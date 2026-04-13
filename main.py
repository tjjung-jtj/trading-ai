import streamlit as st
import yfinance as yf
import pandas as pd
import datetime

# 1. 앱 설정 및 자산 초기화
st.set_page_config(page_title="AI 통합 자동투자", layout="wide")

if 'balance_coin' not in st.session_state:
    st.session_state.balance_coin = 1000000  # 코인 100만
    st.session_state.balance_us = 500000     # 미장 50만
    st.session_state.balance_kr = 500000     # 국장 50만
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = []

st.title("🤖 AI 통합 자산관리 시스템")
st.sidebar.header("💰 실시간 잔고")
st.sidebar.write(f"🪙 코인 잔고: {st.session_state.balance_coin:,.0f}원")
st.sidebar.write(f"🇺🇸 미장 잔고: ${st.session_state.balance_us/1350:,.2f} (약 {st.session_state.balance_us:,.0f}원)")
st.sidebar.write(f"🇰🇷 국장 잔고: {st.session_state.balance_kr:,.0f}원")

# 2. 데이터 클리닝 함수
def get_data(ticker):
    try:
        df = yf.download(ticker, period="1mo", interval="1d", progress=False)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df.dropna()
    except:
        return None

# 3. 자동매매 핵심 로직
def run_auto_trade():
    # 자산별 스캔 리스트
    targets = {
        'coin': ['BTC-KRW', 'ETH-KRW', 'SOL-KRW', 'XRP-KRW'],
        'us': ['NVDA', 'TSLA', 'AAPL', 'MSFT'],
        'kr': ['005930.KS', '000660.KS', '035420.KS', '005380.KS']
    }
    
    # [매도 체크] 기존 보유 종목 수익률 확인 (익절 +5%, 손절 -3%)
    new_portfolio = []
    for stock in st.session_state.portfolio:
        df = get_data(stock['ticker'])
        if df is not None:
            curr_p = float(df['Close'].iloc[-1])
            profit = (curr_p - stock['buy_p']) / stock['buy_p']
            
            if profit >= 0.05 or profit <= -0.03:
                # 매도 처리 (잔고 복구)
                sell_val = curr_p * stock['qty']
                if stock['cat'] == 'coin': st.session_state.balance_coin += sell_val
                elif stock['cat'] == 'us': st.session_state.balance_us += sell_val
                else: st.session_state.balance_kr += sell_val
                st.info(f"✅ 매도 완료: {stock['ticker']} (수익률: {profit*100:.2f}%)")
            else:
                new_portfolio.append(stock)
    st.session_state.portfolio = new_portfolio

    # [매수 체크] 비어있는 자산군에 새로운 종목 채우기
    for cat, tickers in targets.items():
        # 각 자산군당 최대 2종목씩 보유하도록 설정
        current_cat_count = len([s for s in st.session_state.portfolio if s['cat'] == cat])
        if current_cat_count < 2:
            for t in tickers:
                if any(s['ticker'] == t for s in st.session_state.portfolio): continue # 이미 보유중 제외
                
                df = get_data(t)
                if df is not None:
                    curr_p = float(df['Close'].iloc[-1])
                    avg_v = float(df['Volume'].iloc[-5:-1].mean())
                    curr_v = float(df['Volume'].iloc[-1])
                    
                    # AI 매수 조건: 거래량 2배 폭증 시
                    if curr_v > avg_v * 2:
                        buy_limit = 500000 if cat == 'coin' else 250000 # 자산별 1/2씩 투자
                        balance = getattr(st.session_state, f'balance_{cat}')
                        
                        if balance >= buy_limit:
                            qty = buy_limit / curr_p
                            st.session_state.portfolio.append({
                                'ticker': t, 'buy_p': curr_p, 'qty': qty, 'cat': cat
                            })
                            setattr(st.session_state, f'balance_{cat}', balance - buy_limit)
                            st.success(f"🚀 AI 매수: {t} ({cat.upper()} 섹터)")
                            break

# 4. 화면 구성
tab1, tab2 = st.tabs(["📊 실시간 투자 현황", "⚙️ 시스템 설정"])

with tab1:
    st.subheader("현재 포트폴리오")
    if not st.session_state.portfolio:
        st.write("현재 AI가 시장을 관망 중입니다.")
    else:
        for s in st.session_state.portfolio:
            df = get_data(s['ticker'])
            if df is not None:
                curr_p = float(df['Close'].iloc[-1])
                profit = (curr_p - s['buy_p']) / s['buy_p'] * 100
                st.write(f"**[{s['cat'].upper()}] {s['ticker']}** | 매수가: {s['buy_p']:,.0f} | 현재가: {curr_p:,.0f} | 수익률: {profit:.2f}%")

with tab2:
    st.subheader("자동투자 제어판")
    if st.button("🚀 지금 즉시 AI 자동매매 실행"):
        run_auto_trade()
        st.rerun()
    
    if st.button("🔄 초기화 (200만원 재시작)"):
        st.session_state.balance_coin = 1000000
        st.session_state.balance_us = 500000
        st.session_state.balance_kr = 500000
        st.session_state.portfolio = []
        st.rerun()
