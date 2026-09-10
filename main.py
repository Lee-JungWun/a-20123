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
    
    # 1. 영화별 등장 일수(데이터 행 수)를 계산합니다.
    movie_counts = df['영화명'].value_counts()
    
    # 2. 등장 일수가 20일 이상인 영화 이름만 걸러냅니다.
    over_20_days_movies = movie_counts[movie_counts >= 20].index
    
    # 3. 20일 이상 등장한 영화들의 데이터만 1차로 필터링합니다.
    filtered_df = df[df['영화명'].isin(over_20_days_movies)]
    
    # 4. 필터링된 영화 중 최고 누적관객수가 가장 높은 상위 5개 영화를 선별합니다.
    top5_movies = filtered_df.groupby('영화명')['누적관객수'].max().nlargest(5).index.tolist()
    
    # 5. 상위 5개 영화에 해당하는 데이터만 최종 추출합니다.
    top5_df = df[df['영화명'].isin(top5_movies)]
    
    # 6. 다중 선 그래프 생성
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
    
    # 1. 기준일자별로 전체 영화(TOP10)의 해당일관객수를 모두 합산합니다.
    daily_total = df.groupby('기준일자')['해당일관객수'].sum().reset_index()
    
    # 2. 7일 이동평균(Rolling Mean)을 계산합니다.
    daily_total['7일이동평균'] = daily_total['해당일관객수'].rolling(window=7).mean()
    
    # 3. Graph Objects를 사용하여 원본 데이터와 이동평균선을 겹쳐 그립니다.
    fig4 = go.Figure()
    
    # 원본 데이터 선 (연한 색상)
    fig4.add_trace(go.Scatter(
        x=daily_total['기준일자'],
        y=daily_total['해당일관객수'],
        mode='lines',
        name='일별 총 관객수 (원 데이터)',
        line=dict(color='lightblue', width=1.5),
        opacity=0.6
    ))
    
    # 7일 이동평균선 (진한 색상)
    fig4.add_trace(go.Scatter(
        x=daily_total['기준일자'],
        y=daily_total['7일이동평균'],
        mode='lines',
        name='7일 이동평균',
        line=dict(color='royalblue', width=3)
    ))
    
    # 레이블 및 스타일 지정
    fig4.update_layout(
        title="박스오피스 전체 일별 총 관객수와 7일 이동평균 추세",
        xaxis_title="기준일자",
        yaxis_title="총 관객수(명)",
        hovermode="x unified"
    )
    
    st.plotly_chart(fig4, use_container_width=True)
    st.info("💡 **이 그래프로 알 수 있는 것:** 주말과 평일의 반복적인 일별 변동성(노이즈)을 정돈하여, 극장가 전체 관객 수의 전반적인 성수기·비수기 흐름과 중장기적 상승/하락 추세를 부드럽게 파악할 수 있습니다.")
