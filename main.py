import streamlit as st
import yfinance as yf
import pandas as pd
from streamlit_autorefresh import st_autorefresh
import json
import os
import datetime
import time

# 1. 페이지 설정 및 자동 새로고침 (60초마다 실행)
st.set_page_config(page_title="AI 24/7 Hybrid Trader", layout="wide")
st_autorefresh(interval=60000, key="fizzbuzzcounter")

# 2. 데이터 영구 저장/불러오기 로직 (Render 서버 리셋 대비)
DB_FILE = "trading_db.json"

def save_db():
    data = {
        "balance_coin": st.session_state.balance_coin,
        "balance_us": st.session_state.balance_us,
        "balance_kr": st.session_state.balance_kr,
        "portfolio": st.session_state.portfolio,
        "trade_log": st.session_state.trade_log
    }
    with open(DB_FILE, "w") as f:
        json.dump(data, f)

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                return json.load(f)
        except:
            return None
    return None

# 세션 초기화 및 복구
if 'initialized' not in st.session_state:
    saved = load_db()
    if saved:
        st.session_state.update(saved)
    else:
        st.session_state.balance_coin = 1000000
        st.session_state.balance_us = 500000
        st.session_state.balance_kr = 500000
        st.session_state.portfolio = []
        st.session_state.trade_log = []
    st.session_state.initialized = True

# 3. 분석 엔진
def get_analysis(ticker):
    try:
        df = yf.download(ticker, period="1mo", interval="1d", progress=False)
        if df.empty or len(df) < 5: return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        curr_p = float(df['Close'].iloc[-1])
        prev_p = float(df['Close'].iloc[-2])
        high_1m = float(df['High'].max())
        
        vol_ratio = float(df['Volume'].iloc[-1]) / float(df['Volume'].iloc[:-1].mean())
        drop_rate = (curr_p - high_1m) / high_1m * 100
        change = (curr_p - prev_p) / prev_p * 100
        
        return {'p': curr_p, 'vol': vol_ratio, 'drop': drop_rate, 'change': change}
    except:
        return None

# 4. 자동 매도 로직 (익절/손절)
def auto_sell():
    new_portfolio = []
    changed = False
    for s in st.session_state.portfolio:
        res = get_analysis(s['ticker'])
        if res:
            profit = (res['p'] - s['buy_p']) / s['buy_p']
            # 익절 +5% 또는 손절 -3%
            if profit >= 0.05 or profit <= -0.03:
                val = res['p'] * s['qty']
                st.session_state[f"balance_{s['cat']}"] += val
                action = "익절" if profit > 0 else "손절"
                st.session_state.trade_log.append(f"[{datetime.datetime.now().strftime('%m/%d %H:%M')}] {s['ticker']} {action} ({profit*100:.2f}%)")
                changed = True
                continue
        new_portfolio.append(s)
    
    if changed:
        st.session_state.portfolio = new_portfolio
        save_db()

# 5. 메인 UI
st.title("🤖 AI 24/7 하이브리드 자동매매 시스템")
st.write(f"🕒 마지막 감시: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# 사이드바 잔고 현황
st.sidebar.header("💰 실시간 자산")
st.sidebar.write(f"🪙 코인: {st.session_state.balance_coin:,.0f}원")
st.sidebar.write(f"🇺🇸 미장: {st.session_state.balance_us:,.0f}원")
st.sidebar.write(f"🇰🇷 국장: {st.session_state.balance_kr:,.0f}원")

tab1, tab2, tab3 = st.tabs(["🎯 자동매매 제어", "💼 포트폴리오", "📜 거래 로그"])

with tab1:
    if st.button("🚀 AI 자동매매 엔진 가동"):
        auto_sell() # 매도 먼저 체크
        
        targets = {
            'coin': ['BTC-KRW', 'ETH-KRW', 'SOL-KRW', 'DOGE-KRW'],
            'us': ['NVDA', 'TSLA', 'PLTR', 'SOXL', 'TQQQ'],
            'kr': ['005930.KS', '000660.KS', '012450.KS', '086520.KQ']
        }
        
        for cat, tickers in targets.items():
            if len([p for p in st.session_state.portfolio if p['cat'] == cat]) >= 2: continue
            
            for t in tickers:
                if any(p['ticker'] == t for p in st.session_state.portfolio): continue
                res = get_analysis(t)
                if res:
                    # 조건: 거래량 1.5배(이슈) 또는 낙폭과대 후 반등
                    if res['vol'] > 1.5 or (res['drop'] < -15 and res['change'] > 1.0):
                        buy_limit = 500000 if cat == 'coin' else 250000
                        if st.session_state[f"balance_{cat}"] >= buy_limit:
                            st.session_state.portfolio.append({
                                'ticker': t, 'buy_p': res['p'], 'qty': buy_limit/res['p'], 'cat': cat
                            })
                            st.session_state[f"balance_{cat}"] -= buy_limit
                            st.session_state.trade_log.append(f"[{datetime.datetime.now().strftime('%m/%d %H:%M')}] {t} 매수 완료")
                            save_db()
                            st.success(f"🔥 {t} 신규 매수!")
        st.rerun()

with tab2:
    if not st.session_state.portfolio:
        st.write("현재 보유 중인 종목이 없습니다.")
    else:
        for s in st.session_state.portfolio:
            res = get_analysis(s['ticker'])
            if res:
                profit = (res['p'] - s['buy_p']) / s['buy_p'] * 100
                st.write(f"**{s['ticker']}** | 수익률: `{profit:+.2f}%` | 평가금: {res['p']*s['qty']:,.0f}원")

with tab3:
    for log in reversed(st.session_state.trade_log):
        st.write(log)

if st.sidebar.button("🔄 데이터 초기화"):
    if os.path.exists(DB_FILE): os.remove(DB_FILE)
    st.session_state.clear()
    st.rerun()
