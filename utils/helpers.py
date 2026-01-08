import streamlit as st
from typing import Any

def init_session_state(key: str, default_value: Any):
    """세션 상태 초기화"""
    if key not in st.session_state:
        st.session_state[key] = default_value

def show_success_message(message: str):
    """성공 메시지 표시"""
    st.success(f"✅ {message}")

def show_error_message(message: str):
    """오류 메시지 표시"""
    st.error(f"❌ {message}")

def show_warning_message(message: str):
    """경고 메시지 표시"""
    st.warning(f"⚠️ {message}")

def show_info_message(message: str):
    """정보 메시지 표시"""
    st.info(f"ℹ️ {message}")

def format_json_display(data: dict) -> str:
    """JSON 데이터를 보기 좋게 포맷팅"""
    import json
    return json.dumps(data, ensure_ascii=False, indent=2)
