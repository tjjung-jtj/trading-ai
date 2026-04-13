import streamlit as st
import yfinance as yf
import pandas as pd
import time

# 1. 앱 설정
st.set_page_config(page_title="News-Based AI Trader", layout="wide")

if 'balance_coin' not in st.session_state:
    st.session_state.balance_coin, st.session_state.balance_us, st.session_state.balance_kr = 1000000, 500000, 500000
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = []

st.title("🗞️ 뉴스 & 이슈 대응 AI 자동매매")
st.caption("전쟁, AI, 빅테크 등 실시간 수급이 몰리는 테마 종목을 분석합니다.")

# 2. 테마별 종목 세팅 (전쟁, AI, 코인)
THEMES = {
    'AI_TECH': ['NVDA', 'PLTR', 'MSFT', '000660.KS', '035420.KS'],
    'WAR_ENERGY': ['LMT', 'XOM', '012450.KS', '001060.KS'], # 방산(한화에어로, 중외), 에너지
    'COIN_SAFE': ['BTC-KRW', 'ETH-KRW', 'SOL-KRW', 'XRP-KRW']
}

# 3. 뉴스 민감도 분석 (거래량 + 변동성 결합)
def get_theme_analysis(ticker):
    try:
        df = yf.download(ticker, period="5d", interval="1d", progress=False)
        if df.empty or len(df) < 2: return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        curr_p = float(df['Close'].iloc[-1])
        prev_p = float(df['Close'].iloc[-2])
        # 뉴스 민감도: 평소보다 거래량이 1.3배 이상이면서 가격 변동이 2% 이상인 경우
        vol_ratio = df['Volume'].iloc[-1] / df['Volume'].iloc[:-1].mean()
        price_change = abs((curr_p - prev_p) / prev_p * 100)
        
        return {'p': curr_p, 'vol': vol_ratio, 'change': price_change, 'raw': df}
    except:
        return None

# 4. 메인 화면 로직
tab1, tab2 = st.tabs(["📡 실시간 테마 스캔", "💼 통합 포트폴리오"])

with tab1:
    if st.button("🔥 테마별 뉴스 수급 분석 시작"):
        st.subheader("🕵️ AI가 현재 이슈 종목을 찾는 중...")
        for theme_name, tickers in THEMES.items():
            st.write(f"--- **{theme_name} 관련주 분석** ---")
            for t in tickers:
                if any(s['ticker'] == t for s in st.session_state.portfolio): continue
                
                res = get_theme_analysis(t)
                if res:
                    # 조건: 거래량이 1.3배 이상 (이슈 발생) & 변동성이 1.5% 이상 (수급 집중)
                    is_hot = res['vol'] > 1.3 and res['change'] > 1.5
                    status = "✅ 수급 포착 (뉴스 의심)" if is_hot else "💤 조용함"
                    st.write(f"🔍 {t}: 거래량 `{res['vol']:.2f}배` | 변동 `{res['change']:.1f}%` -> {status}")
                    
                    if is_hot:
                        # 자산 배분 로직
                        cat = 'coin' if 'KRW' in t else ('us' if t[0].isalpha() else 'kr')
                        buy_limit = 500000 if cat == 'coin' else 250000
                        
                        st.session_state.portfolio.append({
                            'ticker': t, 'buy_p': res['p'], 'qty': buy_limit/res['p'], 'cat': cat, 'theme': theme_name
                        })
                        st.success(f"🚀 {t} ({theme_name}) 매수 완료!")
                time.sleep(0.1)
        st.rerun()

with tab2:
    if not st.session_state.portfolio:
        st.info("보유 종목이 없습니다.")
    else:
        total_eval = 0
        for s in st.session_state.portfolio:
            res = get_theme_analysis(s['ticker'])
            if res:
                profit = (res['p'] - s['buy_p']) / s['buy_p'] * 100
                total_eval += (res['p'] * s['qty'])
                st.write(f"**[{s['theme']}] {s['ticker']}** | 수익률: `{profit:+.2f}%` | 현재가: {res['p']:,.0f}")
