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
    page_title="일별 박스오피스 조회",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 일별 박스오피스 순위 조회")

# -----------------------------------------------------------------------------
# 2. 한국 시간(KST: UTC+9) 기준 날짜 선택 기능
# -----------------------------------------------------------------------------
# 배포 서버의 시각과 관계없이 한국 시간(KST)을 정확히 계산합니다.
KST = timezone(timedelta(hours=9))
today_kst = datetime.now(KST).date()
yesterday_kst = today_kst - timedelta(days=1)

# 달력(st.date_input)으로 날짜를 선택하되, 가장 늦은 날짜를 '어제'로 제한합니다.
selected_date = st.date_input(
    "📅 조회할 날짜를 선택하세요 (최대 어제 날짜까지 선택 가능)",
    value=yesterday_kst,
    max_value=yesterday_kst,
    help="오늘 자 박스오피스 데이터는 아직 집계 전이므로 선택할 수 없습니다."
)

# API 요청용 여덟 자리 문자열 (예: "20260908")
target_dt = selected_date.strftime("%Y%m%d")
# 화면 표기용 문자열 (예: "2026년 09월 08일")
formatted_date = selected_date.strftime("%Y년 %m월 %d일")

st.caption(f"**조회 기준일:** {formatted_date}")

# -----------------------------------------------------------------------------
# 3. 비밀 금고(Secrets)에서 API 키 불러오기
# -----------------------------------------------------------------------------
if "KOBIS_KEY" not in st.secrets:
    st.error(
        "🔑 **API 인증키(KOBIS_KEY)를 찾을 수 없습니다.**\n\n"
        "**[해결 방법]**\n"
        "1. Streamlit Cloud 앱 설정의 **[Settings] -> [Secrets]** 메뉴로 이동하세요.\n"
        "2. 아래와 같이 KOBIS 인증키를 작성하고 저장해 주세요.\n"
        "   ```toml\n"
        '   KOBIS_KEY = "발급받은_인증키_문자열"\n'
        "   ```"
    )
    st.stop()

api_key = st.secrets["KOBIS_KEY"]

# -----------------------------------------------------------------------------
# 4. API 데이터 요청 및 캐싱 (1시간 기억)
# -----------------------------------------------------------------------------
# @st.cache_data(ttl=3600): 동일한 날짜로 다시 요청하면 API를 부르지 않고 1시간 동안 저장된 결과를 재사용합니다.
@st.cache_data(ttl=3600)
def fetch_box_office_data(key: str, date_str: str):
    url = "https://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json"
    params = {
        "key": key,
        "targetDt": date_str
    }
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    return response.json()

# -----------------------------------------------------------------------------
# 5. API 호출 및 오류 예외 처리
# -----------------------------------------------------------------------------
try:
    data = fetch_box_office_data(api_key, target_dt)

except requests.exceptions.RequestException as net_err:
    st.error(
        "🌐 **KOBIS API 서버에 연결할 수 없습니다.**\n\n"
        "**[확인할 사항]**\n"
        "- 인터넷 연결 상태를 확인해 주세요.\n"
        "- 영화진흥위원회 서버 점검 중일 수 있습니다.\n"
        f"- 상세 오류 내용: `{net_err}`"
    )
    st.stop()

# 인증키 오류 등 KOBIS에서 faultInfo 상자를 보내오는 경우 처리
if "faultInfo" in data:
    fault = data["faultInfo"]
    fault_msg = fault.get("message", "알 수 없는 오류")
    st.error(
        "⚠️ **KOBIS API 인증 및 요청 오류가 발생했습니다.**\n\n"
        f"- **오류 메시지:** {fault_msg}\n\n"
        "**[확인할 사항]**\n"
        "1. Secrets에 입력한 `KOBIS_KEY` 값이 정확한지 확인해 주세요.\n"
        "2. KOBIS 오픈 API 마이페이지에서 키의 승인 상태 및 일일 사용량을 확인해 주세요."
    )
    st.stop()

# 영화 데이터 목록 추출
box_office_result = data.get("boxOfficeResult", {})
daily_list = box_office_result.get("dailyBoxOfficeList", [])

# 영화 목록이 비어 있을 때 안내 문구
if not daily_list:
    st.warning(f"⚠️ **{formatted_date}**: 그날은 아직 집계 전입니다.")
    st.stop()

# -----------------------------------------------------------------------------
# 6. 데이터 전처리 (문자열 -> 숫자 변환, 증감 표시, 100만 관객 트로피)
# -----------------------------------------------------------------------------
df = pd.DataFrame(daily_list)

# 문자열 숫자를 정수(int)형으로 변환합니다.
numeric_columns = ['rank', 'rankInten', 'audiCnt', 'audiAcc', 'scrnCnt', 'showCnt', 'salesAmt']
for col in numeric_columns:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

# 순위 기준 오름차순 정렬
df = df.sort_values(by='rank', ascending=True).reset_index(drop=True)

# 1) 누적관객 100만 명 이상 영화 이름 옆에 트로피 이모지(🏆) 추가
def process_movie_name(row):
    name = row['movieNm']
    if row['audiAcc'] >= 1_000_000:
        return f"{name} 🏆"
    return name

df['display_movieNm'] = df.apply(process_movie_name, axis=1)

# 2) 전날 대비 순위 증감(rankInten) 표시 처리
# - 양수(오름): 빨간 위 화살표
# - 음수(내림): 파란 아래 화살표
def format_rank_change(val):
    if val > 0:
        return f"🔴 ▲{val}"
    elif val < 0:
        return f"🔵 ▼{abs(val)}"
    else:
        return "-"

df['rank_change_display'] = df['rankInten'].apply(format_rank_change)

# -----------------------------------------------------------------------------
# 7. 1위 영화 지표 카드 (Metric Cards 3장)
# -----------------------------------------------------------------------------
top_movie = df.iloc[0]

st.subheader(f"🥇 1위 영화: {top_movie['display_movieNm']}")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label="🎬 영화 제목",
        value=top_movie['display_movieNm'],
        delta=f"개봉일: {top_movie['openDt']}",
        delta_color="off"
    )

with col2:
    st.metric(
        label="🎟️ 당일 관객수",
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
st.subheader("📊 관객수 상위 5편")

top5_df = df.head(5)[['display_movieNm', 'audiCnt']].copy()

st.bar_chart(
    top5_df,
    x="display_movieNm",
    y="audiCnt",
    x_label="영화명",
    y_label="당일 관객수(명)",
    use_container_width=True
)

st.markdown("---")

# -----------------------------------------------------------------------------
# 9. 전체 박스오피스 순위 표
# -----------------------------------------------------------------------------
st.subheader("📋 박스오피스 상세 순위")

# 표에 표시할 컬럼 정리
df_display = df[[
    'rank', 'rank_change_display', 'display_movieNm', 'openDt', 'audiCnt', 'audiAcc', 'scrnCnt'
]].copy()

st.dataframe(
    df_display,
    column_config={
        "rank": st.column_config.NumberColumn("순위", format="%d위"),
        "rank_change_display": st.column_config.TextColumn("전날 대비"),
        "display_movieNm": st.column_config.TextColumn("영화명"),
        "openDt": st.column_config.TextColumn("개봉일"),
        "audiCnt": st.column_config.NumberColumn("관객수", format="%d명"),
        "audiAcc": st.column_config.NumberColumn("누적관객", format="%d명"),
        "scrnCnt": st.column_config.NumberColumn("스크린수", format="%d개"),
    },
    hide_index=True,
    use_container_width=True
)
