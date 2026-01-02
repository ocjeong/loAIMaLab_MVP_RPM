import streamlit as st
from datetime import datetime


def initialize_session_state():
    """세션 상태 초기화"""
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "user_selection"
    
    if 'current_user' not in st.session_state:
        st.session_state.current_user = None
    
    if 'current_request_id' not in st.session_state:
        st.session_state.current_request_id = None
    
    if 'extracted_data' not in st.session_state:
        st.session_state.extracted_data = None
    
    if 'editable_test_items' not in st.session_state:
        st.session_state.editable_test_items = []
    
    if 'plan_dataframe' not in st.session_state:
        st.session_state.plan_dataframe = None
    
    if 'schedule_items' not in st.session_state:
        st.session_state.schedule_items = []


def show_success_popup(message):
    """성공 메시지 팝업"""
    st.success(f"✅ {message}")


def show_error_popup(message):
    """에러 메시지 팝업"""
    st.error(f"❌ {message}")


def show_warning_popup(message):
    """경고 메시지 팝업"""
    st.warning(f"⚠️ {message}")


def format_date(date_obj):
    """날짜 포맷팅"""
    if isinstance(date_obj, str):
        return date_obj
    return date_obj.strftime("%Y-%m-%d")


def parse_duration(duration_str):
    """소요 시간 문자열을 일수로 변환"""
    try:
        if 'day' in duration_str.lower():
            return int(''.join(filter(str.isdigit, duration_str)))
        elif 'hour' in duration_str.lower() or 'h' in duration_str.lower():
            hours = int(''.join(filter(str.isdigit, duration_str)))
            return max(1, hours // 24)  # 최소 1일
        else:
            return int(''.join(filter(str.isdigit, duration_str)))
    except:
        return 1  # 기본값 1일


def generate_request_id():
    """새로운 의뢰 ID 생성"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"R{timestamp}"
