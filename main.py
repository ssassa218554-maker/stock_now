import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. 페이지 설정
st.set_page_config(page_title="실시간 싸싸의 주식 앱", layout="wide", initial_sidebar_state="collapsed")

# 2. 디자인 설정 (흰색 배경 유지)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #fcfcfc; color: #333333; }
    .market-card {
        background: #ffffff; padding: 15px; border-radius: 12px;
        border: 1px solid #e9ecef; margin-bottom: 5px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .market-name { font-size: 0.9rem; font-weight: 700; color: #212529; margin-bottom: 5px; }
    .market-price { font-size: 1.4rem; font-weight: 700; color: #000000; }
    .price-up { color: #10b981; } .price-down { color: #ef4444; }
    .stTabs [data-baseweb="tab-list"] { background-color: #ffffff; border-radius: 10px; padding: 5px; border: 1px solid #e9ecef; }
    .stTabs [data-baseweb="tab"] { color: #6c757d !important; font-weight: 600 !important; }
    .stTabs [data-baseweb="tab"][aria-selected="true"] { background-color: #3b82f6 !important; border-radius: 8px !important; color: #ffffff !important; }
    </style>
    """, unsafe_allow_html=True)

# 3. 종목 및 이름 매핑 (엘지전자 포함)
STOCK_NAMES = {
    "005930.KS": "삼성전자",
    "035720.KS": "카카오",
    "323410.KS": "카카오뱅크",
    "033050.KQ": "제이엠아이",
    "066570.KS": "엘지전자"
}

MARKET_DISPLAY_NAMES = {
    "^KS11": "코스피", "^KQ11": "코스닥", "^NDX": "나스닥 100",
    "USDKRW=X": "원/달러 환율", "CL=F": "WTI 원유", "GC=F": "금 선물", "BTC-USD": "비트코인"
}

@st.cache_data(ttl=30)
def get_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        # [실시간성 강화] 최근 5일 데이터를 1분 단위로 가져와 가장 마지막 가격을 실시간가로 사용
        live_df = stock.history(period="5d", interval="1m")
        # 차트용 1년 데이터
        hist_df = stock.history(period="1y", interval="1d")
        
        if hist_df.empty: return None
        
        # [오류 수정] 가격이 0원인 데이터 제거 (긴 막대기 방지)
        hist_df = hist_df[hist_df['Low'] > 0]
        
        # 최신 가격 결정
        if not live_df.empty:
            curr_price = live_df['Close'].iloc[-1]
            prev_close = stock.history(period="2d")['Close'].iloc[-2]
            pct = ((curr_price - prev_close) / prev_close) * 100
        else:
            curr_price = hist_df['Close'].iloc[-1]
            prev_close = hist_df['Close'].iloc[-2]
            pct = ((curr_price - prev_close) / prev_close) * 100

        hist_df['MA5'] = hist_df['Close'].rolling(window=5).mean()
        hist_df['MA20'] = hist_df['Close'].rolling(window=20).mean()
        hist_df['MA60'] = hist_df['Close'].rolling(window=60).mean()
        
        return {"data": hist_df, "ticker": ticker, "curr_price": curr_price, "pct": pct}
    except:
        return None

def create_stock_chart(df, ticker_name):
    plot_df = df.tail(60)
    fig = go.Figure(data=[go.Candlestick(
        x=plot_df.index, open=plot_df['Open'], high=plot_df['High'],
        low=plot_df['Low'], close=plot_df['Close'], name="주가",
        increasing_line_color='#10b981', decreasing_line_color='#ef4444'
    )])
    fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df['MA5'], line=dict(color='#BF9B30', width=1.2), name="5일선"))
    fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df['MA20'], line=dict(color='#8A2BE2', width=1.2), name="20일선"))
    fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df['MA60'], line=dict(color='#1E90FF', width=1.2), name="60일선"))
    
    fig.update_layout(
        template="plotly_white", plot_bgcolor='#ffffff', paper_bgcolor='#ffffff',
        height=350, margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(rangeslider_visible=False, gridcolor='#f1f3f5', fixedrange=True),
        yaxis=dict(gridcolor='#f1f3f5', side="right", fixedrange=True),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=10)),
        dragmode=False
    )
    return fig

# --- 메인 헤더 ---
st.title("🚀 실시간 싸싸의 주식 앱")
kst_now = datetime.now() + timedelta(hours=9)
st.caption(f"최종 업데이트 (한국 시각): {kst_now.strftime('%Y-%m-%d %H:%M:%S')}")

# 자동 새로고침 (60초)
st_autorefresh(interval=60000, key="data_refresh")

tab1, tab2 = st.tabs(["📌 나의 종목 현황", "📊 글로벌 지수"])

# --- [탭 1: 나의 종목 현황] ---
with tab1:
    for ticker in STOCK_NAMES.keys():
        s_info = get_data(ticker)
        if s_info:
            df = s_info['data']
            curr_price = s_info['curr_price']
            pct = s_info['pct']
            color = "price-up" if pct >= 0 else "price-down"
            kor_name = STOCK_NAMES[ticker]
            
            st.markdown(f"""
                <div class="market-card">
                    <div class="market-name">{kor_name} ({ticker})</div>
                    <div class="market-price">{curr_price:,.0f}원 <span class="{color}" style="font-size: 0.9rem; margin-left:10px;">{pct:+.2f}%</span></div>
                </div>
            """, unsafe_allow_html=True)
            st.plotly_chart(create_stock_chart(df, kor_name), use_container_width=True, config={'displayModeBar': False})

# --- [탭 2: 글로벌 지수] ---
with tab2:
    market_cats = {
        "글로벌 지수": ["^KS11", "^KQ11", "^NDX", "USDKRW=X"],
        "원자재 & 코인": ["CL=F", "GC=F", "BTC-USD"]
    }
    for cat, tickers in market_cats.items():
        st.subheader(cat)
        cols = st.columns(len(tickers))
        for i, t in enumerate(tickers):
            s_data = get_data(t)
            if s_data:
                curr = s_data['curr_price']
                pct = s_data['pct']
                color = "price-up" if pct >= 0 else "price-down"
                display_name = MARKET_DISPLAY_NAMES.get(t, t)
                unit = "원" if "환율" in display_name else ""
                
                with cols[i]:
                    st.markdown(f"""
                        <div class="market-card">
                            <div class="market-name">{display_name}</div>
                            <div class="market-price" style="font-size:1.1rem;">{curr:,.2f}{unit}</div>
                            <div class="{color}" style="font-weight:600; font-size:0.8rem;">{pct:+.2f}%</div>
                        </div>
                    """, unsafe_allow_html=True)