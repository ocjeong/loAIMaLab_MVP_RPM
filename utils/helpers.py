import streamlit as st
import pandas as pd

def initialize_session_state():
    """세션 상태 초기화"""
    if 'page' not in st.session_state:
        st.session_state.page = "user_selection"
    
    if 'current_user' not in st.session_state:
        st.session_state.current_user = None
    
    if 'current_request_id' not in st.session_state:
        st.session_state.current_request_id = None
    
    if 'selected_request_id' not in st.session_state:
        st.session_state.selected_request_id = None
    
    if 'extracted_data' not in st.session_state:
        st.session_state.extracted_data = None
    
    if 'edited_test_items' not in st.session_state:
        st.session_state.edited_test_items = None
    
    if 'plan_data' not in st.session_state:
        st.session_state.plan_data = None

def save_dataframe_to_csv(df, filename):
    """데이터프레임을 CSV로 저장"""
    try:
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        return True
    except Exception as e:
        print(f"Error saving CSV: {e}")
        return False

def load_csv_to_dataframe(filename):
    """CSV를 데이터프레임으로 로드"""
    try:
        return pd.read_csv(filename, encoding='utf-8-sig')
    except Exception as e:
        print(f"Error loading CSV: {e}")
        return pd.DataFrame()
