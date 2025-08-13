import streamlit as st

st.set_page_config(page_title="똑똑한 재활용 도우미")

st.title("똑똑한 재활용 도우미 ♻️")
st.write("궁금한 재활용 쓰레기의 이름을 검색해 보세요.")
recycling_data = {
    "페트병": "내용물을 비우고 라벨을 제거한 후 찌그러뜨려 압축해서 배출합니다.",
    "우유팩": "내용물을 비우고 물로 헹군 후 말려서 펼쳐서 배출합니다. 일반 종이와 분리해서 버려야 합니다.",
    "건전지": "가까운 주민센터나 아파트의 폐건전지 수거함에 버립니다.",
    "유리병": "내용물을 비우고 뚜껑을 제거한 후 배출합니다. 깨진 유리는 종량제 봉투에 버려야 합니다.",
    "계란판": "종이 재질이므로 다른 종이류와 함께 배출합니다.",
    "아이스팩": "내용물(고흡수성 폴리머)은 하수구에 버리면 막힐 수 있으므로, 뜯지 않고 종량제 봉투에 버립니다."
}
# 위에서 만든 recycling_data 딕셔너리 아래에 추가
search_query = st.text_input("검색", placeholder="예: 페트병, 아이스팩")

if search_query:
    # 딕셔너리에서 검색
    if search_query in recycling_data:
        st.success(f"**{search_query}** 재활용 방법")
        st.info(recycling_data[search_query])
    else:
        st.error(f"**{search_query}**에 대한 정보를 찾을 수 없습니다. 다른 검색어를 시도해 보세요.")
