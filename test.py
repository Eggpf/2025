import streamlit as st
import json
import os
import requests
from datetime import datetime
import uuid # 고유 ID 생성을 위해 추가

# --- Constants ---
USER_DATA_FILE = 'users.json' # 사용자 정보를 저장할 파일
SHARING_ROOMS_FILE = 'sharing_rooms.json' # 공유방 정보를 저장할 파일

# Google Books API Key (선택 사항)
# 발급받으셨다면 여기에 넣어주세요. 없어도 책 검색은 작동할 수 있습니다.
GOOGLE_BOOKS_API_KEY = "YOUR_GOOGLE_BOOKS_API_KEY_HERE"

# --- Helper Functions (사용자 및 기록 파일 관리) ---
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

# --- Functions for Sharing Rooms ---
def load_sharing_rooms():
    """공유방 데이터를 로드합니다."""
    if os.path.exists(SHARING_ROOMS_FILE):
        with open(SHARING_ROOMS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {} # {room_id: room_data, ...} 형태

def save_sharing_rooms(rooms):
    """공유방 데이터를 저장합니다."""
    with open(SHARING_ROOMS_FILE, 'w', encoding='utf-8') as f:
        json.dump(rooms, f, indent=4, ensure_ascii=False)

def create_sharing_room(creator_username, room_name, room_password, shared_record_ids):
    """새로운 공유방을 생성하고 저장합니다."""
    rooms = load_sharing_rooms()
    room_id = str(uuid.uuid4()) # 고유한 방 ID 생성
    
    rooms[room_id] = {
        "room_name": room_name,
        "creator_username": creator_username,
        "room_password": room_password, # 평문으로 저장 (보안 강화를 위해선 해싱 필요)
        "shared_record_ids": shared_record_ids,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    save_sharing_rooms(rooms)
    return room_id

def get_sharing_room(room_id):
    """특정 공유방 정보를 가져옵니다."""
    rooms = load_sharing_rooms()
    return rooms.get(room_id)

# --- Search Functions ---
def search_movies(query):
    """TMDB API를 이용해 영화를 검색합니다. (API Key 없어도 작동 시도)"""
    # TMDB는 API 키 없이는 대부분의 기능을 제대로 사용할 수 없습니다.
    # 이 함수는 예시를 위한 것으로, 실제 사용시에는 API 키 발급이 권장됩니다.
    url = f"https://api.themoviedb.org/3/search/movie"
    params = {
        # "api_key": "YOUR_TMDB_API_KEY_HERE", # 실제 TMDB API Key를 발급받으면 여기에 입력
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
    if GOOGLE_BOOKS_API_KEY and GOOGLE_BOOKS_API_KEY != "YOUR_GOOGLE_BOOKS_API_KEY_HERE":
        params["key"] = GOOGLE_BOOKS_API_KEY
    
    try:
        response = requests.get(url, params=params, timeout=5) # 타임아웃 추가
        if response.status_code == 200:
            return response.json().get('items', [])
        else:
            st.warning(f"책 검색에 실패했습니다 (코드: {response.status_code}). 수동 입력을 이용해보세요.")
            return []
    except requests.exceptions.RequestException as e:
        st.warning(f"책 검색 요청 중 오류 발생: {e}. 인터넷 연결 또는 API 문제일 수 있습니다. 수동 입력을 이용해보세요.")
        return []

# --- Display Search Results & Pre-fill Manual Form ---
def display_movie_result(movie):
    """검색된 영화 정보를 표시하고 기록하기 버튼으로 수동 입력 폼을 채웁니다."""
    title = movie.get('title')
    overview = movie.get('overview')
    release_date = movie.get('release_date')
    poster_path = movie.get('poster_path')

    st.subheader(title)
    st.write(f"개봉일: {release_date}")
    st.write(f"줄거리: {overview if overview else '줄거리 정보가 없습니다.'}")
    if st.button(f"'{title}' 정보로 기록하기", key=f"movie_record_{movie.get('id')}"):
        st.session_state['manual_entry_title'] = title
        st.session_state['manual_entry_type'] = '영화'
        st.session_state['manual_entry_director_author'] = '' 
        st.session_state['manual_entry_release_pub_date'] = release_date
        st.session_state['manual_entry_image_url'] = f"https://image.tmdb.org/t/p/w200{poster_path}" if poster_path else ''
        st.session_state['manual_entry_summary'] = overview 
        st.session_state['manual_entry_mode'] = True
        st.session_state['current_page'] = "🔍 작품 검색 및 기록" # 현재 페이지 유지
        st.rerun()

def display_book_result(book):
    """검색된 책 정보를 표시하고 기록하기 버튼으로 수동 입력 폼을 채웁니다."""
    volume_info = book.get('volumeInfo', {})
    title = volume_info.get('title')
    authors = volume_info.get('authors', ['저자 미상'])
    description = volume_info.get('description')
    thumbnail = volume_info.get('imageLinks', {}).get('thumbnail')
    published_date = volume_info.get('publishedDate')

    st.subheader(title)
    st.write(f"저자: {', '.join(authors)}")
    st.write(f"출판일: {published_date}")
    st.write(f"설명: {description[:200] + '...' if description and len(description) > 200 else (description if description else '설명 정보가 없습니다.')}")
    if st.button(f"'{title}' 정보로 기록하기", key=f"book_record_{book.get('id')}"):
        st.session_state['manual_entry_title'] = title
        st.session_state['manual_entry_type'] = '책'
        st.session_state['manual_entry_director_author'] = ', '.join(authors)
        st.session_state['manual_entry_release_pub_date'] = published_date
        st.session_state['manual_entry_image_url'] = thumbnail if thumbnail else ''
        st.session_state['manual_entry_summary'] = description
        st.session_state['manual_entry_mode'] = True
        st.session_state['current_page'] = "🔍 작품 검색 및 기록" # 현재 페이지 유지
        st.rerun()

# --- Manual Entry Form ---
def render_manual_entry_form(username):
    """사용자가 직접 작품 정보를 입력하고 저장하는 폼을 렌더링합니다."""
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
                "id": str(uuid.uuid4()), # 고유 ID 생성 (UUID 사용)
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
    
    if 'manual_entry_mode' not in st.session_state:
        st.session_state['manual_entry_mode'] = False

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

# --- Sharing Room Creation Page ---
def render_create_sharing_room_page(username):
    st.title("🎉 새 감상 공유방 만들기")
    st.info("나만의 감상 공유방을 만들고 친구들에게 링크를 공유해보세요!")

    # 성공 메시지 및 링크를 보여줄 placeholder 설정 (폼 바깥에서 관리)
    success_message_placeholder = st.empty() 

    user_records = load_user_records(username)
    if not user_records:
        st.warning("공유할 기록물이 없습니다. '작품 검색 및 기록'에서 먼저 기록을 추가해주세요!")
        if 'sharing_success_info' in st.session_state:
            del st.session_state['sharing_success_info']
        return

    st.subheader(f"✨ {username}님의 기록물")
    record_options = [(f"{r['title']} ({r['recorded_date'].split(' ')[0]})", r['id']) for r in user_records]
    
    # st.multiselect의 value가 항상 list 타입이 되도록 보장
    # clear_sharing_multiselect 플래그가 True면 빈 리스트로 초기화, 아니면 현재 선택된 값 (세션 상태에서 가져옴)
    current_multiselect_value = []
    if st.session_state.get('clear_sharing_multiselect', False):
        current_multiselect_value = []
        st.session_state['clear_sharing_multiselect'] = False 
    elif 'sharing_multiselect' in st.session_state:
        # 이전에 선택했던 값이 있다면 불러오기 (값은 ID 리스트 형태여야 함)
        current_multiselect_value = st.session_state['sharing_multiselect']
    
    selected_record_ids = st.multiselect(
        "공유방에 포함할 기록물을 선택해주세요 (여러 개 선택 가능):",
        options=record_options, # [('Label', 'Value_ID'), ...]
        format_func=lambda x: x[0].split(" (")[0], # x는 (Label, Value_ID) 튜플
        key="sharing_multiselect", # 이 key로 session_state에 선택된 Value_ID 리스트가 저장됨
        value=current_multiselect_value # value에는 선택될 ID들의 리스트가 와야 함
    )

    st.subheader("방 설정")
    with st.form("create_room_form", clear_on_submit=True): # clear_on_submit=True는 그대로 둠
        room_name = st.text_input("공유방 이름 (예: 명작 탐험대, 인생 영화 모음)", max_chars=50, key="room_name_input")
        room_password = st.text_input("공유방 비밀번호 (선택 사항)", type="password", help="비밀번호를 설정하면 링크를 아는 사람도 비밀번호를 입력해야 접속할 수 있습니다.", key="room_password_input")
        
        submit_button = st.form_submit_button("공유방 만들기!")

        if submit_button:
            if not room_name:
                st.error("공유방 이름을 입력해주세요!")
            elif not selected_record_ids: 
                st.error("공유할 기록물을 최소 한 개 이상 선택해주세요!")
            else:
                room_id = create_sharing_room(username, room_name, room_password, selected_record_ids)
                sharing_link = f"/?room_id={room_id}" 

                # 성공 메시지/링크 정보를 세션 상태에 저장 (폼 외부에서 표시하기 위함)
                st.session_state['sharing_success_info'] = {
                    "room_name": room_name,
                    "sharing_link": sharing_link,
                    "room_password": room_password
                }
                # multiselect 초기화를 트리거하는 플래그 설정 (이 플래그를 통해 위젯 값이 리셋됨)
                st.session_state['clear_sharing_multiselect'] = True 
                
                st.session_state['current_page'] = "🤝 감상 공유방" # 현재 페이지 유지
                st.rerun() # 성공 시에만 rerun
    
    # 세션 상태에 저장된 성공 메시지 정보를 폼 외부에 표시 (플레이스홀더 사용)
    if 'sharing_success_info' in st.session_state:
        with success_message_placeholder.container(): 
            success_info = st.session_state['sharing_success_info']
            st.success(f"'{success_info['room_name']}' 공유방이 성공적으로 만들어졌습니다! 🎉")
            st.write(f"아래 링크를 친구들에게 공유해주세요. (비밀번호: {success_info['room_password'] if success_info['room_password'] else '없음'})")
            st.code(success_info['sharing_link'])
            st.markdown(f"[클릭하여 공유방 바로가기]({success_info['sharing_link']})", unsafe_allow_html=True)
            st.info("이 페이지에서 나중에 공유방 관리(생성/삭제/수정) 기능을 추가할 수 있습니다.")
            
            # 한 번 표시된 후에는 success_info를 지워 다음에 앱이 리로드 될 때 나타나지 않도록 할 수 있음
            # del st.session_state['sharing_success_info'] 

# --- Sharing Room Viewer Page ---
def render_sharing_room_viewer():
    query_params = st.query_params 
    room_id = query_params.get("room_id") 

    if not room_id:
        st.error("유효하지 않은 공유방 링크입니다. 올바른 링크를 사용해주세요.")
        return

    room_data = get_sharing_room(room_id)

    if not room_data:
        st.error("존재하지 않는 공유방입니다. 링크를 확인해주세요.")
        return

    st.title(f"✨ 감상 공유방: {room_data['room_name']}")
    st.write(f"_{room_data['creator_username']}님의 감상_")
    
    if room_data['room_password']:
        auth_key = f"room_authenticated_{room_id}"
        
        if auth_key not in st.session_state or not st.session_state[auth_key]:
            with st.form("room_password_form"):
                entered_password = st.text_input("공유방 비밀번호를 입력해주세요:", type="password", key="room_pass_input")
                auth_button = st.form_submit_button("접속")
                
                if auth_button:
                    if entered_password == room_data['room_password']:
                        st.session_state[auth_key] = True 
                        st.rerun()
                    else:
                        st.error("비밀번호가 올바르지 않습니다.")
            return 

    st.info("이 방은 친구들과 함께 즐기는 공유방입니다. 비밀번호는 만든 사람에게 문의하세요.")

    creator_username = room_data['creator_username']
    all_creator_records = load_user_records(creator_username)
    shared_record_ids = room_data['shared_record_ids']
    
    shared_records = [r for r in all_creator_records if r['id'] in shared_record_ids]

    if shared_records:
        for record in shared_records:
            with st.expander(f"{record.get('title')} ({record.get('recorded_date').split(' ')[0]})") as expander_element: # expander_element를 사용
                st.write(f"**종류:** {record.get('type')}")
                st.write(f"**제목:** {record.get('title')}")
                # "director_author" 필드가 없는 경우 KeyError 방지
                if record.get('director_author'): 
                    st.write(f"**{'감독' if record.get('type')=='영화' else '저자'}:** {record.get('director_author')}")
                if record.get('release_pub_date'):
                    st.write(f"**{'개봉일' if record.get('type')=='영화' else '출판일'}:** {record.get('release_pub_date')}")
                if record.get('genre'):
                    st.write(f"**장르:** {record.get('genre')}")
                
                if record.get('image_url'):
                    try:
                        st.image(record.get('image_url'), width=200, caption=f"'{record.get('title')}' 포스터/표지")
                    except Exception:
                        st.warning(f"이미지를 불러올 수 없습니다: {record.get('image_url')}")
                
                st.write(f"**나의 평점:** {'⭐' * record.get('rating')} ({record.get('rating')}점)")
                st.write(f"**나의 감상:** {record.get('review')}")
                st.write(f"기록일: {record.get('recorded_date')}")
    else:
        st.info("이 공유방에는 아직 공유된 기록물이 없습니다.")

# --- Main App Logic ---
def main():
    st.set_page_config(page_title="나만의 기록 앱", page_icon="📝", layout="wide")

    # URL 쿼리 파라미터에서 room_id 확인
    query_params = st.query_params
    room_id_from_url = query_params.get("room_id")

    # session_state 초기화
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
    if 'username' not in st.session_state:
        st.session_state['username'] = None
    if 'current_page' not in st.session_state:
        st.session_state['current_page'] = "📖 내 기록 보기"

    # 수동 입력 폼 관련 세션 스테이트 초기화 (값을 미리 채울 때 사용)
    if 'manual_entry_title' not in st.session_state: st.session_state['manual_entry_title'] = ''
    if 'manual_entry_type' not in st.session_state: st.session_state['manual_entry_type'] = '영화'
    if 'manual_entry_director_author' not in st.session_state: st.session_state['manual_entry_director_author'] = ''
    if 'manual_entry_release_pub_date' not in st.session_state: st.session_state['manual_entry_release_pub_date'] = ''
    if 'manual_entry_image_url' not in st.session_state: st.session_state['manual_entry_image_url'] = ''
    if 'manual_entry_summary' not in st.session_state: st.session_state['manual_entry_summary'] = ''
    if 'manual_entry_mode' not in st.session_state: st.session_state['manual_entry_mode'] = False
    
    # 공유방 multiselect 초기화를 위한 플래그
    if 'clear_sharing_multiselect' not in st.session_state:
        st.session_state['clear_sharing_multiselect'] = False

    # sharing_multiselect의 기본값을 항상 빈 리스트로 보장 (TypeError 방지)
    if 'sharing_multiselect' not in st.session_state:
        st.session_state['sharing_multiselect'] = []

    # 공유방 접속 시 별도 처리 (로그인 없이 바로 방으로 이동)
    if room_id_from_url:
        render_sharing_room_viewer()
    else: # 일반 앱 흐름 (로그인 필요)
        if st.session_state['logged_in']:
            # --- 로그인 성공 후 메인 페이지 ---
            st.sidebar.title(f"환영합니다, {st.session_state['username']}님! 👋")
            if st.sidebar.button("로그아웃 🚪"):
                st.session_state['logged_in'] = False
                st.session_state['username'] = None
                st.session_state['current_page'] = "📖 내 기록 보기"
                st.session_state['manual_entry_mode'] = False
                # 모든 공유방 인증 세션 초기화 (접속했던 방의 비밀번호도 초기화)
                for key in list(st.session_state.keys()):
                    if key.startswith('room_authenticated_'):
                        del st.session_state[key]
                
                # sharing_success_info 초기화 (성공 메시지를 다시 띄우지 않도록)
                if 'sharing_success_info' in st.session_state:
                    del st.session_state['sharing_success_info']
                
                # 공유방 멀티셀렉트 초기화
                if 'sharing_multiselect' in st.session_state:
                    del st.session_state['sharing_multiselect'] # 명시적으로 제거
                if 'current_sharing_multiselect_initialized' in st.session_state: # 이 플래그도 초기화
                    del st.session_state['current_sharing_multiselect_initialized']

                st.rerun()

            # 사이드바에서 페이지 선택 라디오 버튼
            st.sidebar.markdown("---")
            selected_page = st.sidebar.radio(
                "메뉴",
                ["📖 내 기록 보기", "🔍 작품 검색 및 기록", "🤝 감상 공유방", "✨ 인기 작품 보기"],
                key="main_menu_radio"
            )
            
            # 페이지 전환 시 multiselect 초기화 플래그를 관리 (중요!)
            if st.session_state['current_page'] != selected_page: # 페이지가 변경될 때만
                if selected_page == "🤝 감상 공유방":
                    st.session_state['clear_sharing_multiselect'] = True # multiselect 초기화 지시
                
                # 다른 페이지에서 넘어올 때 공유방 성공 메시지 초기화 (선택 사항)
                if selected_page != "🤝 감상 공유방" and 'sharing_success_info' in st.session_state:
                     del st.session_state['sharing_success_info']

                st.session_state['current_page'] = selected_page
                st.rerun() # 페이지 전환

            # 메인 콘텐츠 영역 (선택된 페이지에 따라 다른 함수 호출)
            if st.session_state['current_page'] == "📖 내 기록 보기":
                st.title("📖 내 기록 보기")
                user_records = load_user_records(st.session_state['username'])
                if user_records:
                    st.write(f"{st.session_state['username']}님의 소중한 기록들을 보여드릴게요.")
                    for record in user_records: 
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
                else:
                    st.info(f"{st.session_state['username']}님의 기록이 아직 없습니다. '작품 검색 및 기록'에서 새로운 작품을 추가해보세요!")


            elif st.session_state['current_page'] == "🔍 작품 검색 및 기록":
                render_search_and_record_page()
            elif st.session_state['current_page'] == "🤝 감상 공유방":
                render_create_sharing_room_page(st.session_state['username'])
            elif st.session_state['current_page'] == "✨ 인기 작품 보기":
                st.title("✨ 인기 작품 보기")
                st.write("지금 다른 사용자들이 어떤 작품에 관심을 가지고 있는지 보여주는 공간이 될 거예요!")
                st.info("인기 작품 목록은 나중에 구현될 예정입니다.")

        else:
            # --- 로그인/회원가입 페이지 ---
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
