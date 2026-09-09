import streamlit as st
st.title("나의 데이터 과학 포트폴리오")
st.write("반갑습니다! 이제부터 여기에 제 작업을 기록합니다.")
import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta, timezone

# -----------------------------------------------------------------------------
# 1. 페이지 기본 설정 및 디자인
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="어제 박스오피스",
    page_icon="🎬",
    layout="wide"
)

# -----------------------------------------------------------------------------
# 2. 한국 시간(KST: UTC+9) 기준 어제 날짜 계산
# -----------------------------------------------------------------------------
# 배포 서버가 해외(UTC)에 있어도 항상 한국 기준 어제 날짜를 구합니다.
KST = timezone(timedelta(hours=9))
today_kst = datetime.now(KST)
yesterday_kst = today_kst - timedelta(days=1)

# API 요청에 필요한 여덟 자리 날짜 (예: "20260908")
target_dt = yesterday_kst.strftime("%Y%m%d")
# 화면 표기용 날짜 (예: "2026년 09월 08일")
formatted_date = yesterday_kst.strftime("%Y년 %m월 %d일")

st.title("🎬 일별 박스오피스 TOP 10")
st.caption(f"📅 기준일자: **{formatted_date}** (한국 시간 기준 어제)")

# -----------------------------------------------------------------------------
# 3. 비밀 금고(Secrets)에서 API 키 불러오기 및 검증
# -----------------------------------------------------------------------------
# 코드에 키를 직접 적지 않고 스트림릿 비밀 금고에서 안전하게 읽어옵니다.
if "KOBIS_KEY" not in st.secrets:
    st.error(
        "🔑 **API 인증키(KOBIS_KEY)를 찾을 수 없습니다.**\n\n"
        "**[해결 방법]**\n"
        "1. Streamlit Cloud 앱 관리 페이지의 **[Settings] -> [Secrets]** 메뉴로 이동합니다.\n"
        "2. 아래와 같이 KOBIS 인증키를 입력하고 저장해 주세요.\n"
        "   ```toml\n"
        '   KOBIS_KEY = "발급받은_인증키_문자열"\n'
        "   ```\n"
        "3. 로컬 테스트 중이라면 `.streamlit/secrets.toml` 파일에 위 내용을 작성해 주세요."
    )
    st.stop()

api_key = st.secrets["KOBIS_KEY"]

# -----------------------------------------------------------------------------
# 4. API 데이터 요청 함수 (캐싱 적용)
# -----------------------------------------------------------------------------
# @st.cache_data(ttl=3600): 동일한 날짜 요청은 1시간(3600초) 동안 저장된 결과를 재사용합니다.
@st.cache_data(ttl=3600)
def fetch_box_office_data(key: str, date_str: str):
    url = "https://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json"
    params = {
        "key": key,
        "targetDt": date_str
    }
    # 10초 내 응답이 없으면 타임아웃 발생
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status() # HTTP 네트워크 오류 검사
    return response.json()

# -----------------------------------------------------------------------------
# 5. API 호출 및 오류 예외 처리
# -----------------------------------------------------------------------------
try:
    data = fetch_box_office_data(api_key, target_dt)

# 네트워크 연결 실패 또는 HTTP 상태 코드 오류 처리
except requests.exceptions.RequestException as net_err:
    st.error(
        "🌐 **KOBIS API 서버에 연결할 수 없습니다.**\n\n"
        "**[확인할 사항]**\n"
        "- 인터넷 연결 상태가 정상인지 확인해 주세요.\n"
        "- 영화진흥위원회(KOBIS) 서버가 점검 중일 수 있습니다.\n"
        f"- 상세 오류 정보: `{net_err}`"
    )
    st.stop()

# KOBIS 특유의 오류 응답 처리 (인증키 오류 등도 200 OK와 함께 faultInfo 상자로 응답됨)
if "faultInfo" in data:
    fault = data["faultInfo"]
    fault_msg = fault.get("message", "알 수 없는 오류")
    st.error(
        "⚠️ **KOBIS API 인증 및 요청 오류가 발생했습니다.**\n\n"
        f"- **오류 메시지:** {fault_msg}\n\n"
        "**[확인할 사항]**\n"
        "1. Secrets에 등록된 `KOBIS_KEY` 값이 정확한지 확인해 주세요.\n"
        "2. KOBIS 오픈 API 홈페이지에서 해당 인증키의 사용 승인 상태 및 일일 요청 한도를 확인해 주세요."
    )
    st.stop()

# 영화 데이터 목록 추출
box_office_result = data.get("boxOfficeResult", {})
daily_list = box_office_result.get("dailyBoxOfficeList", [])

# 영화 목록이 비어 있는 경우 예외 처리
if not daily_list:
    st.warning(
        f"⚠️ **{formatted_date} 박스오피스 집계 데이터가 없습니다.**\n\n"
        "**[확인할 사항]**\n"
        "- 아직 KOBIS 측에서 어제 자 박스오피스 집계를 완료하지 않았을 수 있습니다.\n"
        "- 일시적인 데이터 누락일 수 있으니 잠시 후 다시 접속해 주세요."
    )
    st.stop()

# -----------------------------------------------------------------------------
# 6. 데이터 전처리 (문자열 -> 숫자 타입 변환)
# -----------------------------------------------------------------------------
df = pd.DataFrame(daily_list)

# 숫자가 문자열 형태로 넘어오므로 정수(int) 타입으로 변환합니다.
numeric_columns = ['rank', 'audiCnt', 'audiAcc', 'scrnCnt', 'showCnt', 'salesAmt']
for col in numeric_columns:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

# 순위 기준 오름차순 정렬
df = df.sort_values(by='rank', ascending=True).reset_index(drop=True)

# -----------------------------------------------------------------------------
# 7. 1위 영화 지표 카드 (Metric Cards 3장)
# -----------------------------------------------------------------------------
top_movie = df.iloc[0]

st.subheader(f"🥇 어제 1위 영화: {top_movie['movieNm']}")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label="🎬 영화 제목 (개봉일)",
        value=top_movie['movieNm'],
        delta=f"개봉일: {top_movie['openDt']}",
        delta_color="off"
    )

with col2:
    st.metric(
        label="🎟️ 어제 관객수",
        value=f"{top_movie['audiCnt']:,} 명"
    )

with col3:
    st.metric(
        label="👥 누적 관객수",
        value=f"{top_movie['audiAcc']:,} 명"
    )

st.markdown("---")

# -----------------------------------------------------------------------------
# 8. 관객수 상위 5편 막대그래프
# -----------------------------------------------------------------------------
st.subheader("📊 관객수 상위 5편 영화")

# 상위 5개 데이터 추출
top5_df = df.head(5)[['movieNm', 'audiCnt']].copy()

# 막대그래프 시각화 (x축: 영화명, y축: 관객수)
st.bar_chart(
    top5_df,
    x="movieNm",
    y="audiCnt",
    x_label="영화명",
    y_label="당일 관객수(명)",
    use_container_width=True
)

st.markdown("---")

# -----------------------------------------------------------------------------
# 9. 전체 박스오피스 순위 표 (순위·영화명·개봉일·관객수·누적관객·스크린수)
# -----------------------------------------------------------------------------
st.subheader("📋 전체 박스오피스 순위")

# 요청받은 필수 컬럼 구성
df_display = df[['rank', 'movieNm', 'openDt', 'audiCnt', 'audiAcc', 'scrnCnt']].copy()

st.dataframe(
    df_display,
    column_config={
        "rank": st.column_config.NumberColumn("순위", format="%d위"),
        "movieNm": st.column_config.TextColumn("영화명"),
        "openDt": st.column_config.TextColumn("개봉일"),
        "audiCnt": st.column_config.NumberColumn("관객수", format="%d명"),
        "audiAcc": st.column_config.NumberColumn("누적관객", format="%d명"),
        "scrnCnt": st.column_config.NumberColumn("스크린수", format="%d개"),
    },
    hide_index=True,
    use_container_width=True
)
st.write("9/9 - ㅇㅇㅇㅇㅇ")
