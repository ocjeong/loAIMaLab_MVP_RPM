import streamlit as st
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd

# 모듈 경로 추가
sys.path.append(str(Path(__file__).parent))

from modules.database import init_database, get_users, get_user_requests, create_user
from modules.visualization import create_monthly_schedule

# 페이지 설정
st.set_page_config(
    page_title="RPM - Reliable Planning Manager",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 세션 상태 초기화
if 'db_initialized' not in st.session_state:
    init_database()
    st.session_state.db_initialized = True

if 'current_user' not in st.session_state:
    st.session_state.current_user = None

if 'current_request' not in st.session_state:
    st.session_state.current_request = None

if 'extracted_data' not in st.session_state:
    st.session_state.extracted_data = None

# 메인 화면
def main():
    st.title("🔧 RPM - Reliable Planning Manager")
    st.subheader("Blower Motor Test Support System")
    
    st.markdown("---")
    
    # 사용자 선택 섹션
    st.header("👤 사용자 선택")
    
    users = get_users()
    
    if not users:
        st.warning("등록된 사용자가 없습니다. 새 사용자를 등록하세요.")
        with st.expander("➕ 새 사용자 등록"):
            with st.form("new_user_form"):
                user_id = st.text_input("사용자 ID (예: U001)")
                user_name = st.text_input("이름")
                department = st.text_input("부서")
                
                if st.form_submit_button("등록"):
                    if user_id and user_name:
                        create_user(user_id, user_name, department)
                        st.success(f"✅ {user_name}님이 등록되었습니다.")
                        st.rerun()
                    else:
                        st.error("사용자 ID와 이름은 필수입니다.")
    else:
        user_options = {f"{u[1]} ({u[2]})": u[0] for u in users}
        selected_user = st.selectbox(
            "사용자를 선택하세요",
            options=list(user_options.keys()),
            key="user_select"
        )
        
        if selected_user:
            st.session_state.current_user = user_options[selected_user]
            user_id = st.session_state.current_user
            
            # 월간 일정 표시
            st.markdown("---")
            st.header(f"📅 {selected_user}님의 이번 달 시험 일정")
            
            try:
                fig = create_monthly_schedule(user_id)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("등록된 시험 일정이 없습니다.")
            except Exception as e:
                st.info("일정 데이터가 없습니다.")
            
            # 기존 의뢰 선택
            st.markdown("---")
            st.header("📋 의뢰 관리")
            
            requests = get_user_requests(user_id)
            
            if requests:
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    request_options = {
                        f"{r[0]} - {r[2]} ({r[3]})": r[0] for r in requests
                    }
                    selected_request = st.selectbox(
                        "기존 의뢰 선택",
                        options=list(request_options.keys())
                    )
                    
                    if selected_request:
                        st.session_state.current_request = request_options[selected_request]
                
                with col2:
                    st.write("")
                    st.write("")
                    if st.button("📝 의뢰 수정", use_container_width=True):
                        st.switch_page("pages/1_📋_Request_Data.py")
            else:
                st.info("등록된 의뢰가 없습니다.")
            
            # 새 의뢰 생성
            st.markdown("---")
            st.header("➕ 새 의뢰 생성")
            
            uploaded_file = st.file_uploader(
                "테스트 스펙 파일 업로드 (PDF 또는 DOCX)",
                type=["pdf", "docx"],
                help="PDF 또는 DOCX 형식, 최대 10MB"
            )
            
            if uploaded_file:
                file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
                st.info(f"📄 파일명: {uploaded_file.name} ({file_size_mb:.2f} MB)")
                
                if file_size_mb > 10:
                    st.error("❌ 파일 크기가 10MB를 초과합니다.")
                else:
                    if st.button("🚀 새 의뢰 생성", type="primary", use_container_width=True):
                        st.session_state.uploaded_file = uploaded_file
                        st.switch_page("pages/1_📋_Request_Data.py")

    # 사이드바 정보
    with st.sidebar:
        st.header("ℹ️ 시스템 정보")
        st.info(f"**현재 사용자:** {st.session_state.current_user or '미선택'}")
        st.info(f"**현재 의뢰:** {st.session_state.current_request or '미선택'}")
        st.markdown("---")
        st.caption("RPM v1.0.0")
        st.caption("© 2026 Potens.AI")

if __name__ == "__main__":
    main()
