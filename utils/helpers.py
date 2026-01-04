import streamlit as st
import pandas as pd
from io import BytesIO

def init_session_state():
    """세션 상태 초기화"""
    if 'current_screen' not in st.session_state:
        st.session_state.current_screen = 'user_selection'
    
    if 'current_user_id' not in st.session_state:
        st.session_state.current_user_id = None
    
    if 'current_user_name' not in st.session_state:
        st.session_state.current_user_name = None
    
    if 'extracted_data' not in st.session_state:
        st.session_state.extracted_data = None
    
    if 'editing_request_id' not in st.session_state:
        st.session_state.editing_request_id = None
    
    if 'edited_test_items' not in st.session_state:
        st.session_state.edited_test_items = []
    
    if 'final_plan' not in st.session_state:
        st.session_state.final_plan = None
    
    if 'schedule_details' not in st.session_state:
        st.session_state.schedule_details = None

def save_excel(dataframe):
    """DataFrame을 Excel 파일로 변환"""
    output = BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        dataframe.to_excel(writer, index=False, sheet_name='Test Plan')
    
    output.seek(0)
    return output.getvalue()

def format_date(date_str):
    """날짜 포맷 변환"""
    from datetime import datetime
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        return date_obj.strftime('%Y년 %m월 %d일')
    except:
        return date_str
