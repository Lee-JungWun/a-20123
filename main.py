import streamlit as st
st.title("나의 데이터 과학 포트폴리오")
st.write("반갑습니다! 이제부터 여기에 제 작업을 기록합니다.")
import streamlit as st
import pandas as pd
import plotly.express as px

# -----------------------------------------------------------------------------
# 페이지 기본 설정 (웹 브라우저 탭 제목 및 레이아웃)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="영화 박스오피스 분석 대시보드",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 영화별 일별 관객수 추이 분석")
st.caption("최근 1년간의 KOBIS 박스오피스 데이터를 통해 영화의 흥행 흐름을 분석합니다.")

# -----------------------------------------------------------------------------
# [1. 데이터 불러오기 및 2. 데이터 전처리]
# -----------------------------------------------------------------------------
# @st.cache_data 어노테이션을 붙이면 매번 인터넷에서 데이터를 새로 읽지 않고
# 한 번 불러온 데이터를 메모리에 저장(캐싱)하여 앱 실행 속도가 훨씬 빨라집니다.
@st.cache_data
def load_and_preprocess_data():
    url = "https://raw.githubusercontent.com/keep-growing-park/data-science/refs/heads/main/dataset/kobis_1year_boxoffice.csv"
    
    # pandas 라이브러리로 인터넷 상의 CSV 파일 읽어오기
    df = pd.read_csv(url)
    
    # [전처리 1] 결측치(빈 데이터)가 포함된 행 모두 삭제
    df = df.dropna().copy()
    
    # [전처리 2] "기준일자" 컬럼을 문자열에서 날짜(datetime) 형식으로 변환
    df["기준일자"] = pd.to_datetime(df["기준일자"])
    
    # [전처리 3] 데이터를 "기준일자" 순서대로 정렬 (과거 -> 최근)
    df = df.sort_values(by="기준일자", ascending=True).reset_index(drop=True)
    
    return df

# 캐싱 처리된 데이터 로드
with st.spinner("박스오피스 데이터를 불러오는 중..."):
    df = load_and_preprocess_data()

# -----------------------------------------------------------------------------
# [3. 영화 선택 기능 (사이드바)]
# -----------------------------------------------------------------------------
st.sidebar.header("🔍 분석할 영화 선택")

# 영화별 최고 "누적관객수"를 구한 뒤, 관객수가 많은 순서대로(내림차순) 정렬합니다.
movie_ranking = (
    df.groupby("영화명")["누적관객수"]
    .max()
    .sort_values(ascending=False)
)

# 누적관객수 내림차순으로 정렬된 영화 이름 목록 추출
movie_options = movie_ranking.index.tolist()

# 사용자가 드롭다운 목록에서 영화를 고를 수 있게 합니다.
selected_movie = st.sidebar.selectbox(
    "영화 목록 (누적관객수 높은 순):",
    options=movie_options
)

# -----------------------------------------------------------------------------
# 선택된 영화의 데이터만 필터링
# -----------------------------------------------------------------------------
filtered_df = df[df["영화명"] == selected_movie].copy()

# 선택한 영화의 핵심 정보를 상단 카드(Metric)로 보여줍니다.
max_audi_acc = filtered_df["누적관객수"].max()
start_date = filtered_df["기준일자"].min().strftime("%Y-%m-%d")
end_date = filtered_df["기준일자"].max().strftime("%Y-%m-%d")

col_a, col_b, col_c = st.columns(3)
with col_a:
    st.metric(label="🎥 선택한 영화명", value=selected_movie)
with col_b:
    st.metric(label="🏆 최고 누적관객수", value=f"{max_audi_acc:,} 명")
with col_c:
    st.metric(label="📅 데이터 집계 기간", value=f"{start_date} ~ {end_date}")

st.markdown("---")

# -----------------------------------------------------------------------------
# [5. 기타 - 구역 나누기 (Tab 구조 활용)]
# 향후 새로운 그래프나 분석 내용을 계속 추가하기 쉽도록 탭으로 구역을 나누었습니다.
# -----------------------------------------------------------------------------
tab1, tab2 = st.tabs(["📈 일별 관객수 추이", "📊 추가 그래프 예정 구역"])

# -----------------------------------------------------------------------------
# [4. 선그래프 그리기 (Plotly)]
# -----------------------------------------------------------------------------
with tab1:
    st.subheader(f"[{selected_movie}] 일별 관객수 변화 추이")
    
    # Plotly express를 이용해 날짜별 관객수 변화를 선그래프로 그립니다.
    fig = px.line(
        filtered_df,
        x="기준일자",
        y="해당일관객수",
        title=f"[{selected_movie}] 기준일자별 해당일관객수 그래프",
        markers=True,  # 각 데이터 지점에 점 표기
        labels={
            "기준일자": "날짜 (기준일자)",
            "해당일관객수": "해당일 관객수 (명)"
        }
    )
    
    # 그래프 스타일 조정 (선 색상, 마우스 커서 호버 디자인 등)
    fig.update_traces(
        line_color="#E50914",
        hovertemplate="<b>날짜:</b> %{x|%Y-%m-%d}<br><b>관객수:</b> %{y:,}명<extra></extra>"
    )
    fig.update_layout(
        hovermode="x unified",
        xaxis_title="기준일자",
        yaxis_title="해당일 관객수(명)",
        margin=dict(l=20, r=20, t=50, b=20)
    )
    
    # Streamlit 화면에 Plotly 그래프 출력
    st.plotly_chart(fig, use_container_width=True)
    
    # [5. 기타 - 그래프 설명 문구 자리]
    st.info(
        f"💡 **이 그래프로 알 수 있는 것:** "
        f"선택한 영화 '{selected_movie}'의 개봉 초기 관객 집중도와 "
        f"주말/평일 간의 관객수 등락 패턴 및 전체적인 흥행 유지 기간을 한눈에 파악할 수 있습니다."
    )

# -----------------------------------------------------------------------------
# [5. 기타 - 추후 그래프 추가용 구역 예시]
# -----------------------------------------------------------------------------
with tab2:
    st.subheader("🚀 향후 그래프 추가 구역")
    st.write("이 공간은 앞으로 매출액 추이, 요일별 관객 비율 등 추가 그래프가 들어올 자리입니다.")
    
    # 추후 추가될 그래프를 위한 설명 문구 자리 예시
    st.info(
        "💡 **이 그래프로 알 수 있는 것:** "
        "(추후 새로운 그래프가 추가되면 해당 시각화 결과를 설명하는 한 문장 분석 결과가 입력되는 자리입니다.)"
    )
