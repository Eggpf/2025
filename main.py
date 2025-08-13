import streamlit as st

# 페이지 설정
st.set_page_config(
    page_title="똑똑한 재활용 도우미",
    page_icon="♻️",
    layout="centered"
)

# --- 스타일링 (친환경적 느낌) ---
# Streamlit의 기본 스타일을 오버라이드하여 디자인을 꾸밉니다.
st.markdown("""
<style>
    /* 제목 및 부제목 색상 */
    h1, h2, h3 {
        color: #2e7d32;
    }
    /* 메인 컨테이너 - 배경색과 둥근 모서리 */
    .st-emotion-cache-1g6go4k {
        background-color: #f4f8f2;
        padding: 2rem;
        border-radius: 10px;
    }
    /* 검색창 - 테두리와 둥근 모서리 */
    .st-emotion-cache-1cypcdb {
        border: 2px solid #a5d6a7;
        border-radius: 8px;
    }
    /* 성공/정보/오류 메시지 - 색상 변경 */
    .st-success > div {
        background-color: #e8f5e9;
        color: #1b5e20;
    }
    .st-info > div {
        background-color: #f1f8e9;
        color: #388e3c;
    }
    .st-error > div {
        background-color: #ffebee;
        color: #d32f2f;
    }
</style>
""", unsafe_allow_html=True)

# --- 헤더 섹션 ---
st.title("🌱 똑똑한 재활용 도우미 ♻️")
st.write("지구를 위한 첫걸음! 🌍 궁금한 재활용 쓰레기의 이름을 검색해 보세요.")
st.markdown("---")

# --- 재활용 데이터 (딕셔너리) ---
recycling_data = {
    "페트병": "💧 내용물을 비우고 라벨을 제거한 후 찌그러뜨려 압축해서 배출합니다.",
    "우유팩": "🥛 내용물을 비우고 물로 헹군 후 말려서 펼쳐서 배출합니다. 일반 종이와 분리해서 버려야 합니다.",
    "건전지": "🔋 가까운 주민센터나 아파트의 폐건전지 수거함에 버립니다.",
    "유리병": "🍾 내용물을 비우고 뚜껑을 제거한 후 배출합니다. 깨진 유리는 종량제 봉투에 버려야 합니다.",
    "계란판": "🥚 종이 재질이므로 다른 종이류와 함께 배출합니다.",
    "아이스팩": "🧊 내용물(고흡수성 폴리머)은 하수구에 버리면 막힐 수 있으므로, 뜯지 않고 종량제 봉투에 버립니다.",
    "종이컵": "☕️ 종이컵 전용 수거함에 분리 배출합니다. 물로 헹구고 완전히 건조하는 것이 좋습니다.",
    "헌 옷": "👕 의류 수거함에 배출합니다. 신발이나 가방 등도 가능하지만, 솜이불, 베개 등은 불가능합니다.",
    "고무장갑": "🧤 재활용이 안 되므로 일반 쓰레기(종량제 봉투)로 버려야 합니다."
}

# --- 검색 기능 섹션 ---
search_query = st.text_input("🔍 검색", placeholder="예: 페트병, 아이스팩, 고무장갑")

# 검색 결과 표시
if search_query:
    result = recycling_data.get(search_query)
    if result:
        st.success(f"✅ **{search_query}** 재활용 방법")
        st.info(result)
    else:
        # 사용자의 입력과 유사한 단어를 찾기 위한 간단한 로직 추가
        found_similar = False
        for key in recycling_data.keys():
            if search_query in key or key in search_query:
                st.warning(f"⚠️ '{search_query}'에 대한 정보는 없지만, **'{key}'** 관련 정보가 있을 수 있습니다.")
                found_similar = True
                break
        
        if not found_similar:
            st.error(f"❌ **'{search_query}'**에 대한 정보를 찾을 수 없습니다. 정확한 검색어를 입력하거나 다른 단어를 시도해 보세요.")

st.markdown("---")

# --- 꿀팁 섹션 ---
st.subheader("🍀 재활용 꿀팁")
st.write("분리수거는 깨끗하게, 올바르게! 😊")
st.write("궁금한 재활용품이 있다면 언제든지 검색해 보세요! 🌱")
