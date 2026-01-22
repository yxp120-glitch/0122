import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import io

# 페이지 설정
st.set_page_config(page_title="서울 기온 분석기 Pro", layout="wide", page_icon="🌡️")

# 데이터 로딩 함수 (인코딩 자동 감지 로직 추가)
@st.cache_data
def load_data(file):
    encodings = ['utf-8', 'cp949', 'euc-kr'] # 시도할 인코딩 목록
    
    for encoding in encodings:
        try:
            # 파일 포인터를 처음으로 되돌림 (여러 번 읽기 위해)
            if hasattr(file, 'seek'):
                file.seek(0)
            
            # 데이터 읽기 시도
            df = pd.read_csv(file, encoding=encoding, skiprows=7)
            
            # 날짜 컬럼 전처리
            if '날짜' in df.columns:
                df['날짜'] = df['날짜'].astype(str).str.strip()
                df['날짜'] = pd.to_datetime(df['날짜'], errors='coerce')
                df = df.dropna(subset=['날짜', '평균기온(℃)'])
                return df
        except UnicodeDecodeError:
            continue
        except Exception as e:
            st.error(f"오류 발생: {e}")
            return None
            
    st.error("파일의 인코딩을 인식할 수 없습니다. UTF-8 또는 CP949 형식인지 확인해주세요.")
    return None

# --- 이하 기존 코드와 동일하게 유지 ---
st.title("🌡️ 서울 기온 비교 데이터 분석기")

default_file = 'ta_20260122174530.csv'
uploaded_file = st.sidebar.file_uploader("추가 기온 데이터 업로드 (CSV)", type=['csv'])

if uploaded_file:
    df = load_data(uploaded_file)
else:
    # 기본 파일 로드 시에도 동일한 함수 사용
    try:
        with open(default_file, 'rb') as f:
            df = load_data(f)
    except FileNotFoundError:
        st.error(f"기본 데이터 파일({default_file})을 찾을 수 없습니다.")
        df = None

if df is not None:
    # 날짜 선택 및 시각화 로직 (기존과 동일)
    max_date = df['날짜'].max().date()
    min_date = df['날짜'].min().date()
    
    st.sidebar.divider()
    selected_date = st.sidebar.date_input(
        "📅 비교 기준일 선택",
        value=max_date,
        min_value=min_date,
        max_value=max_date
    )

    target_month = selected_date.month
    target_day = selected_date.day
    same_day_df = df[(df['날짜'].dt.month == target_month) & (df['날짜'].dt.day == target_day)].copy()
    same_day_df['연도'] = same_day_df['날짜'].dt.year
    target_row = same_day_df[same_day_df['날짜'].dt.date == selected_date]

    if not target_row.empty:
        curr_temp = target_row['평균기온(℃)'].values[0]
        hist_avg = same_day_df['평균기온(℃)'].mean()
        
        st.subheader(f"📊 {selected_date.year}년 {target_month}월 {target_day}일 요약")
        m1, m2, m3 = st.columns(3)
        m1.metric("선택한 날 기온", f"{curr_temp} ℃")
        m2.metric("역대 평균", f"{hist_avg:.1f} ℃", delta=round(curr_temp - hist_avg, 2))
        m3.metric("데이터 개수", f"{len(same_day_df)} 개년")

        # Plotly 차트 생성
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=same_day_df['연도'], y=same_day_df['평균기온(℃)'], mode='lines+markers', name='과거 기온'))
        fig.add_trace(go.Scatter(x=[selected_date.year], y=[curr_temp], mode='markers', name='선택한 날', marker=dict(color='red', size=12)))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("⚠️ 해당 날짜의 데이터가 존재하지 않습니다.")
