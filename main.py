import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# 1. 페이지 설정
st.set_page_config(page_title="실시간 싸싸의 주식 앱", layout="wide", initial_sidebar_state="collapsed")

# 2. 프리미엄 Light Mode 디자인 (CSS)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #fcfcfc; color: #333333; }
    
    /* 카드 디자인 */
    .market-card {
        background: #ffffff; padding: 15px; border-radius: 12px;
        border: 1px solid #e9ecef; margin-bottom: 5px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .market-name { font-size: 0.9rem; font-weight: 700; color: #212529; margin-bottom: 5px; }
    .market-price { font-size: 1.4rem; font-weight: 700; color: #000000; }
    .price-up { color: #10b981; } .price-down { color: #ef4444; }
    
    /* 탭 디자인 */
    .stTabs [data-baseweb="tab-list"] { background-color: #ffffff; border-radius: 10px; padding: 5px; border: 1px solid #e9ecef; }
    .stTabs [data-baseweb="tab"] { color: #6c757d !important; font-weight: 600 !important; }
    .stTabs [data-baseweb="tab"][aria-selected="true"] { background-color: #3b82f6 !important; border-radius: 8px !important; color: #ffffff !important; }
    
    /* 차트 상단 간격 조절 */
    .element-container { margin-top: -5px !important; }
    </style>
    """, unsafe_allow_html=True)

# 3. 데이터 로드 및 한글 이름 매핑
STOCK_NAMES = {
    "005930.KS": "삼성전자",
    "035720.KS": "카카오",
    "323410.KS": "카카오뱅크",
    "033050.KQ": "제이엠아이",
    "000660.KS": "SK하이닉스"
}

@st.cache_data(ttl=60)
def get_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="1y", interval="1d")
        if df.empty: return None
        df['MA5'] = df['Close'].rolling(window=5).mean()
        df['MA20'] = df['Close'].rolling(window=20).mean()
        df['MA60'] = df['Close'].rolling(window=60).mean()
        return {"data": df, "ticker": ticker}
    except:
        return None

# 차트 그리기 함수 (가로가 너무 길지 않게 높이 조절)
def create_stock_chart(df, ticker_name):
    plot_df = df.tail(60)
    fig = go.Figure(data=[go.Candlestick(
        x=plot_df.index, open=plot_df['Open'], high=plot_df['High'],
        low=plot_df['Low'], close=plot_df['Close'], name="주가",
        increasing_line_color='#10b981', decreasing_line_color='#ef4444'
    )])
    
    # 이동평균선 (흰색 배경 최적화 색상)
    fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df['MA5'], line=dict(color='#BF9B30', width=1.2), name="5일선"))
    fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df['MA20'], line=dict(color='#8A2BE2', width=1.2), name="20일선"))
    fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df['MA60'], line=dict(color='#1E90FF', width=1.2), name="60일선"))
    
    fig.update_layout(
        template="plotly_white", plot_bgcolor='#ffffff', paper_bgcolor='#ffffff',
        height=350, # 아이폰에서 적절한 세로 길이 (가로로 너무 길어 보이지 않게 조절)
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(rangeslider_visible=False, gridcolor='#f1f3f5'),
        yaxis=dict(gridcolor='#f1f3f5', side="right"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=10))
    )
    return fig

# --- 메인 헤더 ---
st.title("🚀 실시간 싸싸의 주식 앱")
st.caption(f"최종 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# 자동 새로고침 (60초)
st_autorefresh(interval=60000, key="data_refresh")

# 4. 탭 구성 (분석 탭 삭제)
tab1, tab2 = st.tabs(["📌 나의 종목 현황", "📊 시장 대시보드"])

# --- [탭 1: 나의 종목 현황] ---
with tab1:
    my_tickers = list(STOCK_NAMES.keys())
    
    for ticker in my_tickers:
        stock_info = get_data(ticker)
        if stock_info:
            df = stock_info['data']
            curr_price = df['Close'].iloc[-1]
            prev_price = df['Close'].iloc[-2]
            pct = ((curr_price - prev_price) / prev_price) * 100
            
            color = "price-up" if pct >= 0 else "price-down"
            sign = "+" if pct >= 0 else ""
            kor_name = STOCK_NAMES[ticker]
            
            # 상단 요약 카드
            st.markdown(f"""
                <div class="market-card">
                    <div class="market-name">{kor_name} ({ticker})</div>
                    <div class="market-price">{curr_price:,.0f}원 <span class="{color}" style="font-size: 0.9rem; margin-left:10px;">{sign}{pct:.2f}%</span></div>
                </div>
            """, unsafe_allow_html=True)
            
            # 차트 출력 (높이 조절됨)
            st.plotly_chart(create_stock_chart(df, kor_name), use_container_width=True, config={'displayModeBar': False})
            st.write("") # 간격

# --- [탭 2: 시장 대시보드] ---
with tab2:
    market_cats = {
        "글로벌 지수": ["^KS11", "^KQ11", "^NDX", "USDKRW=X"],
        "원자재 & 코인": ["CL=F", "GC=F", "BTC-USD"]
    }
    for cat, tickers in market_cats.items():
        st.subheader(cat)
        cols = st.columns(len(tickers))
        for i, t in enumerate(tickers):
            s = yf.Ticker(t).history(period="2d")
            if not s.empty:
                curr = s['Close'].iloc[-1]
                prev = s['Close'].iloc[-2]
                pct = ((curr - prev) / prev) * 100
                color = "price-up" if pct >= 0 else "price-down"
                with cols[i]:
                    st.markdown(f"""
                        <div class="market-card">
                            <div class="market-name">{t}</div>
                            <div class="market-price" style="font-size:1.1rem;">{curr:,.2f}</div>
                            <div class="{color}" style="font-weight:600; font-size:0.8rem;">{pct:+.2f}%</div>
                        </div>
                    """, unsafe_allow_html=True)