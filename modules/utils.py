import streamlit as st

def initialize_session_state():
    """세션 상태 초기화"""
    if 'current_user' not in st.session_state:
        st.session_state.current_user = None
    
    if 'current_request' not in st.session_state:
        st.session_state.current_request = None
    
    if 'extracted_data' not in st.session_state:
        st.session_state.extracted_data = None
    
    if 'plan_dataframe' not in st.session_state:
        st.session_state.plan_dataframe = None
    
    if 'edit_mode' not in st.session_state:
        st.session_state.edit_mode = False
    
    if 'show_add_user' not in st.session_state:
        st.session_state.show_add_user = False

    if 'page_to_show' not in st.session_state:
        st.session_state.page_to_show = None

def display_session_info(user, request):
    """세션 정보 표시"""
    st.info(f"👤 **사용자:** {user['name']} | 📋 **의뢰:** {request.get('client', 'N/A')} - {request.get('project', 'N/A')}")
