import streamlit as st
from datetime import datetime
import os
import glob


def initialize_session_state():
    """세션 상태 초기화"""
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'user_selection'
    
    if 'current_user' not in st.session_state:
        st.session_state.current_user = None
    
    if 'current_request' not in st.session_state:
        st.session_state.current_request = None
    
    if 'schedule_data' not in st.session_state:
        st.session_state.schedule_data = None
    
    if 'show_add_modal' not in st.session_state:
        st.session_state.show_add_modal = False
    
    if 'show_delete_modal' not in st.session_state:
        st.session_state.show_delete_modal = False


def get_sample_pdf_files():
    """sample 폴더에서 PDF 파일 목록 가져오기"""
    sample_dir = 'sample'
    
    # sample 폴더가 없으면 생성
    if not os.path.exists(sample_dir):
        os.makedirs(sample_dir)
        return []
    
    # PDF 파일 찾기
    pdf_files = glob.glob(os.path.join(sample_dir, '*.pdf'))
    
    # 파일명만 추출 (경로 제외)
    sample_files = []
    for pdf_path in pdf_files:
        filename = os.path.basename(pdf_path)
        sample_files.append({
            'name': filename,
            'path': pdf_path,
            'display_name': filename.replace('.pdf', '').replace('_', ' ').title()
        })
    
    return sample_files


def load_sample_pdf(file_path):
    """샘플 PDF 파일을 읽어서 UploadedFile과 유사한 객체로 반환"""
    try:
        with open(file_path, 'rb') as f:
            file_bytes = f.read()
        
        # UploadedFile과 유사한 객체 생성
        class SampleFile:
            def __init__(self, name, data):
                self.name = name
                self._data = data
            
            def read(self):
                return self._data
            
            def getvalue(self):
                return self._data
        
        filename = os.path.basename(file_path)
        return SampleFile(filename, file_bytes)
    
    except Exception as e:
        st.error(f"샘플 파일 로드 오류: {e}")
        return None


def load_css():
    """커스텀 CSS 로드"""
    st.markdown("""
        <style>
        /* 메인 컨테이너 스타일 */
        .main {
            padding: 2rem;
        }
        
        /* 버튼 스타일 */
        .stButton>button {
            width: 100%;
            border-radius: 5px;
            height: 3em;
            font-weight: 500;
        }
        
        /* 파일 업로더 스타일 */
        .uploadedFile {
            border: 2px dashed #4472C4;
            border-radius: 5px;
            padding: 1rem;
        }
        
        /* 데이터프레임 스타일 */
        .dataframe {
            font-size: 0.9em;
        }
        
        /* 확장 가능한 섹션 스타일 */
        .streamlit-expanderHeader {
            font-size: 1.1em;
            font-weight: 500;
        }
        
        /* 사이드바 스타일 */
        .css-1d391kg {
            padding-top: 3rem;
        }
        
        /* 제목 스타일 */
        h1 {
            color: #4472C4;
            padding-bottom: 1rem;
            border-bottom: 2px solid #4472C4;
        }
        
        h2 {
            color: #5B9BD5;
            margin-top: 2rem;
        }
        
        h3 {
            color: #70AD47;
            margin-top: 1.5rem;
        }
        
        /* 정보 박스 스타일 */
        .stAlert {
            border-radius: 5px;
        }
        
        /* 테이블 스타일 */
        table {
            width: 100%;
        }
        
        /* 입력 필드 스타일 */
        .stTextInput>div>div>input {
            border-radius: 5px;
        }
        
        .stSelectbox>div>div>select {
            border-radius: 5px;
        }
        
        /* 구분선 스타일 */
        hr {
            margin: 2rem 0;
            border: none;
            border-top: 1px solid #e0e0e0;
        }
        
        /* 아이콘 스타일 */
        .icon-success {
            color: #28a745;
            font-size: 1.2em;
        }
        
        .icon-warning {
            color: #ffc107;
            font-size: 1.2em;
        }
        
        .icon-error {
            color: #dc3545;
            font-size: 1.2em;
        }
        
        /* 샘플 파일 버튼 스타일 */
        .sample-file-button {
            background-color: #70AD47;
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 5px;
            cursor: pointer;
            margin: 0.25rem;
        }
        
        .sample-file-button:hover {
            background-color: #5a8c38;
        }
        </style>
    """, unsafe_allow_html=True)


def format_date(date_str):
    """날짜 문자열 포맷팅"""
    try:
        if isinstance(date_str, str):
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        else:
            date_obj = date_str
        return date_obj.strftime('%Y년 %m월 %d일')
    except:
        return date_str


def validate_file_type(file, allowed_types=['pdf', 'docx']):
    """파일 타입 검증"""
    if file is None:
        return False
    
    file_extension = file.name.split('.')[-1].lower()
    return file_extension in allowed_types


def generate_id(prefix, last_id, id_length=3):
    """ID 생성 헬퍼 함수"""
    if last_id:
        num = int(last_id[len(prefix):]) + 1
    else:
        num = 1
    
    return f"{prefix}{num:0{id_length}d}"


def safe_json_parse(json_str, default=None):
    """안전한 JSON 파싱"""
    import json
    try:
        return json.loads(json_str)
    except:
        return default if default is not None else {}


def truncate_text(text, max_length=50):
    """텍스트 자르기"""
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length] + "..."


def format_duration(days):
    """기간 포맷팅"""
    try:
        days = int(days)
        if days == 1:
            return "1일"
        elif days < 7:
            return f"{days}일"
        elif days < 30:
            weeks = days // 7
            remaining_days = days % 7
            if remaining_days == 0:
                return f"{weeks}주"
            else:
                return f"{weeks}주 {remaining_days}일"
        else:
            months = days // 30
            remaining_days = days % 30
            if remaining_days == 0:
                return f"{months}개월"
            else:
                return f"{months}개월 {remaining_days}일"
    except:
        return str(days)


def create_download_link(data, filename, file_type="text/csv"):
    """다운로드 링크 생성"""
    import base64
    
    if isinstance(data, str):
        data = data.encode()
    
    b64 = base64.b64encode(data).decode()
    href = f'<a href="data:{file_type};base64,{b64}" download="{filename}">📥 {filename} 다운로드</a>'
    return href


def show_success_message(message, duration=3):
    """성공 메시지 표시"""
    st.success(f"✅ {message}")


def show_error_message(message):
    """에러 메시지 표시"""
    st.error(f"❌ {message}")


def show_warning_message(message):
    """경고 메시지 표시"""
    st.warning(f"⚠️ {message}")


def show_info_message(message):
    """정보 메시지 표시"""
    st.info(f"ℹ️ {message}")


def confirm_action(message):
    """액션 확인 다이얼로그"""
    return st.checkbox(message)


def create_progress_bar(current, total, label="진행률"):
    """진행률 바 생성"""
    progress = current / total if total > 0 else 0
    st.progress(progress)
    st.text(f"{label}: {current}/{total} ({progress*100:.1f}%)")


def format_file_size(size_bytes):
    """파일 크기 포맷팅"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


def get_status_icon(status):
    """상태 아이콘 반환"""
    icons = {
        'success': '✅',
        'warning': '⚠️',
        'error': '❌',
        'info': 'ℹ️',
        'pending': '⏳',
        'completed': '✔️',
        'in_progress': '🔄'
    }
    return icons.get(status, '•')


def create_badge(text, color='blue'):
    """배지 생성"""
    colors = {
        'blue': '#4472C4',
        'green': '#70AD47',
        'red': '#E74C3C',
        'yellow': '#F39C12',
        'gray': '#95A5A6'
    }
    
    bg_color = colors.get(color, colors['blue'])
    
    badge_html = f"""
        <span style="
            background-color: {bg_color};
            color: white;
            padding: 0.25rem 0.75rem;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 500;
            display: inline-block;
            margin: 0.25rem;
        ">
            {text}
        </span>
    """
    return badge_html


def display_metric_card(title, value, delta=None, icon="📊"):
    """메트릭 카드 표시"""
    col1, col2 = st.columns([1, 4])
    with col1:
        st.markdown(f"<div style='font-size: 3em;'>{icon}</div>", unsafe_allow_html=True)
    with col2:
        st.metric(label=title, value=value, delta=delta)
