import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 페이지 기본 설정
st.set_page_config(page_title="영화 박스오피스 분석", layout="wide")

# [1. 데이터 불러오기]
# @st.cache_data를 사용해 앱을 새로고침할 때마다 데이터를 다시 다운로드하지 않고 캐시에 저장합니다.
@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/keep-growing-park/data-science/refs/heads/main/dataset/kobis_1year_boxoffice.csv"
    df = pd.read_csv(url)
    
    # [2. 날짜 전처리]
    # 결측치가 하나라도 포함된 행은 제거합니다.
    df = df.dropna()
    
    # '기준일자' 컬럼을 문자열에서 날짜(datetime) 형식으로 변환합니다.
    df['기준일자'] = pd.to_datetime(df['기준일자'])
    
    # 데이터를 기준일자 오름차순으로 정렬합니다.
    df = df.sort_values('기준일자')
    
    return df

# 데이터 로딩
df = load_data()

st.title("🎬 영화 박스오피스 데이터 분석")

# [3. 영화 선택 기능]
# 영화별 최고 누적관객수를 구해 내림차순으로 정렬한 뒤 전체 영화 이름 목록을 생성합니다.
movie_list = df.groupby('영화명')['누적관객수'].max().sort_values(ascending=False).index.tolist()

# 사이드바에 개별 영화 선택 셀렉트박스를 생성합니다.
selected_movie = st.sidebar.selectbox("영화를 선택하세요:", movie_list)

# 선택된 단일 영화 데이터만 필터링합니다.
movie_df = df[df['영화명'] == selected_movie]

# ---------------------------------------------------------
# [첫 번째 구역] 개별 영화 - 일별 관객수 (선 그래프)
# ---------------------------------------------------------
with st.container():
    st.subheader(f"📊 {selected_movie} - 일별 관객수 추이")
    
    fig1 = px.line(
        movie_df,
        x='기준일자',
        y='해당일관객수',
        title=f"[{selected_movie}] 일별 관객수 변화 그래프",
        markers=True
    )
    
    fig1.update_layout(
        xaxis_title="기준일자",
        yaxis_title="해당일 관객수(명)",
        hovermode="x unified"
    )
    
    st.plotly_chart(fig1, use_container_width=True)
    st.info(f"💡 **이 그래프로 알 수 있는 것:** {selected_movie}의 개봉 후 일자별 관객수 증감 패턴(주말 상승/평일 감소)과 최대 관객을 동원한 전성기 시점을 확인할 수 있습니다.")

st.divider()

# ---------------------------------------------------------
# [두 번째 구역] 개별 영화 - 누적 관객수 (영역 차트)
# ---------------------------------------------------------
with st.container():
    st.subheader(f"📈 {selected_movie} - 누적 관객수 성장 추이")
    
    fig2 = px.area(
        movie_df,
        x='기준일자',
        y='누적관객수',
        title=f"[{selected_movie}] 누적 관객수 변화 그래프",
        markers=True
    )
    
    fig2.update_layout(
        xaxis_title="기준일자",
        yaxis_title="누적 관객수(명)",
        hovermode="x unified"
    )
    
    st.plotly_chart(fig2, use_container_width=True)
    st.info(f"💡 **이 그래프로 알 수 있는 것:** 시간 경과에 따른 {selected_movie}의 전체 누적 관객수 증가 속도와 관객 동원이 완만해지는 흥행 정체 시점을 파악할 수 있습니다.")

st.divider()

# ---------------------------------------------------------
# [세 번째 구역] 20일 이상 등장한 영화 중 누적 관객수 TOP 5 비교 (다중 선 그래프)
# ---------------------------------------------------------
with st.container():
    st.subheader("🏆 20일 이상 차트인 영화 중 TOP 5 누적 관객수 추이 비교")
    
    movie_counts = df['영화명'].value_counts()
    over_20_days_movies = movie_counts[movie_counts >= 20].index
    filtered_df = df[df['영화명'].isin(over_20_days_movies)]
    
    top5_movies = filtered_df.groupby('영화명')['누적관객수'].max().nlargest(5).index.tolist()
    top5_df = df[df['영화명'].isin(top5_movies)]
    
    fig3 = px.line(
        top5_df,
        x='기준일자',
        y='누적관객수',
        color='영화명',
        title="20일 이상 차트인한 주요 흥행작 TOP 5의 누적 관객수 변화 비교",
        markers=True
    )
    
    fig3.update_layout(
        xaxis_title="기준일자",
        yaxis_title="누적 관객수(명)",
        hovermode="x unified",
        legend_title="영화 제목"
    )
    
    st.plotly_chart(fig3, use_container_width=True)
    st.info("💡 **이 그래프로 알 수 있는 것:** 단기 반짝 흥행을 제외하고 최소 20일 이상 차트에 머문 대표 '장기 흥행작' 5편의 누적 관객수 증가 속도와 최종 흥행 스케일을 비교해볼 수 있습니다.")

st.divider()

# ---------------------------------------------------------
# [네 번째 구역] 전체 박스오피스 일별 총 관객수 & 7일 이동평균선
# ---------------------------------------------------------
with st.container():
    st.subheader("📉 전체 박스오피스 일별 총 관객수 및 7일 이동평균 추이")
    
    daily_total = df.groupby('기준일자')['해당일관객수'].sum().reset_index()
    daily_total['7일이동평균'] = daily_total['해당일관객수'].rolling(window=7).mean()
    
    fig4 = go.Figure()
    
    fig4.add_trace(go.Scatter(
        x=daily_total['기준일자'],
        y=daily_total['해당일관객수'],
        mode='lines',
        name='일별 총 관객수 (원 데이터)',
        line=dict(color='lightblue', width=1.5),
        opacity=0.6
    ))
    
    fig4.add_trace(go.Scatter(
        x=daily_total['기준일자'],
        y=daily_total['7일이동평균'],
        mode='lines',
        name='7일 이동평균',
        line=dict(color='royalblue', width=3)
    ))
    
    fig4.update_layout(
        title="박스오피스 전체 일별 총 관객수와 7일 이동평균 추세",
        xaxis_title="기준일자",
        yaxis_title="총 관객수(명)",
        hovermode="x unified"
    )
    
    st.plotly_chart(fig4, use_container_width=True)
    st.info("💡 **이 그래프로 알 수 있는 것:** 주말과 평일의 반복적인 일별 변동성(노이즈)을 정돈하여, 극장가 전체 관객 수의 전반적인 성수기·비수기 흐름과 중장기적 상승/하락 추세를 부드럽게 파악할 수 있습니다.")

st.divider()

# ---------------------------------------------------------
# [다섯 번째 구역] 월별 박스오피스 전체 관객수 합계 (막대 그래프)
# ---------------------------------------------------------
with st.container():
    st.subheader("🗓️ 월별 전체 관객수 집계")
    
    daily_total['연월'] = daily_total['기준일자'].dt.strftime('%Y-%m')
    monthly_total = daily_total.groupby('연월')['해당일관객수'].sum().reset_index()
    
    fig5 = px.bar(
        monthly_total,
        x='연월',
        y='해당일관객수',
        title="월별 박스오피스 전체 관객수 합계",
        text_auto=True
    )
    
    fig5.update_layout(
        xaxis_title="월 (연-월)",
        yaxis_title="총 관객수(명)",
        hovermode="x unified"
    )
    
    st.plotly_chart(fig5, use_container_width=True)
    st.info("💡 **이 그래프로 알 수 있는 것:** 연중 어느 월에 극장 관객수가 가장 집중되는지(여름/겨울 성수기 vs 봄/가을 비수기) 월 단위의 시장 규모 차이를 한눈에 직관적으로 비교할 수 있습니다.")

st.divider()

# ---------------------------------------------------------
# [여섯 번째 구역] 캘린더 히트맵 (주차별 x 요일별 관객수)
# ---------------------------------------------------------
with st.container():
    st.subheader("📅 주차별 × 요일별 관객수 캘린더 히트맵")
    
    # 1. 요일 순서 지정 (월요일부터 일요일) 및 한국어 요일 매핑
    weekday_order = ['월', '화', '수', '목', '금', '토', '일']
    weekday_map = {0: '월', 1: '화', 2: '수', 3: '목', 4: '금', 5: '토', 6: '일'}
    
    # 2. 날짜 데이터에서 요일, ISO 주차, YYYY-MM-DD 문자열을 추출합니다.
    heatmap_df = daily_total.copy()
    heatmap_df['요일'] = heatmap_df['기준일자'].dt.weekday.map(weekday_map)
    
    iso_cal = heatmap_df['기준일자'].dt.isocalendar()
    heatmap_df['주차'] = iso_cal.year.astype(str) + "년 " + iso_cal.week.astype(str).str.zfill(2) + "주차"
    heatmap_df['날짜str'] = heatmap_df['기준일자'].dt.strftime('%Y-%m-%d')
    
    # 3. Y축(주차) x X축(요일) 형태의 피벗 테이블을 생성합니다.
    pivot_val = heatmap_df.pivot(index='주차', columns='요일', values='해당일관객수').reindex(columns=weekday_order)
    pivot_date = heatmap_df.pivot(index='주차', columns='요일', values='날짜str').reindex(columns=weekday_order)
    
    # 4. Plotly Heatmap을 사용하여 캘린더 형태 시각화 (색이 진할수록 관객수 증가)
    fig6 = go.Figure(data=go.Heatmap(
        z=pivot_val.values,
        x=weekday_order,
        y=pivot_val.index,
        text=pivot_date.values,
        hoverinfo='text+z',
        hovertemplate='<b>날짜: %{text}</b><br>요일: %{x}<br>관객수: %{z:,.0f}명<extra></extra>',
        colorscale='Blues'  # 관객수가 많을수록 진한 파란색
    ))
    
    fig6.update_layout(
        title="일별 박스오피스 관객수 분포 히트맵",
        xaxis_title="요일",
        yaxis_title="주차",
        yaxis=dict(autorange='reversed')  # 날짜 흐름에 맞춰 이전 주차가 상단에 위치
    )
    
    st.plotly_chart(fig6, use_container_width=True)
    st.info("💡 **이 그래프로 알 수 있는 것:** 주차별·요일별 관객 동원 패턴을 캘린더 형태로 한눈에 파악할 수 있으며, 공휴일이나 연휴 등 특정 일자에 극장 관객수가 급증한 지점을 직관적으로 찾아낼 수 있습니다.")
