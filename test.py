import streamlit as st
import pandas as pd
import json
import os
import requests # API 호출을 위한 라이브러리

# --- Constants ---
USER_DATA_FILE = 'users.json' # 사용자 정보를 저장할 파일

# TMDB API Key는 이제 필요 없으므로 제거 (혹은 주석 처리)
# TMDB_API_KEY = "YOUR_TMDB_API_KEY_HERE"

# Google Books API Key (선택 사항, 없어도 검색은 가능하나 요청 제한 있을 수 있음)
GOOGLE_BOOKS_API_KEY = "YOUR_GOOGLE_BOOKS_API_KEY_HERE"

# --- Helper Functions (기존 함수들 - 변경 없음) ---
def load_users():
    """사용자 데이터를 로드합니다."""
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_users(users):
    """사용자 데이터를 저장합니다."""
    with open(USER_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=4)

def authenticate_user(username, password):
    """사용자 인증을 시도합니다."""
    users = load_users()
    if username in users and users[username]['password'] == password:
        return True
    return False

def register_user(username, password):
    """새로운 사용자를 등록합니다."""
    users = load_users()
    if username in users:
        return False # 이미 존재하는 사용자
    users[username] = {'password': password}
    save_users(users)
    return True

# --- Modified Search Functions (수정된 부분) ---

def search_movies(query):
    """TMDB API를 이용해 영화를 검색합니다. (API Key 없이 시도)"""
    # 주의: API Key 없이 TMDB 검색 시, 접근이 불안정하거나 제한될 수 있습니다.
    # 안전한 사용을 위해서는 API Key를 발급받는 것이 좋습니다.
    url = f"https://api.themoviedb.org/3/search/movie"
    params = {
        # "api_key": TMDB_API_KEY, # <- API Key 제거
        "query": query,
        "language": "ko-KR"
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        results = response.json().get('results', [])
        return results
    else:
        st.error(f"영화 검색에 실패했습니다. (API Key 없이는 불안정할 수 있습니다.) 오류 코드: {response.status_code}")
        st.error(f"오류 메시지: {response.text}")
        return []

def search_books(query):
    """Google Books API를 이용해 책을 검색합니다."""
    url = f"https://www.googleapis.com/books/v1/volumes"
    params = {
        "q": query,
        "langRestrict": "ko" # 한국어로 검색 결과 제한
    }
    if GOOGLE_BOOKS_API_KEY: # API Key가 있다면 추가 (없어도 동작함)
        params["key"] = GOOGLE_BOOKS_API_KEY
        
    response = requests.get(url, params=params)
    if response.status_code == 200:
        results = response.json().get('items', [])
        return results
    else:
        st.error(f"책 검색에 실패했습니다. 오류 코드: {response.status_code}")
        st.error(f"오류 메시지: {response.text}")
        return []

def display_movie_result(movie):
    """검색된 영화 한 편을 텍스트로 표시합니다. (이미지 제거)"""
    title = movie.get('title')
    overview = movie.get('overview')
    # poster_path = movie.get('poster_path') # <- 이미지 관련 코드 제거
    release_date = movie.get('release_date')

    st.subheader(title)
    # if poster_path:
    #     st.image(f"https://image.tmdb.org/t/p/w200{poster_path}", caption=title)
    # else:
    #     st.image("https://via.placeholder.com/200x300?text=No+Poster", caption="포스터 없음")
    st.write(f"개봉일: {release_date}")
    st.write(f"줄거리: {overview if overview else '줄거리 정보가 없습니다.'}")
    st.button(f"'{title}' 기록하기", key=f"movie_record_{movie.get('id')}") # 기록 기능 버튼


def display_book_result(book):
    """검색된 책 한 권을 텍스트로 표시합니다. (이미지 제거)"""
    volume_info = book.get('volumeInfo', {})
    title = volume_info.get('title')
    authors = volume_info.get('authors', ['저자 미상'])
    description = volume_info.get('description')
    # thumbnail = volume_info.get('imageLinks', {}).get('thumbnail') # <- 이미지 관련 코드 제거
    published_date = volume_info.get('publishedDate')

    st.subheader(title)
    st.write(f"저자: {', '.join(authors)}")
    st.write(f"출판일: {published_date}")
    st.write(f"설명: {description[:200] + '...' if description and len(description) > 200 else (description if description else '설명 정보가 없습니다.')}")
    st.button(f"'{title}' 기록하기", key=f"book_record_{book.get('id')}") # 기록 기능 버튼


def render_search_page():
    """작품 검색 페이지를 렌더링합니다."""
    st.title("🔍 작품 검색 및 기록")

    # 영화/책 검색 선택
    search_type = st.radio("어떤 작품을 검색하시겠어요?", ["영화", "책"], horizontal=True)

    # 검색 폼
    with st.form(key="search_form"):
        search_query = st.text_input(f"{search_type} 제목을 입력해주세요:")
        search_button = st.form_submit_button(f"{search_type} 검색")

    if search_button and search_query:
        st.write(f"'{search_query}'(으)로 {search_type}을(를) 검색 중입니다...")
        if search_type == "영화":
            results = search_movies(search_query)
            if results:
                st.write(f"총 {len(results)}건의 영화를 찾았습니다.")
                for i, movie in enumerate(results):
                    st.expander(f"**{movie.get('title')} ({movie.get('release_date', '날짜 미상').split('-')[0]})**").write(display_movie_result(movie))
            else:
                st.info("검색 결과가 없습니다. 다른 검색어로 시도해보세요.")
        elif search_type == "책":
            results = search_books(search_query)
            if results:
                st.write(f"총 {len(results)}건의 책을 찾았습니다.")
                for i, book in enumerate(results):
                    volume_info = book.get('volumeInfo', {})
                    st.expander(f"**{volume_info.get('title')} ({volume_info.get('authors', ['저자 미상'])[0]})**").write(display_book_result(book))
            else:
                st.info("검색 결과가 없습니다. 다른 검색어로 시도해보세요.")
    elif search_button and not search_query:
        st.warning("검색어를 입력해주세요!")


# --- Streamlit App (main 함수 - 변경 없음) ---
def main():
    st.set_page_config(page_title="나만의 기록 앱", page_icon="📝", layout="wide")

    # st.session_state 초기화
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
    if 'username' not in st.session_state:
        st.session_state['username'] = None
    # 현재 선택된 페이지를 저장하기 위한 session_state 추가
    if 'current_page' not in st.session_state:
        st.session_state['current_page'] = "내 기록 보기" # 기본 페이지

    if st.session_state['logged_in']:
        # --- 로그인 성공 후 메인 페이지 ---
        st.sidebar.title(f"환영합니다, {st.session_state['username']}님! 👋")
        if st.sidebar.button("로그아웃 🚪"):
            st.session_state['logged_in'] = False
            st.session_state['username'] = None
            st.session_state['current_page'] = "내 기록 보기" # 로그아웃 시 페이지 초기화
            st.rerun()

        # 사이드바에서 페이지 선택 라디오 버튼
        st.sidebar.markdown("---")
        selected_page = st.sidebar.radio(
            "메뉴",
            ["📖 내 기록 보기", "🔍 작품 검색 및 기록", "✨ 인기 작품 보기"],
            key="main_menu_radio"
        )
        st.session_state['current_page'] = selected_page

        # 메인 콘텐츠 영역
        if st.session_state['current_page'] == "📖 내 기록 보기":
            st.title("📖 내 기록 보기")
            st.write(f"{st.session_state['username']}님의 소중한 기록들을 여기에 모아둘 거예요!")
            st.info("이곳에 영화/책 기록 목록이 표시될 예정입니다.")
        elif st.session_state['current_page'] == "🔍 작품 검색 및 기록":
            render_search_page()
        elif st.session_state['current_page'] == "✨ 인기 작품 보기":
            st.title("✨ 인기 작품 보기")
            st.write("지금 다른 사용자들이 어떤 작품에 관심을 가지고 있는지 보여주는 공간이 될 거예요!")
            st.info("인기 작품 목록은 나중에 구현될 예정입니다.")

    else:
        # --- 로그인/회원가입 페이지 (기존과 동일) ---
        st.title("📝 나만의 기록 앱 로그인/회원가입")
        st.subheader("계정이 있으시면 로그인해주세요.")

        with st.form("login_form"):
            username = st.text_input("사용자 이름 (ID)", key="login_username")
            password = st.text_input("비밀번호", type="password", key="login_password")
            login_button = st.form_submit_button("로그인")

            if login_button:
                if authenticate_user(username, password):
                    st.session_state['logged_in'] = True
                    st.session_state['username'] = username
                    st.success(f"{username}님, 환영합니다!")
                    st.rerun()
                else:
                    st.error("사용자 이름 또는 비밀번호가 잘못되었습니다.")

        st.subheader("새로운 계정을 만드시려면 회원가입해주세요.")

        with st.form("register_form"):
            new_username = st.text_input("새 사용자 이름 (ID)", key="register_new_username")
            new_password = st.text_input("새 비밀번호", type="password", key="register_new_password")
            register_button = st.form_submit_button("회원가입")

            if register_button:
                if register_user(new_username, new_password):
                    st.success(f"'{new_username}' 계정이 성공적으로 생성되었습니다! 이제 로그인해주세요.")
                else:
                    st.error(f"'{new_username}'은 이미 존재하는 사용자 이름입니다. 다른 이름을 사용해주세요.")

if __name__ == "__main__":
    main()
