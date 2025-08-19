import streamlit as st
import pandas as pd
import json
import os
import requests # API 호출을 위한 라이브러리
from datetime import datetime # 기록 날짜를 위해 추가

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

# --- New Functions for User Records ---
def get_user_records_file(username):
    """사용자별 기록 파일 경로를 반환합니다."""
    return f'{username}_records.json'

def load_user_records(username):
    """특정 사용자의 기록을 로드합니다."""
    records_file = get_user_records_file(username)
    if os.path.exists(records_file):
        with open(records_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return [] # 파일이 없으면 빈 리스트 반환

def save_user_records(username, records):
    """특정 사용자의 기록을 저장합니다."""
    records_file = get_user_records_file(username)
    with open(records_file, 'w', encoding='utf-8') as f:
        json.dump(records, f, indent=4, ensure_ascii=False) # 한글 인코딩 문제 방지


# --- Search Functions (기존과 동일하게 유지하거나 필요에 따라 API KEY 제거) ---

def search_movies(query):
    """TMDB API를 이용해 영화를 검색합니다. (API Key 없이 시도)"""
    # TMDB는 API 키 없이는 대부분의 기능을 제대로 사용할 수 없습니다.
    # 이 함수는 예시를 위한 것으로, 실제 사용시에는 API 키 발급이 권장됩니다.
    url = f"https://api.themoviedb.org/3/search/movie"
    params = {
        # "api_key": TMDB_API_KEY, # 실제 사용시 여기에 API KEY를 넣어야 함
        "query": query,
        "language": "ko-KR"
    }
    try:
        response = requests.get(url, params=params, timeout=5) # 타임아웃 추가
        if response.status_code == 200:
            results = response.json().get('results', [])
            return results
        else:
            st.warning(f"영화 검색에 실패했습니다 (코드: {response.status_code}). API Key 없이는 불안정할 수 있습니다. 수동 입력을 이용해보세요.")
            return []
    except requests.exceptions.RequestException as e:
        st.warning(f"영화 검색 요청 중 오류 발생: {e}. 인터넷 연결 또는 API 문제일 수 있습니다. 수동 입력을 이용해보세요.")
        return []

def search_books(query):
    """Google Books API를 이용해 책을 검색합니다."""
    url = f"https://www.googleapis.com/books/v1/volumes"
    params = {
        "q": query,
        "langRestrict": "ko"
    }
    if GOOGLE_BOOKS_API_KEY:
        params["key"] = GOOGLE_BOOKS_API_KEY
    
    try:
        response = requests.get(url, params=params, timeout=5) # 타임아웃 추가
        if response.status_code == 200:
            results = response.json().get('items', [])
            return results
        else:
            st.warning(f"책 검색에 실패했습니다 (코드: {response.status_code}). 수동 입력을 이용해보세요.")
            return []
    except requests.exceptions.RequestException as e:
        st.warning(f"책 검색 요청 중 오류 발생: {e}. 인터넷 연결 또는 API 문제일 수 있습니다. 수동 입력을 이용해보세요.")
        return []

# --- Display Search Results (수정: 이미지 대신 텍스트만) ---

def display_movie_result(movie):
    """검색된 영화 한 편을 텍스트로 표시합니다."""
    title = movie.get('title')
    overview = movie.get('overview')
    release_date = movie.get('release_date')
    poster_path = movie.get('poster_path') # API에 남아있을 수 있으므로 받아는 둡니다.

    st.subheader(title)
    st.write(f"개봉일: {release_date}")
    st.write(f"줄거리: {overview if overview else '줄거리 정보가 없습니다.'}")
    
    # 기록하기 버튼 클릭 시 수동 입력 폼으로 해당 정보 미리 채우기
    if st.button(f"'{title}' 정보로 기록하기", key=f"movie_record_{movie.get('id')}"):
        st.session_state['manual_entry_title'] = title
        st.session_state['manual_entry_type'] = '영화'
        st.session_state['manual_entry_director_author'] = '' # 감독 정보는 별도로 필요시 TMDB에서 다시 가져와야 함 (간단하게 일단 비움)
        st.session_state['manual_entry_release_pub_date'] = release_date
        # 포스터 URL이 API에 있다면 이것을 이용
        if poster_path:
            st.session_state['manual_entry_image_url'] = f"https://image.tmdb.org/t/p/w200{poster_path}"
        else:
            st.session_state['manual_entry_image_url'] = ''
        st.session_state['manual_entry_summary'] = overview # 줄거리를 감상평 요약으로
        st.session_state['current_page'] = "🔍 작품 검색 및 기록" # 현재 페이지 유지
        st.session_state['manual_entry_mode'] = True # 수동 입력 모드 활성화 (폼 펼치기)
        st.rerun()


def display_book_result(book):
    """검색된 책 한 권을 텍스트로 표시합니다."""
    volume_info = book.get('volumeInfo', {})
    title = volume_info.get('title')
    authors = volume_info.get('authors', ['저자 미상'])
    description = volume_info.get('description')
    thumbnail = volume_info.get('imageLinks', {}).get('thumbnail') # API에 남아있을 수 있으므로 받아는 둡니다.
    published_date = volume_info.get('publishedDate')

    st.subheader(title)
    st.write(f"저자: {', '.join(authors)}")
    st.write(f"출판일: {published_date}")
    st.write(f"설명: {description[:200] + '...' if description and len(description) > 200 else (description if description else '설명 정보가 없습니다.')}")
    
    # 기록하기 버튼 클릭 시 수동 입력 폼으로 해당 정보 미리 채우기
    if st.button(f"'{title}' 정보로 기록하기", key=f"book_record_{book.get('id')}"):
        st.session_state['manual_entry_title'] = title
        st.session_state['manual_entry_type'] = '책'
        st.session_state['manual_entry_director_author'] = ', '.join(authors)
        st.session_state['manual_entry_release_pub_date'] = published_date
        st.session_state['manual_entry_image_url'] = thumbnail if thumbnail else ''
        st.session_state['manual_entry_summary'] = description # 설명을 감상평 요약으로
        st.session_state['current_page'] = "🔍 작품 검색 및 기록" # 현재 페이지 유지
        st.session_state['manual_entry_mode'] = True # 수동 입력 모드 활성화 (폼 펼치기)
        st.rerun()

# --- New Manual Entry Page ---
def render_manual_entry_form(username):
    st.subheader("📝 작품 수동 기록하기")
    st.info("검색되지 않거나 직접 입력하고 싶은 작품의 정보를 기록해보세요. 이미지 URL을 넣으면 포스터/표지도 함께 볼 수 있습니다!")

    with st.form("manual_record_form"):
        # 기존 세션 스테이트에서 값 불러오기 (검색 결과에서 가져왔을 경우)
        default_title = st.session_state.get('manual_entry_title', '')
        default_type = st.session_state.get('manual_entry_type', '영화')
        default_director_author = st.session_state.get('manual_entry_director_author', '')
        default_release_pub_date = st.session_state.get('manual_entry_release_pub_date', '')
        default_image_url = st.session_state.get('manual_entry_image_url', '')
        default_summary = st.session_state.get('manual_entry_summary', '')
        
        col_type, col_title = st.columns([0.2, 0.8])
        record_type = col_type.radio("종류", ["영화", "책"], horizontal=True, key="manual_type_radio", index=0 if default_type == '영화' else 1)
        title = col_title.text_input("제목", value=default_title, key="manual_title")
        
        col_maker_date = st.columns(2)
        director_author = col_maker_date[0].text_input(
            f"{'감독' if record_type == '영화' else '저자'}", 
            value=default_director_author, 
            key="manual_director_author"
        )
        release_pub_date = col_maker_date[1].text_input(
            f"{'개봉일' if record_type == '영화' else '출판일'}", 
            help="예: 2023-01-15 또는 2023", 
            value=default_release_pub_date, 
            key="manual_release_pub_date"
        )

        genre = st.text_input("장르 (예: 판타지, 로맨스, SF)", key="manual_genre")
        
        image_url = st.text_input("이미지 URL (포스터/표지 URL을 직접 입력하세요)", value=default_image_url, key="manual_image_url")
        if image_url:
            st.image(image_url, width=150, caption="미리보기") # 이미지 미리보기
        
        rating = st.slider("나의 평점 (1점은 최악, 5점은 최고)", 1, 5, 3, key="manual_rating")
        review = st.text_area("나의 감상/기록", value=default_summary, key="manual_review")

        save_button = st.form_submit_button("이 작품 기록 저장하기 ✅")

        if save_button:
            if not title:
                st.error("제목은 필수로 입력해야 합니다!")
                return
            
            # 새 기록 데이터 구성
            new_record = {
                "id": str(datetime.now().timestamp()), # 고유 ID 생성 (나중에 편집/삭제에 사용)
                "type": record_type,
                "title": title,
                "director_author": director_author,
                "release_pub_date": release_pub_date,
                "genre": genre,
                "image_url": image_url,
                "rating": rating,
                "review": review,
                "recorded_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            records = load_user_records(username)
            records.append(new_record)
            save_user_records(username, records)
            st.success(f"'{title}' 작품 기록이 성공적으로 저장되었습니다!")
            
            # 입력 폼 초기화 (검색 결과에서 가져온 값도 초기화)
            st.session_state['manual_entry_title'] = ''
            st.session_state['manual_entry_type'] = '영화'
            st.session_state['manual_entry_director_author'] = ''
            st.session_state['manual_entry_release_pub_date'] = ''
            st.session_state['manual_entry_image_url'] = ''
            st.session_state['manual_entry_summary'] = ''
            st.session_state['manual_entry_mode'] = False # 폼 접기
            st.rerun() # 화면 새로고침하여 초기화된 폼 보여주기

# --- Main Search and Record Page ---
def render_search_and_record_page():
    """작품 검색 및 기록 페이지를 렌더링합니다."""
    st.title("🔍 작품 검색 및 기록")
    
    # 세션 스테이트를 이용해 수동 입력 폼의 Expander 상태 제어
    # 'manual_entry_mode'가 True면 열려있도록 설정 (검색 결과로부터 정보 채우기 등)
    if 'manual_entry_mode' not in st.session_state:
        st.session_state['manual_entry_mode'] = False

    # 탭 또는 라디오 버튼 대신, 섹션을 나누는 방식으로
    st.header("온라인 검색으로 찾기")
    search_type = st.radio("어떤 작품을 검색하시겠어요?", ["영화", "책"], horizontal=True, key="search_type_radio")
    
    with st.form(key="online_search_form"):
        search_query = st.text_input(f"{search_type} 제목을 입력해주세요:")
        search_button = st.form_submit_button(f"{search_type} 검색")

    if search_button and search_query:
        st.write(f"'{search_query}'(으)로 {search_type}을(를) 검색 중입니다...")
        if search_type == "영화":
            results = search_movies(search_query)
            if results:
                st.write(f"총 {len(results)}건의 영화를 찾았습니다.")
                for i, movie in enumerate(results):
                    with st.expander(f"**{movie.get('title')} ({movie.get('release_date', '날짜 미상').split('-')[0]})**"):
                        display_movie_result(movie)
            else:
                st.info("검색 결과가 없습니다. 직접 기록하기를 이용해보세요.")
        elif search_type == "책":
            results = search_books(search_query)
            if results:
                st.write(f"총 {len(results)}건의 책을 찾았습니다.")
                for i, book in enumerate(results):
                    volume_info = book.get('volumeInfo', {})
                    with st.expander(f"**{volume_info.get('title')} ({volume_info.get('authors', ['저자 미상'])[0]})**"):
                        display_book_result(book)
            else:
                st.info("검색 결과가 없습니다. 직접 기록하기를 이용해보세요.")
    elif search_button and not search_query:
        st.warning("검색어를 입력해주세요!")
        
    st.markdown("---") # 구분선

    # 수동 입력 폼을 Expander로 감싸서 필요할 때만 보이게
    manual_entry_expander = st.expander(
        "혹은 직접 기록하기 ✍️", 
        expanded=st.session_state['manual_entry_mode']
    )
    with manual_entry_expander:
        render_manual_entry_form(st.session_state['username'])
        
# --- Streamlit App (main 함수 수정) ---
def main():
    st.set_page_config(page_title="나만의 기록 앱", page_icon="📝", layout="wide")

    # st.session_state 초기화
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
    if 'username' not in st.session_state:
        st.session_state['username'] = None
    if 'current_page' not in st.session_state:
        st.session_state['current_page'] = "📖 내 기록 보기" # 기본 페이지

    # 수동 입력 폼의 미리 채울 값들을 위한 세션 스테이트 초기화 (맨 위로 이동)
    if 'manual_entry_title' not in st.session_state: st.session_state['manual_entry_title'] = ''
    if 'manual_entry_type' not in st.session_state: st.session_state['manual_entry_type'] = '영화'
    if 'manual_entry_director_author' not in st.session_state: st.session_state['manual_entry_director_author'] = ''
    if 'manual_entry_release_pub_date' not in st.session_state: st.session_state['manual_entry_release_pub_date'] = ''
    if 'manual_entry_image_url' not in st.session_state: st.session_state['manual_entry_image_url'] = ''
    if 'manual_entry_summary' not in st.session_state: st.session_state['manual_entry_summary'] = ''
    # Expander 상태를 위한 session_state도 초기화
    if 'manual_entry_mode' not in st.session_state:
        st.session_state['manual_entry_mode'] = False


    if st.session_state['logged_in']:
        # --- 로그인 성공 후 메인 페이지 ---
        st.sidebar.title(f"환영합니다, {st.session_state['username']}님! 👋")
        if st.sidebar.button("로그아웃 🚪"):
            st.session_state['logged_in'] = False
            st.session_state['username'] = None
            st.session_state['current_page'] = "📖 내 기록 보기" # 로그아웃 시 페이지 초기화
            st.session_state['manual_entry_mode'] = False # 수동 입력 모드도 초기화
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
            # --- 사용자의 기록 표시 ---
            user_records = load_user_records(st.session_state['username'])
            if user_records:
                st.write(f"{st.session_state['username']}님의 소중한 기록들을 보여드릴게요.")
                for i, record in enumerate(user_records):
                    with st.expander(f"{record.get('title')} ({record.get('recorded_date').split(' ')[0]})"):
                        st.write(f"**종류:** {record.get('type')}")
                        st.write(f"**제목:** {record.get('title')}")
                        if record.get('director_author'):
                            st.write(f"**{'감독' if record.get('type')=='영화' else '저자'}:** {record.get('director_author')}")
                        if record.get('release_pub_date'):
                            st.write(f"**{'개봉일' if record.get('type')=='영화' else '출판일'}:** {record.get('release_pub_date')}")
                        if record.get('genre'):
                            st.write(f"**장르:** {record.get('genre')}")
                        
                        if record.get('image_url'):
                            try:
                                st.image(record.get('image_url'), width=200, caption=f"'{record.get('title')}' 포스터/표지")
                            except Exception as e:
                                st.warning(f"이미지를 불러올 수 없습니다: {e}")
                                st.text(f"URL: {record.get('image_url')}")
                        
                        st.write(f"**나의 평점:** {'⭐' * record.get('rating')} ({record.get('rating')}점)")
                        st.write(f"**나의 감상:** {record.get('review')}")
                        st.write(f"기록일: {record.get('recorded_date')}")

                        # 나중에 기록 편집/삭제 기능도 추가할 수 있어요.
            else:
                st.info(f"{st.session_state['username']}님의 기록이 아직 없습니다. '작품 검색 및 기록'에서 새로운 작품을 추가해보세요!")


        elif st.session_state['current_page'] == "🔍 작품 검색 및 기록":
            render_search_and_record_page() # 함수 이름 변경
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
