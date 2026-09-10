import streamlit as st
import pandas as pd
import plotly.express as px

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
# 영화별 최고 누적관객수를 구해 내림차순으로 정렬한 뒤 영화 이름 목록을 생성합니다.
movie_list = df.groupby('영화명')['누적관객수'].max().sort_values(ascending=False).index.tolist()

# 사이드바에 영화 선택 셀렉트박스를 생성합니다.
selected_movie = st.sidebar.selectbox("영화를 선택하세요:", movie_list)

# 선택된 영화에 해당하는 데이터만 필터링합니다.
movie_df = df[df['영화명'] == selected_movie]

# ---------------------------------------------------------
# [첫 번째 구역] 일별 관객수 (선 그래프)
# ---------------------------------------------------------
with st.container():
    st.subheader(f"📊 {selected_movie} - 일별 관객수 추이")
    
    # [4. 선그래프 그리기]
    fig1 = px.line(
        movie_df,
        x='기준일자',
        y='해당일관객수',
        title=f"[{selected_movie}] 일별 관객수 변화 그래프",
        markers=True
    )
    
    # X축/Y축 레이블 및 스타일 설정
    fig1.update_layout(
        xaxis_title="기준일자",
        yaxis_title="해당일 관객수(명)",
        hovermode="x unified"
    )
    
    # Streamlit 화면에 Plotly 그래프 출력
    st.plotly_chart(fig1, use_container_width=True)
    
    # 그래프 설명 문구
    st.info(f"💡 **이 그래프로 알 수 있는 것:** {selected_movie}의 개봉 후 일자별 관객수 증감 패턴(주말 상승/평일 감소)과 최대 관객을 동원한 전성기 시점을 확인할 수 있습니다.")

st.divider()

# ---------------------------------------------------------
# [두 번째 구역] 누적 관객수 (영역 차트)
# ---------------------------------------------------------
with st.container():
    st.subheader(f"📈 {selected_movie} - 누적 관객수 성장 추이")
    
    # [새로 추가된 영역차트 그리기]
    # px.area 함수를 사용하여 기준일자별 누적관객수 변화를 나타냅니다.
    fig2 = px.area(
        movie_df,
        x='기준일자',
        y='누적관객수',
        title=f"[{selected_movie}] 누적 관객수 변화 그래프",
        markers=True
    )
    
    # X축/Y축 레이블 및 스타일 설정
    fig2.update_layout(
        xaxis_title="기준일자",
        yaxis_title="누적 관객수(명)",
        hovermode="x unified"
    )
    
    # Streamlit 화면에 영역차트 출력
    st.plotly_chart(fig2, use_container_width=True)
    
    # 영역차트 설명 문구
    st.info(f"💡 **이 그래프로 알 수 있는 것:** 시간 경과에 따른 {selected_movie}의 전체 누적 관객수 증가 속도와 관객 동원이 완만해지는 흥행 정체 시점을 파악할 수 있습니다.")
