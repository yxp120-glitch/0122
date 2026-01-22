import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# 페이지 설정
st.set_page_config(page_title="서울 기온 분석기 Pro", layout="wide", page_icon="🌡️")

# 스타일링 (CSS)
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

st.title("🌡️ 서울 기온 비교 데이터 분석기")
st.markdown("과거 100년 이상의 데이터를 바탕으로, 오늘(또는 특정일)의 기온이 역사적으로 어느 정도 위치인지 분석합니다.")

# 데이터 로딩 함수
@st.cache_data
def load_data(file):
    try:
        # 데이터 읽기 및 전처리
        df = pd.read_csv(file, encoding='utf-8', skiprows=7)
        df['날짜'] = df['날짜'].str.strip()
        df['날짜'] = pd.to_datetime(df['날짜'])
        # 결측치가 있는 행은 분석의 정확도를 위해 제거하거나 무시
        df = df.dropna(subset=['평균기온(℃)'])
        return df
    except Exception as e:
        st.error(f"데이터 로딩 오류: {e}")
        return None

# 1. 데이터 소스 처리
default_file = 'ta_20260122174530.csv'
uploaded_file = st.sidebar.file_uploader("추가 기온 데이터 업로드 (CSV)", type=['csv'])

if uploaded_file:
    df = load_data(uploaded_file)
    st.sidebar.success("✅ 사용자 데이터 로드 완료")
else:
    df = load_data(default_file)
    st.sidebar.info("ℹ️ 기본 데이터를 사용 중입니다.")

if df is not None:
    # 2. 날짜 선택
    max_date = df['날짜'].max().date()
    min_date = df['날짜'].min().date()
    
    st.sidebar.divider()
    selected_date = st.sidebar.date_input(
        "📅 비교 기준일 선택",
        value=max_date,
        min_value=min_date,
        max_value=max_date
    )

    # 3. 데이터 필터링 (같은 월, 일 데이터 추출)
    target_month = selected_date.month
    target_day = selected_date.day
    
    # 동일 월/일 역대 데이터
    same_day_df = df[(df['날짜'].dt.month == target_month) & (df['날짜'].dt.day == target_day)].copy()
    same_day_df['연도'] = same_day_df['날짜'].dt.year
    
    # 선택한 날의 실제 데이터
    target_row = same_day_df[same_day_df['날짜'].dt.date == selected_date]

    if not target_row.empty:
        curr_temp = target_row['평균기온(℃)'].values[0]
        hist_avg = same_day_df['평균기온(℃)'].mean()
        hist_max = same_day_df['평균기온(℃)'].max()
        hist_min = same_day_df['평균기온(℃)'].min()
        diff = curr_temp - hist_avg

        # 결과 요약 지표 (Metrics)
        st.subheader(f"📊 {selected_date.year}년 {target_month}월 {target_day}일 요약")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("선택한 날 기온", f"{curr_temp} ℃")
        m2.metric("역대 평균", f"{hist_avg:.1f} ℃", delta=round(diff, 2))
        m3.metric("역대 최고", f"{hist_max} ℃")
        m4.metric("역대 최저", f"{hist_min} ℃")

        # 4. Plotly를 이용한 인터렉티브 차트
        st.divider()
        st.subheader(f"📈 역대 {target_month}월 {target_day}일 평균 기온 변화")
        
        fig = go.Figure()

        # 전체 과거 기온 선 그래프
        fig.add_trace(go.Scatter(
            x=same_day_df['연도'], 
            y=same_day_df['평균기온(℃)'],
            mode='lines+markers',
            name='과거 기온',
            line=dict(color='lightgray', width=1),
            marker=dict(size=4),
            hovertemplate='%{x}년: %{y}℃<extra></extra>'
        ))

        # 역대 평균 가로선
        fig.add_hline(y=hist_avg, line_dash="dash", line_color="blue", 
                      annotation_text=f"평균: {hist_avg:.1f}℃", annotation_position="bottom right")

        # 선택한 날 포인트 강조
        fig.add_trace(go.Scatter(
            x=[selected_date.year], 
            y=[curr_temp],
            mode='markers',
            name='선택한 날',
            marker=dict(color='red', size=12, symbol='star'),
            hovertemplate='%{x}년(현재): %{y}℃<extra></extra>'
        ))

        fig.update_layout(
            hovermode="x unified",
            xaxis_title="연도",
            yaxis_title="평균 기온 (℃)",
            showlegend=True,
            template="plotly_white",
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)

        # 5. 분포 분석 (Histogram)
        st.subheader("🌡️ 동일 날짜 기온 분포 내 위치")
        
        fig_dist = px.histogram(
            same_day_df, x="평균기온(℃)", 
            nbins=20, 
            title=f"역대 {target_month}/{target_day} 기온 분포",
            color_discrete_sequence=['skyblue']
        )
        # 현재 기온 위치 표시
        fig_dist.add_vline(x=curr_temp, line_width=3, line_color="red", 
                           annotation_text="현재 위치", annotation_position="top right")
        
        st.plotly_chart(fig_dist, use_container_width=True)

        # 6. 통계 텍스트 요약
        rank = same_day_df['평균기온(℃)'].rank(ascending=False).loc[target_row.index[0]]
        total = len(same_day_df)
        st.info(f"💡 **{selected_date.year}년 {target_month}월 {target_day}일**은 관측 데이터 {total}개 연도 중 **{int(rank)}위**로 더운 날이었습니다. (상위 {rank/total*100:.1f}%)")

    else:
        st.warning("⚠️ 해당 날짜의 데이터가 존재하지 않습니다. 다른 날짜를 선택해 주세요.")
else:
    st.error("데이터를 불러올 수 없습니다. 파일 형식을 확인해 주세요.")
