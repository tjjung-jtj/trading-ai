import streamlit as st
import yfinance as yf
import pandas as pd
import time

# 1. 앱 설정 및 자산 초기화
st.set_page_config(page_title="AI Hybrid Trader", layout="wide")

if 'balance_coin' not in st.session_state:
    st.session_state.balance_coin, st.session_state.balance_us, st.session_state.balance_kr = 1000000, 500000, 500000
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = []

st.title("🤖 AI 하이브리드 통합 자동매매")
st.caption("기술적 분석(기존) + 뉴스 테마(전쟁/AI)를 결합하여 최적의 종목을 사냥합니다.")

# 2. 통합 분석 리스트 (기존 우량주 + 뉴스 테마주)
ASSET_GROUPS = {
    'COIN': ['BTC-KRW', 'ETH-KRW', 'SOL-KRW', 'DOGE-KRW'],
    'US_TECH': ['NVDA', 'TSLA', 'AAPL', 'PLTR', 'SOXL', 'TQQQ'],
    'KR_MARKET': ['005930.KS', '000660.KS', '005380.KS', '086520.KQ', '012450.KS'], # 삼성, 하이닉스, 현대차, 에코프로비엠, 한화에어로
}

# 3. 통합 분석 엔진
def get_hybrid_analysis(ticker):
    try:
        df = yf.download(ticker, period="1mo", interval="1d", progress=False)
        if df.empty or len(df) < 10: return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        curr_p = float(df['Close'].iloc[-1])
        prev_p = float(df['Close'].iloc[-2])
        high_1m = float(df['High'].max())
        
        # 지표 계산
        vol_ratio = df['Volume'].iloc[-1] / df['Volume'].iloc[:-1].mean()
        drop_rate = (curr_p - high_1m) / high_1m * 100
        change = (curr_p - prev_p) / prev_p * 100
        
        return {'p': curr_p, 'vol': vol_ratio, 'drop': drop_rate, 'change': change}
    except:
        return None

# 4. 메인 화면
st.sidebar.header("💰 실시간 잔고")
st.sidebar.info(f"🪙 코인: {st.session_state.balance_coin:,.0f}원\n\n🇺🇸 미장: {st.session_state.balance_us:,.0f}원\n\n🇰🇷 국장: {st.session_state.balance_kr:,.0f}원")

tab1, tab2 = st.tabs(["🎯 통합 시장 스캔", "💼 내 포트폴리오"])

with tab1:
    if st.button("🚀 AI 하이브리드 매매 가동"):
        st.subheader("📡 전 종목 실시간 수색 로그")
        for cat, tickers in ASSET_GROUPS.items():
            current_count = len([s for s in st.session_state.portfolio if s['cat'] == cat.lower()])
            
            for t in tickers:
                if current_count >= 2: break # 섹터당 2개 유지
                if any(s['ticker'] == t for s in st.session_state.portfolio): continue
                
                res = get_hybrid_analysis(t)
                if res:
                    # [매수 판정 로직]
                    # 1. 뉴스/이슈형: 거래량이 1.5배 이상 터진 경우
                    # 2. 기술적 반등형: 낙폭이 -15% 이상인데 오늘 반등(+1%) 하는 경우
                    is_news_hot = res['vol'] > 1.5
                    is_bottom_rebound = res['drop'] < -15 and res['change'] > 1.0
                    
                    reason = ""
                    if is_news_hot: reason = "🔥 수급 포착 (뉴스/이슈)"
                    elif is_bottom_rebound: reason = "💎 바닥 반등 (기술적 분석)"
                    
                    if reason:
                        # 매수 실행
                        cat_key = cat.lower()
                        if cat_key == 'us_tech': cat_key = 'us'
                        elif cat_key == 'kr_market': cat_key = 'kr'
                        
                        buy_limit = 500000 if cat_key == 'coin' else 250000
                        balance = getattr(st.session_state, f'balance_{cat_key}')
                        
                        if balance >= buy_limit:
                            st.session_state.portfolio.append({
                                'ticker': t, 'buy_p': res['p'], 'qty': buy_limit/res['p'], 
                                'cat': cat_key, 'reason': reason
                            })
                            setattr(st.session_state, f'balance_{cat_key}', balance - buy_limit)
                            st.success(f"🚀 {t} 매수 완료! | 사유: {reason}")
                            current_count += 1
                    else:
                        st.write(f"🔍 {t}: 관망 중 (특이사항 없음)")
                time.sleep(0.05)
        st.rerun()

with tab2:
    if not st.session_state.portfolio:
        st.info("현재 보유 종목이 없습니다.")
    else:
        for i, s in enumerate(st.session_state.portfolio):
            res = get_hybrid_analysis(s['ticker'])
            if res:
                profit = (res['p'] - s['buy_p']) / s['buy_p'] * 100
                st.write(f"**[{s['cat'].upper()}] {s['ticker']}** | {s['reason']}")
                st.write(f"수익률: `{profit:+.2f}%` | 평가금: {(res['p']*s['qty']):,.0f}원")
                if st.button("청산", key=f"sell_{i}"):
                    val = res['p'] * s['qty']
                    setattr(st.session_state, f"balance_{s['cat']}", getattr(st.session_state, f"balance_{s['cat']}") + val)
                    st.session_state.portfolio.pop(i)
                    st.rerun()
