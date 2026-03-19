import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# 1. 페이지 기본 설정
st.set_page_config(page_title="실시간 싸싸의 주식 앱", layout="wide", initial_sidebar_state="collapsed")

# 2. 롱숏나우 스타일 프리미엄 디자인 (CSS)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #0f1116; color: #ffffff; }
    
    .market-card {
        background: #1a1d24; padding: 20px; border-radius: 16px;
        border: 1px solid #2d3139; margin-bottom: 20px;
    }
    .market-name { font-size: 0.9rem; font-weight: 600; color: #9ca3af; margin-bottom: 8px; }
    .market-price { font-size: 1.5rem; font-weight: 700; margin: 5px 0; }
    .price-up { color: #10b981; } .price-down { color: #ef4444; }
    
    .stTabs [data-baseweb="tab-list"] { background-color: #1a1d24; border-radius: 10px; padding: 5px; }
    .stTabs [data-baseweb="tab"] { color: #ffffff !important; }
    .stTabs [data-baseweb="tab"][aria-selected="true"] { background-color: #3b82f6 !important; border-radius: 8px !important; }
    </style>
    """, unsafe_allow_html=True)

# 3. 데이터 로드 함수
@st.cache_data(ttl=60)
def get_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="2d")
        if len(hist) < 2: return None
        curr = hist['Close'].iloc[-1]
        prev = hist['Close'].iloc[-2]
        diff = curr - prev
        pct = (diff / prev) * 100
        name = stock.info.get('shortName', ticker)
        return {"name": name, "price": curr, "diff": diff, "pct": pct, "ticker": ticker}
    except:
        return None

# --- 사이드바: 자산 설정 ---
with st.sidebar:
    st.header("💰 나의 자산 설정")
    samsung_qty = st.number_input("삼성전자 수량", value=90)
    hynix_qty = st.number_input("SK하이닉스 수량", value=20)
    st.divider()
    st.caption("실시간 싸싸의 주식 앱 v1.1")

# --- 메인 헤더 ---
st.title("🚀 실시간 싸싸의 주식 앱")
st.caption(f"최종 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# 자동 새로고침 (60초)
st_autorefresh(interval=60000, key="data_refresh")

# 4. 탭 구성 (종목 현황 탭을 첫 번째로 배치)
tab1, tab2, tab3 = st.tabs(["📌 나의 종목 현황", "📊 시장 대시보드", "📈 실시간 차트 분석"])

# --- [탭 1: 나의 종목 현황] ---
with tab1:
    st.subheader("관심 종목 실시간 주가")
    # 요청하신 종목 리스트 (삼성전자, 카카오, 카카오뱅크, 제이엠티, SK하이닉스)
    my_stocks = ["005930.KS", "035720.KS", "323410.KS", "090470.KQ", "000660.KS"]
    
    cols = st.columns(len(my_stocks))
    for i, t in enumerate(my_stocks):
        data = get_data(t)
        if data:
            with cols[i]:
                color = "price-up" if data['pct'] >= 0 else "price-down"
                sign = "+" if data['pct'] >= 0 else ""
                st.markdown(f"""
                    <div class="market-card">
                        <div class="market-name">{data['name']}</div>
                        <div class="market-price">{data['price']:,.0f}원</div>
                        <div class="{color}">{sign}{data['pct']:.2f}%</div>
                    </div>
                """, unsafe_allow_html=True)

# --- [탭 2: 시장 대시보드] ---
with tab2:
    market_list = {
        "글로벌 지수": ["^KS11", "^KQ11", "^NDX", "USDKRW=X"],
        "가상자산": ["BTC-USD", "ETH-USD", "DOGE-USD"]
    }
    for category, tickers in market_list.items():
        st.subheader(category)
        cols = st.columns(4)
        for i, t in enumerate(tickers):
            data = get_data(t)
            if data:
                with cols[i % 4]:
                    color = "price-up" if data['pct'] >= 0 else "price-down"
                    st.markdown(f"""
                        <div class="market-card">
                            <div class="market-name">{data['name']}</div>
                            <div class="market-price">{data['price']:,.2f}</div>
                            <div class="{color}">{data['pct']:.2f}%</div>
                        </div>
                    """, unsafe_allow_html=True)

# --- [탭 3: 실시간 차트 분석 (이동평균선 추가)] ---
with tab3:
    st.subheader("기술적 지표 분석 (MA 5/20/60)")
    selected = st.selectbox("분석 종목 선택", ["005930.KS", "035720.KS", "323410.KS", "090470.KQ", "000660.KS", "BTC-USD"])
    
    # 충분한 데이터를 가져오기 위해 1년치 데이터 로드
    df = yf.Ticker(selected).history(period="1y", interval="1d")
    
    # 이동평균선 계산
    df['MA5'] = df['Close'].rolling(window=5).mean()
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA60'] = df['Close'].rolling(window=60).mean()
    
    # 최근 100일 데이터만 차트에 표시
    plot_df = df.tail(100)
    
    fig = go.Figure()
    # 캔들스틱 차트
    fig.add_trace(go.Candlestick(
        x=plot_df.index, open=plot_df['Open'], high=plot_df['High'],
        low=plot_df['Low'], close=plot_df['Close'], name="Price"
    ))
    
    # 이동평균선 라인 추가
    fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df['MA5'], line=dict(color='#FFD700', width=1.5), name="MA5"))
    fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df['MA20'], line=dict(color='#FF00FF', width=1.5), name="MA20"))
    fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df['MA60'], line=dict(color='#00BFFF', width=1.5), name="MA60"))
    
    fig.update_layout(
        template="plotly_dark", plot_bgcolor='#0f1116', paper_bgcolor='#0f1116',
        xaxis_rangeslider_visible=False, height=500
    )
    st.plotly_chart(fig, use_container_width=True)