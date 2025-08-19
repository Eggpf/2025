import streamlit as st
import json
import os
import requests
from datetime import datetime
import uuid # 고유 ID 생성을 위해 추가

# --- Constants ---
USER_DATA_FILE = 'users.json' # 사용자 정보를 저장할 파일 (로그인 정보)
SHARING_ROOMS_FILE = 'sharing_rooms.json' # 공유방 정보를 저장할 파일

# Google Books API Key (선택 사항)
# 발급받으셨다면 여기에 넣어주세요. 없어도 책 검색은 작동할 수 있습니다.
GOOGLE_BOOKS_API_KEY = "YOUR_GOOGLE_BOOKS_API_KEY_HERE"

# --- Helper Functions: 파일 기반 데이터 관리 ---
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

# --- Helper Functions: 공유방 관리 ---
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

# --- API 연동 함수: 영화/책 검색 ---
def search_movies(query):
    """TMDB API를 이용해 영화를 검색합니다. (API Key 없어도 작동 시도)"""
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

# --- 렌더링 함수: 검색 결과 표시 및 수동 입력 폼 채우기 ---
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

# --- 렌더링 함수: 수동 기록 폼 ---
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

# --- 렌더링 함수: 작품 검색 및 기록 페이지 ---
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
            results = search_books(query) # `query`를 `search_query`로 수정
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

# --- 렌더링 함수: 감상 공유방 생성 페이지 ---
def render_create_sharing_room_page(username):
    st.title("🎉 새 감상 공유방 만들기")
    st.info("나만의 감상 공유방을 만들고 친구들에게 링크를 공유해보세요!")

    # 성공 메시지 및 링크를 보여줄 placeholder 설정 (폼 바깥에서 관리)
    success_message_placeholder = st.empty() 

    user_records = load_user_records(username)
    if not user_records:
        st.warning("공유할 기록물이 없습니다. '작품 검색 및 기록'에서 먼저 기록을 추가해주세요!")
        # 공유할 기록이 없으면 이전 성공 정보가 있어도 보여주지 않음
        if 'sharing_success_info' in st.session_state:
            del st.session_state['sharing_success_info']
        return

    st.subheader(f"✨ {username}님의 기록물")
    # record_options는 [(표시될 라벨, 실제 값 ID)] 형태의 튜플 리스트
    record_options = [(f"{r['title']} ({r['recorded_date'].split(' ')[0]})", r['id']) for r in user_records]
    
    # 현재 유효한 모든 기록 ID 목록을 Set 형태로 생성 (성능 최적화)
    all_available_record_ids_set = {option[1] for option in record_options}

    # st.multiselect에 전달할 초기값 (value 매개변수) 결정
    initial_multiselect_value = []
    
    # 폼 제출 후 multiselect를 초기화해야 하는 경우 (flag 사용)
    if st.session_state.get('clear_sharing_multiselect_flag', False):
        initial_multiselect_value = []
        # 플래그 사용 후 바로 초기화하여 다음 렌더링에서 다시 초기화되지 않도록 함
        del st.session_state['clear_sharing_multiselect_flag'] 
    else:
        # 이전에 선택했던 값이 세션 상태에 있다면 가져옴
        # .get() 메서드로 'sharing_multiselect'가 없을 때 빈 리스트를 기본값으로 지정하여 KeyError 방지
        stored_selected_ids = st.session_state.get('sharing_multiselect', []) 
        
        # 저장된 선택값 중 현재 유효한(현재 기록 목록에 존재하는) 값들만 필터링
        # 이 필터링이 TypeError를 방지하는 핵심 로직
        initial_multiselect_value = [
            record_id for record_id in stored_selected_ids
            if record_id in all_available_record_ids_set
        ]
        
    selected_record_ids = st.multiselect(
        "공유방에 포함할 기록물을 선택해주세요 (여러 개 선택 가능):",
        options=record_options, # [('Label', 'Value_ID'), ...]
        format_func=lambda x: x[0].split(" (")[0], # x는 (Label, Value_ID) 튜플
        key="sharing_multiselect", # 이 key로 st.session_state에 선택된 Value_ID 리스트가 저장됨
        value=initial_multiselect_value # <--- 필터링된 유효한 값들의 리스트를 전달!
    )

    st.subheader("방 설정")
    # clear_on_submit=True는 폼 제출 후 폼 내부의 위젯 값을 초기화
    with st.form("create_room_form", clear_on_submit=True): 
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

                # 공유방 생성 성공 정보를 세션 상태에 저장 (폼 외부에서 표시하기 위함)
                st.session_state['sharing_success_info'] = {
                    "room_name": room_name,
                    "sharing_link": sharing_link,
                    "room_password": room_password
                }
                # multiselect를 초기화하도록 지시하는 플래그 설정
                st.session_state['clear_sharing_multiselect_flag'] = True 
                
                # 페이지를 다시 로드하여 성공 메시지 표시 및 폼 초기화 (UI 업데이트)
                st.session_state['current_page'] = "🤝 감상 공유방" 
                st.rerun() 
    
    # 세션 상태에 저장된 성공 메시지 정보를 폼 외부에 표시 (placeholder 사용)
    if 'sharing_success_info' in st.session_state:
        with success_message_placeholder.container(): 
            success_info = st.session_state['sharing_success_info']
            st.success(f"'{success_info['room_name']}' 공유방이 성공적으로 만들어졌습니다! 🎉")
            st.write(f"아래 링크를 친구들에게 공유해주세요. (비밀번호: {success_info['room_password'] if success_info['room_password'] else '없음'})")
            st.code(success_info['sharing_link'])
            st.markdown(f"[클릭하여 공유방 바로가기]({success_info['sharing_link']})", unsafe_allow_html=True)
            st.info("이 페이지에서 나중에 공유방 관리(생성/삭제/수정) 기능을 추가할 수 있습니다.")
            
            # 만약 한 번 보여준 후 다음 리로드 시에는 다시 보이지 않게 하고 싶다면 이 줄 주석 해제
            # del st.session_state['sharing_success_info'] 

# --- 렌더링 함수: 감상 공유방 조회 페이지 ---
def render_sharing_room_viewer():
    # st.query_params는 딕셔너리처럼 동작하여 URL 쿼리 파라미터에 접근
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
    
    # 비밀번호가 설정되어 있다면 비밀번호 확인 로직 수행
    if room_data['room_password']:
        auth_key = f"room_authenticated_{room_id}" # 방마다 고유한 인증 상태 키 생성
        
        # 인증되지 않았거나 다른 방이었다면 비밀번호 입력 폼 표시
        if auth_key not in st.session_state or not st.session_state[auth_key]:
            with st.form("room_password_form"):
                entered_password = st.text_input("공유방 비밀번호를 입력해주세요:", type="password", key="room_pass_input")
                auth_button = st.form_submit_button("접속")
                
                if auth_button:
                    if entered_password == room_data['room_password']:
                        st.session_state[auth_key] = True # 해당 방에 대한 인증 성공 표시
                        st.rerun() # 인증 후 페이지 리로드
                    else:
                        st.error("비밀번호가 올바르지 않습니다.")
            return # 비밀번호 입력 폼이 보이면 여기서 함수 종료 (아래 콘텐츠는 표시 안 함)

    st.info("이 방은 친구들과 함께 즐기는 공유방입니다. 비밀번호는 만든 사람에게 문의하세요.")

    # 공유된 기록물 표시
    creator_username = room_data['creator_username']
    all_creator_records = load_user_records(creator_username)
    shared_record_ids = room_data['shared_record_ids']
    
    # 모든 기록물 중 공유된 ID에 해당하는 기록물만 필터링
    shared_records = [r for r in all_creator_records if r['id'] in shared_record_ids]

    if shared_records:
        for record in shared_records:
            # st.expander는 context manager이므로 'as expander_element' 필요 없음
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
                    except Exception: # 이미지 로드 실패 시
                        st.warning(f"이미지를 불러올 수 없습니다: {record.get('image_url')}")
                
                st.write(f"**나의 평점:** {'⭐' * record.get('rating')} ({record.get('rating')}점)")
                st.write(f"**나의 감상:** {record.get('review')}")
                st.write(f"기록일: {record.get('recorded_date')}")
    else:
        st.info("이 공유방에는 아직 공유된 기록물이 없습니다.")

# --- 메인 앱 로직 ---
def main():
    # 페이지 기본 설정: 제목, 아이콘, 레이아웃
    st.set_page_config(page_title="나만의 기록 앱", page_icon="📝", layout="wide")

    # URL 쿼리 파라미터에서 room_id 확인 (공유방 링크로 직접 접근했는지 여부)
    query_params = st.query_params
    room_id_from_url = query_params.get("room_id")

    # 세션 상태(st.session_state) 초기화: 앱 전반의 상태를 기억
    # 이 부분은 앱이 처음 로드될 때 또는 리셋될 때만 실행됩니다.
    if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
    if 'username' not in st.session_state: st.session_state['username'] = None
    if 'current_page' not in st.session_state: st.session_state['current_page'] = "📖 내 기록 보기"

    # 수동 입력 폼의 미리 채울 값들을 위한 세션 상태 변수 초기화
    if 'manual_entry_title' not in st.session_state: st.session_state['manual_entry_title'] = ''
    if 'manual_entry_type' not in st.session_state: st.session_state['manual_entry_type'] = '영화'
    if 'manual_entry_director_author' not in st.session_state: st.session_state['manual_entry_director_author'] = ''
    if 'manual_entry_release_pub_date' not in st.session_state: st.session_state['manual_entry_release_pub_date'] = ''
    if 'manual_entry_image_url' not in st.session_state: st.session_state['manual_entry_image_url'] = ''
    if 'manual_entry_summary' not in st.session_state: st.session_state['manual_entry_summary'] = ''
    if 'manual_entry_mode' not in st.session_state: st.session_state['manual_entry_mode'] = False
    
    # 공유방 멀티셀렉트 초기화를 위한 플래그 (폼 제출 후 초기화를 트리거)
    if 'clear_sharing_multiselect_flag' not in st.session_state:
        st.session_state['clear_sharing_multiselect_flag'] = False
    # sharing_multiselect 위젯 자체의 값은 key="sharing_multiselect"에 의해 자동으로 관리되므로,
    # 여기서는 초기 상태를 보장하기 위해 빈 리스트로 직접 설정하지 않고,
    # 위젯이 로드될 때 value= 매개변수를 통해 제어합니다.
    # 하지만 만약을 대비해서 해당 키가 없으면 빈 리스트로 시작하도록 하는 것이 안전
    if 'sharing_multiselect' not in st.session_state:
        st.session_state['sharing_multiselect'] = []


    # 앱의 메인 로직 분기: 공유방 뷰어 vs. 일반 앱 (로그인 필요)
    if room_id_from_url:
        render_sharing_room_viewer() # 공유방 링크로 접근 시 로그인 없이 바로 보여줌
    else: # 일반 앱 사용: 로그인 필요
        if st.session_state['logged_in']: # 로그인 상태라면 메인 앱 페이지 표시
            # --- 로그인 성공 후 메인 페이지 ---
            st.sidebar.title(f"환영합니다, {st.session_state['username']}님! 👋")
            if st.sidebar.button("로그아웃 🚪"): # 로그아웃 버튼
                st.session_state['logged_in'] = False
                st.session_state['username'] = None
                st.session_state['current_page'] = "📖 내 기록 보기"
                st.session_state['manual_entry_mode'] = False
                # 로그인 세션과 관련된 모든 상태를 초기화
                for key in list(st.session_state.keys()):
                    if key.startswith('room_authenticated_') or \
                       key == 'sharing_success_info' or \
                       key == 'clear_sharing_multiselect_flag' or \
                       key == 'sharing_multiselect': # multiselect 값도 로그아웃 시 확실히 초기화
                        del st.session_state[key]
                st.rerun() # 로그아웃 후 앱 재시작 (로그인 페이지로 돌아감)

            # 사이드바에서 메뉴 선택
            st.sidebar.markdown("---")
            selected_page_from_radio = st.sidebar.radio( # 라디오 버튼의 실제 선택값
                "메뉴",
                ["📖 내 기록 보기", "🔍 작품 검색 및 기록", "🤝 감상 공유방", "✨ 인기 작품 보기"],
                key="main_menu_radio"
            )
            
            # 페이지 전환 로직: 선택된 페이지가 현재 페이지와 다를 경우만 처리
            if st.session_state['current_page'] != selected_page_from_radio:
                # 페이지 변경 시 기존 공유방 성공 메시지 초기화 (선택사항, 깔끔한 UI 위함)
                if 'sharing_success_info' in st.session_state:
                    del st.session_state['sharing_success_info']
                
                # '감상 공유방' 페이지로 이동할 때 multiselect 초기화를 지시하는 플래그 설정
                if selected_page_from_radio == "🤝 감상 공유방":
                    st.session_state['clear_sharing_multiselect_flag'] = True
                
                st.session_state['current_page'] = selected_page_from_radio # 현재 페이지 상태 업데이트
                st.rerun() # 페이지 전환을 위해 앱 재실행

            # 메인 콘텐츠 영역: 현재 선택된 페이지에 따라 다른 함수 호출
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

        else: # 로그인되지 않은 상태일 경우 로그인/회원가입 페이지 표시
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
