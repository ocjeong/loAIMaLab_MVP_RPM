import streamlit as st
import pandas as pd
from datetime import datetime
import os
from modules.database import DatabaseManager
from modules.llm_handler import LLMHandler
from modules.standardization import standardize_test_item, get_master_by_id
from modules.schedule import ScheduleManager
from modules.export import ExportManager
from utils.helpers import initialize_session_state, load_css

# 페이지 설정
st.set_page_config(
    page_title="RPM - Reliable Planning Manager",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 세션 상태 초기화
initialize_session_state()

# CSS 로드
load_css()

# 데이터베이스 매니저 초기화
db = DatabaseManager()

# LLM 핸들러 초기화
llm_handler = LLMHandler()

# 스케줄 매니저 초기화
schedule_manager = ScheduleManager()

# 내보내기 매니저 초기화
export_manager = ExportManager()


def render_sidebar():
    """사이드바 렌더링"""
    with st.sidebar:
        st.title("🔧 RPM")
        st.markdown("### Reliable Planning Manager")
        st.divider()
        
        # 3.5.1. 현재 세션 정보 표시
        st.markdown("#### 📊 세션 정보")
        if st.session_state.current_user:
            st.info(f"👤 사용자: {st.session_state.current_user['user_name']}")
        else:
            st.warning("사용자를 선택해주세요")
        
        if st.session_state.current_request:
            st.info(f"📄 의뢰: {st.session_state.current_request.get('project', 'N/A')}")
        
        st.divider()
        
        # 3.5.2. 화면 네비게이션 버튼
        st.markdown("#### 🧭 네비게이션")
        
        if st.button("🏠 사용자 선택", use_container_width=True):
            st.session_state.current_page = "user_selection"
            st.rerun()
        
        if st.button("📝 시험 규격 편집", use_container_width=True, 
                     disabled=not st.session_state.current_user):
            st.session_state.current_page = "test_spec_edit"
            st.rerun()
        
        if st.button("📋 계획서 작성", use_container_width=True,
                     disabled=not st.session_state.current_request):
            st.session_state.current_page = "plan_draft"
            st.rerun()
        
        if st.button("📅 일정 관리", use_container_width=True,
                     disabled=not st.session_state.schedule_data):
            st.session_state.current_page = "schedule_management"
            st.rerun()
        
        st.divider()
        
        # 3.5.3. Database Export 기능
        st.markdown("#### 💾 데이터베이스 내보내기")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Master", use_container_width=True):
                csv = db.export_to_csv('master')
                st.download_button(
                    "⬇️ 다운로드",
                    csv,
                    "Master_Test.csv",
                    "text/csv",
                    use_container_width=True
                )
        
        with col2:
            if st.button("Request", use_container_width=True):
                csv = db.export_to_csv('request')
                st.download_button(
                    "⬇️ 다운로드",
                    csv,
                    "Request_Info.csv",
                    "text/csv",
                    use_container_width=True
                )
        
        col3, col4 = st.columns(2)
        with col3:
            if st.button("Test Item", use_container_width=True):
                csv = db.export_to_csv('test_item')
                st.download_button(
                    "⬇️ 다운로드",
                    csv,
                    "Test_Item.csv",
                    "text/csv",
                    use_container_width=True
                )
        
        with col4:
            if st.button("User List", use_container_width=True):
                csv = db.export_to_csv('user')
                st.download_button(
                    "⬇️ 다운로드",
                    csv,
                    "User_List.csv",
                    "text/csv",
                    use_container_width=True
                )


def page_user_selection():
    """3.1. 사용자 선택 화면"""
    st.title("👤 사용자 선택")
    
    col1, col2 = st.columns([2, 3])
    
    with col1:
        # 3.1.1. 사용자 선택 메뉴
        st.markdown("### 사용자 선택")
        
        users = db.get_all_users()
        user_names = [user['user_name'] for user in users]
        
        selected_user_name = st.selectbox(
            "사용자를 선택하세요",
            options=user_names,
            index=0 if user_names else None
        )
        
        if selected_user_name:
            selected_user = next(u for u in users if u['user_name'] == selected_user_name)
            st.session_state.current_user = selected_user
            db.update_user_last_access(selected_user['id'])
        
        # 사용자 추가
        st.markdown("#### 새 사용자 추가")
        new_user_name = st.text_input("사용자 이름")
        if st.button("➕ 사용자 추가", use_container_width=True):
            if new_user_name:
                db.add_user(new_user_name)
                st.success(f"✅ {new_user_name} 사용자가 추가되었습니다!")
                st.rerun()
            else:
                st.error("사용자 이름을 입력해주세요.")
        
        st.divider()
        
        # 3.1.3. 의뢰 선택 메뉴
        if st.session_state.current_user:
            st.markdown("### 기존 의뢰 선택")
            
            user_requests = db.get_user_requests(st.session_state.current_user['id'])
            
            if user_requests:
                request_options = {
                    f"{req['project']} ({req['client']})": req['id'] 
                    for req in user_requests
                }
                
                selected_request = st.selectbox(
                    "의뢰를 선택하세요",
                    options=list(request_options.keys())
                )
                
                if selected_request:
                    request_id = request_options[selected_request]
                    request_data = db.get_request_by_id(request_id)
                    st.session_state.current_request = request_data
                    
                    # 3.1.5. 의뢰 수정 버튼
                    if st.button("✏️ 의뢰 수정", use_container_width=True):
                        st.session_state.current_page = "test_spec_edit"
                        st.rerun()
            else:
                st.info("저장된 의뢰가 없습니다.")
        
        st.divider()
        
        # 3.1.4. 새 의뢰 버튼
        st.markdown("### 새 의뢰 생성")
        uploaded_file = st.file_uploader(
            "시험 규격 파일 업로드",
            type=['pdf', 'docx'],
            help="PDF 또는 DOCX 형식의 파일만 업로드 가능합니다."
        )
        
        if uploaded_file:
            if st.button("🚀 새 의뢰 생성", use_container_width=True):
                with st.spinner("문서를 분석하고 있습니다..."):
                    # 파일 처리 및 LLM 추출
                    extracted_data = llm_handler.extract_from_document(uploaded_file)
                    
                    if extracted_data:
                        # 표준화 적용
                        standardized_items = []
                        for item in extracted_data.get('test_items', []):
                            standardized_item = standardize_test_item(item, db)
                            standardized_items.append(standardized_item)
                        
                        # 새 의뢰 생성
                        request_id = db.create_request(
                            user_id=st.session_state.current_user['id'],
                            client=extracted_data.get('request_info', {}).get('client', ''),
                            project=extracted_data.get('request_info', {}).get('project', ''),
                            extracted_data=extracted_data.get('test_items', []),
                            final_data=standardized_items
                        )
                        
                        st.session_state.current_request = db.get_request_by_id(request_id)
                        st.success("✅ 의뢰가 생성되었습니다!")
                        st.session_state.current_page = "test_spec_edit"
                        st.rerun()
                    else:
                        st.error("문서 추출에 실패했습니다.")
    
    with col2:
        # 3.1.2. 일정 확인 박스
        st.markdown("### 📅 시험 일정")
        
        if st.session_state.current_user:
            schedules = db.get_user_schedules(st.session_state.current_user['id'])
            
            if schedules:
                # 선택된 의뢰의 일정 또는 전체 일정 표시
                if st.session_state.current_request:
                    filtered_schedules = [
                        s for s in schedules 
                        if s.get('request_id') == st.session_state.current_request['id']
                    ]
                    st.markdown(f"**{st.session_state.current_request.get('project', '')} 의뢰 일정**")
                else:
                    filtered_schedules = schedules
                    st.markdown("**전체 시험 일정**")
                
                if filtered_schedules:
                    fig = schedule_manager.create_gantt_chart(filtered_schedules)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("표시할 일정이 없습니다.")
            else:
                st.info("저장된 일정이 없습니다.")
        else:
            st.warning("사용자를 선택해주세요.")


def page_test_spec_edit():
    """3.2. 추출 시험 규격 편집 화면"""
    st.title("📝 시험 규격 편집")
    
    if not st.session_state.current_request:
        st.warning("의뢰를 선택하거나 생성해주세요.")
        return
    
    # 3.2.1. 의뢰 추출 데이터 박스
    st.markdown("### 의뢰 정보")
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"**발주처:** {st.session_state.current_request.get('client', 'N/A')}")
    with col2:
        st.info(f"**프로젝트:** {st.session_state.current_request.get('project', 'N/A')}")
    
    st.divider()
    
    # 시험 항목 편집
    st.markdown("### 시험 항목 목록")
    
    final_data = st.session_state.current_request.get('final_data', [])
    
    if not final_data:
        st.warning("시험 항목이 없습니다.")
        return
    
    # Expandable tree view로 표시
    for idx, item in enumerate(final_data):
        # 표준화 적용 여부 아이콘
        if item.get('test_master_id'):
            master = get_master_by_id(item['test_master_id'], db)
            icon = "✅"
            status = f"[마스터: {item['test_master_id']}]"
            status_color = "green"
        else:
            master = None
            icon = "⚠️"
            status = "[미매칭]"
            status_color = "orange"
        
        with st.expander(
            f"{icon} {item.get('test_name', 'Unknown Test')} {status}",
            expanded=False
        ):
            # 표준화 비교 표시
            if master:
                col_orig, col_std = st.columns(2)
                
                with col_orig:
                    st.markdown("#### 📄 원본 데이터")
                    st.text(f"시험명: {item.get('test_name_original', 'N/A')}")
                    st.text(f"분류: {item.get('category_original', 'N/A')}")
                
                with col_std:
                    st.markdown("#### ✨ 표준화된 데이터")
                    st.text(f"시험명: {item.get('test_name', 'N/A')}")
                    st.text(f"분류: {item.get('category', 'N/A')}")
                
                # 마스터 정보 상세 표시
                st.markdown("#### 📋 마스터 정보")
                st.json({
                    "id": master.get('id'),
                    "std_name": master.get('std_name'),
                    "std_category": master.get('std_category'),
                    "ref_standard": master.get('ref_standard'),
                    "aliases": master.get('aliases', [])
                })
            
            st.divider()
            
            # 편집 가능한 필드들
            col1, col2 = st.columns(2)
            
            with col1:
                item['test_name'] = st.text_input(
                    "시험명",
                    value=item.get('test_name
