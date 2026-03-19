import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# 1. 페이지 기본 설정 및 앱 이름 변경
st.set_page_config(page_title="실시간 싸싸의 주식 앱", layout="wide", initial_sidebar_state="collapsed")

# 2. 프리미엄 Light Mode 디자인 (CSS) - 흰색 배경 최적화
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    /* 전체 배경 흰색, 글자색 어둡게 */
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #fcfcfc; color: #333333; }
    
    /* 사이드바 연한 회색 */
    section[data-testid="stSidebar"] { background-color: #f8f9fa !important; border-right: 1px solid #e9ecef !important; }
    
    /* 카드 디자인 (흰색 배경, 부드러운 그림자) */
    .market-card {
        background: #ffffff; padding: 15px; border-radius: 12px;
        border: 1px solid #e9ecef; margin-bottom: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .market-name { font-size: 0.85rem; font-weight: 600; color: #6c757d; margin-bottom: 5px; }
    .market-price { font-size: 1.3rem; font-weight: 700; margin: 3px 0; color: #212529; }
    .price-up { color: #10b981; } /* 초록색 (상승) */
    .price-down { color: #ef4444; } /* 빨간색 (하락) */
    
    /* 탭 디자인 (흰색/연한 회색 테마) */
    .stTabs [data-baseweb="tab-list"] { background-color: #ffffff; border-radius: 10px; padding: 5px; border: 1px solid #e9ecef; }
    .stTabs [data-baseweb="tab"] { color: #6c757d !important; font-weight: 600 !important; }
    .stTabs [data-baseweb="tab"][aria-selected="true"] { background-color: #3b82f6 !important; border-radius: 8px !important; color: #ffffff !important; }
    
    /* 메트릭 색상 보정 */
    [data-testid="stMetricValue"] { color: #212529 !important; }
    
    /* 차트 상단 마진 줄이기 */
    .element-container { margin-top: -10px !important; }
    </style>
    """, unsafe_allow_html=True)

# 3. 데이터 로드 함수 (캐싱 사용)
@st.cache_data(ttl=60)
def get_data(ticker, period="1y", interval="1d"):
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period=period, interval=interval)
        if df.empty: return None
        
        # 이동평균선 계산
        df['MA5'] = df['Close'].rolling(window=5).mean()
        df['MA20'] = df['Close'].rolling(window=20).mean()
        df['MA60'] = df['Close'].rolling(window=60).mean()
        
        return {"data": df, "name": stock.info.get('shortName', ticker), "ticker": ticker, "currency": stock.info.get('currency', 'KRW')}
    except:
        return None

# 종목별 캔들 차트 + 이동평균선 그리기 함수 (흰색 배경 최적화)
def create_stock_chart(df, ticker_name, currency):
    # 최근 60일 데이터만 차트에 표시
    plot_df = df.tail(60)
    
    # 캔들스틱 차트
    fig = go.Figure(data=[go.Candlestick(
        x=plot_df.index, open=plot_df['Open'], high=plot_df['High'],
        low=plot_df['Low'], close=plot_df['Close'], name="Price",
        increasing_line_color='#10b981', decreasing_line_color='#ef4444' # 선 색상 선명하게
    )])
    
    # 이동평균선 라인 추가 (흰색 배경에 맞게 색상 보정 - 더 진하게)
    fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df['MA5'], line=dict(color='#BF9B30', width=1.5), name="MA5")) # 진한 노랑
    fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df['MA20'], line=dict(color='#8A2BE2', width=1.5), name="MA20")) # 진한 퍼플
    fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df['MA60'], line=dict(color='#1E90FF', width=1.5), name="MA60")) # 진한 블루
    
    # 통화 기호 설정
    currency_symbol = currency
    if currency == "KRW": currency_symbol = "₩"
    elif currency == "USD": currency_symbol = "$"
    
    # 차트 레이아웃 설정 (흰색 테마)
    fig.update_layout(
        title=dict(text=f"<b>{ticker_name}</b> 실시간 차트 (MA 5/20/60)", font=dict(size=16, color="#000000")),
        yaxis=dict(title=dict(text=f"가격 ({currency_symbol})", font=dict(size=12, color="#000000")), tickfont=dict(size=10, color="#000000"), gridcolor='#e9ecef'),
        xaxis=dict(tickfont=dict(size=10, color="#000000"), gridcolor='#e9ecef', rangeslider_visible=False),
        template="plotly_white", plot_bgcolor='#ffffff', paper_bgcolor='#ffffff',
        height=300, # 아이폰 높이
        margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(font=dict(size=10, color="#000000"), orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig

# 대시보드 스파크라인 차트 함수 (탭 2용)
@st.cache_data(ttl=60)
def get_dashboard_data(tickers):
    data = []
    for t in tickers:
        stock = yf.Ticker(t)
        # 최근 2일 데이터 사용
        hist = stock.history(period="2d")
        if len(hist) < 2: continue
        curr = hist['Close'].iloc[-1]
        prev = hist['Close'].iloc[-2]
        diff = curr - prev
        pct = (diff / prev) * 100
        name = stock.info.get('shortName', t)
        
        # 스파크라인 차트 데이터 (최근 1일, 15분 단위)
        chart_data = yf.Ticker(t).history(period="1d", interval="15m")
        
        data.append({
            "ticker": t,
            "name": name,
            "price": curr,
            "diff": diff,
            "pct": pct,
            "chart_data": chart_data
        })
    return data

# 스파크라인 차트 그리기 함수 (탭 2용 - 흰색 배경)
def create_sparkline(hist_data):
    # 가격 등락에 따른 색상 설정
    if not hist_data.empty and hist_data['Close'].iloc[-1] >= hist_data['Close'].iloc[0]:
        color = '#10b981' # 상승 (초록)
    else:
        color = '#ef4444' # 하락 (빨강)
        
    fig = go.Figure(data=go.Scatter(x=hist_data.index, y=hist_data['Close'], mode='lines', line=dict(color=color, width=1.8)))
    fig.update_layout(height=60, margin=dict(l=0, r=0, t=0, b=0),
                      xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                      yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                      plot_bgcolor='#ffffff', paper_bgcolor='#ffffff', template="plotly_white")
    return fig

# --- 사이드바: 자산 및 앱 설정 ---
with st.sidebar:
    st.header("Settings")
    st.write("보유 자산을 설정하세요.")
    samsung_qty = st.number_input("삼성전자 수량", value=90)
    hynix_qty = st.number_input("SK하이닉스 수량", value=20)
    st.divider()
    st.info("Yahoo Finance 데이터를 사용하며, 60초마다 자동 새로고침됩니다.")
    st.caption("실시간 싸싸의 주식 앱 v1.4 (Light Mode)")

# --- 메인 헤더 ---
st.title("🚀 실시간 싸싸의 주식 앱")
st.caption(f"최종 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# 자동 새로고침 설정 (60초마다)
st_autorefresh(interval=60 * 1000, key="data_refresh")

# 4. 탭 구성
tab1, tab2, tab3 = st.tabs(["📌 나의 종목 현황", "📊 시장 대시보드", "📈 실시간 차트 분석"])

# --- [탭 1: 나의 종목 현황] ---
with tab1:
    st.subheader("관심 종목 실시간 차트 및 투자 성과")
    
    # 요청하신 종목 리스트
    my_stock_tickers = ["005930.KS", "035720.KS", "323410.KS", "090470.KQ", "000660.KS"]
    
    # 데이터를 먼저 가져와서 총 자산 계산에 사용
    my_stocks_data = []
    for ticker in my_stock_tickers:
        stock_data = get_data(ticker)
        if stock_data:
            my_stocks_data.append(stock_data)
    
    # 총 자산 계산
    total_val_krw = 0
    for s in my_stocks_data:
        curr_price = s['data']['Close'].iloc[-1]
        if s['ticker'] == "005930.KS": total_val_krw += curr_price * samsung_qty
        elif s['ticker'] == "000660.KS": total_val_krw += curr_price * hynix_qty
    
    # 상단 총 자산 메트릭
    st.metric("Total Investment Assets", f"{total_val_krw:,.0f}원")
    st.divider()
    
    # 종목별 루프 (차트 포함)
    for s in my_stocks_data:
        curr_price = s['data']['Close'].iloc[-1]
        prev_price = s['data']['Close'].iloc[-2]
        diff = curr_price - prev_price
        pct = (diff / prev_price) * 100
        
        color = "price-up" if pct >= 0 else "price-down"
        sign = "+" if pct >= 0 else ""
        
        # 종목 정보 카드
        st.markdown(f"""
            <div class="market-card">
                <div class="market-name">{s['name']} ({s['ticker']})</div>
                <div class="market-price">{curr_price:,.0f}원</div>
                <div class="{color}" style="font-weight:600;">{sign}{pct:.2f}% ({sign}{diff:,.0f}원)</div>
            </div>
        """, unsafe_allow_html=True)
        
        # 종목별 실시간 차트 (흰색 배경)
        st.plotly_chart(create_stock_chart(s['data'], s['name'], s['currency']), use_container_width=True, config={'displayModeBar': False})
        st.divider()

# --- [탭 2: 시장 대시보드] ---
with tab2:
    st.subheader("통합 시장 현황")
    market_categories = {
        "글로벌 주요 지수": ["^KS11", "^KQ11", "^NDX", "^GSPC"],
        "주요 지표 & 상품": ["USDKRW=X", "CL=F", "GC=F"],
        "가상자산 시장": ["BTC-USD", "ETH-USD", "DOGE-USD"]
    }
    
    for category_name, category_tickers in market_categories.items():
        st.subheader(category_name)
        markets_data = get_dashboard_data(category_tickers)
        cols = st.columns(4)
        
        for i, s in enumerate(markets_data):
            with cols[i % 4]:
                color = "price-up" if s['pct'] >= 0 else "price-down"
                sign = "+" if s['pct'] >= 0 else ""
                
                currency_symbol = s['ticker'].split('-')[-1] if '-' in s['ticker'] else "USD"
                if currency_symbol == "USD": currency_symbol = "$"
                elif currency_symbol == "X": currency_symbol = "₩" 
                
                price_text = f"{s['price']:,.2f}" if s['price'] < 100 else f"{s['price']:,.0f}"

                st.markdown(f"""
                    <div class="market-card">
                        <div class="market-name">{s['name']}</div>
                        <div class="market-price">{currency_symbol}{price_text}</div>
                        <div class="{color}" style="font-weight:600;">
                            {sign}{s['pct']:.2f}%
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                # 스파크라인 차트 추가 (흰색 배경)
                st.plotly_chart(create_sparkline(s['chart_data']), use_container_width=True, config={'displayModeBar': False})
    st.divider()

# --- [탭 3: 상세 차트 분석] ---
with tab3:
    st.subheader("종목별 상세 차트 분석 (MA 5/20/60)")
    target_tickers_chart = ["005930.KS", "035720.KS", "BTC-USD", "^KS11", "^NDX", "USDKRW=X", "CL=F", "GC=F"]
    selected = st.selectbox("분석 종목 선택", target_tickers_chart)
    
    period = st.radio("기간 선택", ["1D", "5D", "1M", "6M", "1Y"], horizontal=True)
    interval_map = {"1D":"1m", "5D":"5m", "1M":"1d", "6M":"1d", "1Y":"1d"}
    
    stock_chart_data = get_data(selected, period=period.lower(), interval=interval_map[period])
    
    if stock_chart_data:
        df_detailed = stock_chart_data['data']
        num_days = 60 if period in ["1M", "6M", "1Y"] else len(df_detailed)
        plot_df_detailed = df_detailed.tail(num_days)
        
        # Plotly 캔들스틱 + 이평선 (흰색 테마)
        fig_detailed = go.Figure()
        fig_detailed.add_trace(go.Candlestick(
            x=plot_df_detailed.index, open=plot_df_detailed['Open'], high=plot_df_detailed['High'],
            low=plot_df_detailed['Low'], close=plot_df_detailed['Close'], name="Price",
            increasing_line_color='#10b981', decreasing_line_color='#ef4444'
        ))
        
        # 보정된 이평선 색상 적용
        if 'MA5' in plot_df_detailed.columns: fig_detailed.add_trace(go.Scatter(x=plot_df_detailed.index, y=plot_df_detailed['MA5'], line=dict(color='#BF9B30', width=1.5), name="MA5")) # 진한 노랑
        if 'MA20' in plot_df_detailed.columns: fig_detailed.add_trace(go.Scatter(x=plot_df_detailed.index, y=plot_df_detailed['MA20'], line=dict(color='#8A2BE2', width=1.5), name="MA20")) # 진한 퍼플
        if 'MA60' in plot_df_detailed.columns: fig_detailed.add_trace(go.Scatter(x=plot_df_detailed.index, y=plot_df_detailed['MA60'], line=dict(color='#1E90FF', width=1.5), name="MA60")) # 진한 블루
        
        fig_detailed.update_layout(
            template="plotly_white", plot_bgcolor='#ffffff', paper_bgcolor='#ffffff',
            xaxis=dict(rangeslider_visible=False, gridcolor='#e9ecef', tickfont=dict(color='#000000')),
            yaxis=dict(gridcolor='#e9ecef', tickfont=dict(color='#000000'), title=dict(font=dict(color='#000000'))),
            height=500, margin=dict(l=10, r=10, t=10, b=10),
            title=dict(font=dict(color='#000000')), legend=dict(font=dict(color='#000000'))
        )
        st.plotly_chart(fig_detailed, use_container_width=True)