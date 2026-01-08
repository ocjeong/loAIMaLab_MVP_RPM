import streamlit as st
from datetime import datetime
import pandas as pd
import json
from modules.database import Database
from modules.llm_handler import LLMHandler
from modules.standardization import Standardization
from modules.planning import PlanningManager
from modules.scheduling import SchedulingManager
from utils.helpers import *

# 페이지 설정
st.set_page_config(
    page_title="RPM - Reliable Planning Manager",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 세션 상태 초기화
init_session_state('current_page', 'user_selection')
init_session_state('current_user_id', None)
init_session_state('current_user_name', None)
init_session_state('current_request_id', None)
init_session_state('extracted_data', None)
init_session_state('test_items', None)
init_session_state('plan_df', None)
init_session_state('dday_schedule', None)

# 데이터베이스 초기화
@st.cache_resource
def get_database():
    return Database()

db = get_database()

# LLM Handler 초기화 (API 키 필요)
def get_llm_handler():
    api_key = st.secrets.get("GEMINI_API_KEY", "")
    if not api_key:
        st.warning("⚠️ Gemini API 키가 설정되지 않았습니다. secrets.toml 파일에 GEMINI_API_KEY를 추가해주세요.")
        return None
    return LLMHandler(api_key)

# 표준화 및 계획 관리자 초기화
standardization = Standardization(db)
planning_manager = PlanningManager()
scheduling_manager = SchedulingManager(db)

# 사이드바
with st.sidebar:
    st.title("🔧 RPM")
    st.caption("Reliable Planning Manager")
    
    st.divider()
    
    # 현재 세션 정보
    st.subheader("📋 Current Session")
    if st.session_state.current_user_name:
        st.write(f"**User:** {st.session_state.current_user_name}")
    if st.session_state.current_request_id:
        st.write(f"**Request:** {st.session_state.current_request_id}")
    
    st.divider()
    
    # 네비게이션
    st.subheader("🧭 Navigation")
    
    if st.button("👤 User Selection", use_container_width=True):
        st.session_state.current_page = 'user_selection'
        st.rerun()
    
    if st.button("📝 Edit Test Items", use_container_width=True):
        if st.session_state.extracted_data:
            st.session_state.current_page = 'edit_items'
            st.rerun()
        else:
            show_warning_message("추출된 데이터가 없습니다.")
    
    if st.button("📊 Create Plan", use_container_width=True):
        if st.session_state.test_items:
            st.session_state.current_page = 'create_plan'
            st.rerun()
        else:
            show_warning_message("시험 항목 데이터가 없습니다.")
    
    if st.button("📅 Schedule", use_container_width=True):
        if st.session_state.plan_df is not None:
            st.session_state.current_page = 'schedule'
            st.rerun()
        else:
            show_warning_message("계획서가 생성되지 않았습니다.")
    
    if st.button("📆 View All Schedules", use_container_width=True):
        if st.session_state.current_user_id:
            st.session_state.current_page = 'view_schedules'
            st.rerun()
        else:
            show_warning_message("사용자를 선택해주세요.")
    
    st.divider()
    
    # Database Export
    st.subheader("💾 Database Export")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("User List", use_container_width=True):
            path = db.export_to_csv("User_List")
            with open(path, 'rb') as f:
                st.download_button(
                    label="Download",
                    data=f,
                    file_name="User_List.csv",
                    mime="text/csv"
                )
    
    with col2:
        if st.button("Master Test", use_container_width=True):
            path = db.export_to_csv("Master_Test")
            with open(path, 'rb') as f:
                st.download_button(
                    label="Download",
                    data=f,
                    file_name="Master_Test.csv",
                    mime="text/csv"
                )
    
    col3, col4 = st.columns(2)
    
    with col3:
        if st.button("Request Info", use_container_width=True):
            path = db.export_to_csv("Request_Info")
            with open(path, 'rb') as f:
                st.download_button(
                    label="Download",
                    data=f,
                    file_name="Request_Info.csv",
                    mime="text/csv"
                )
    
    with col4:
        if st.button("Test Item", use_container_width=True):
            path = db.export_to_csv("Test_Item")
            with open(path, 'rb') as f:
                st.download_button(
                    label="Download",
                    data=f,
                    file_name="Test_Item.csv",
                    mime="text/csv"
                )

# 메인 컨텐츠
if st.session_state.current_page == 'user_selection':
    st.title("👤 User Selection")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # 사용자 선택
        users_df = db.get_all_users()
        
        if len(users_df) > 0:
            user_options = users_df['user_name'].tolist()
            selected_user = st.selectbox("Select User", user_options)
            
            if selected_user:
                user_row = users_df[users_df['user_name'] == selected_user].iloc[0]
                st.session_state.current_user_id = user_row['id']
                st.session_state.current_user_name = user_row['user_name']
                db.update_user_access(user_row['id'])
                
                show_success_message(f"User '{selected_user}' selected")
        else:
            st.info("No users found. Please add a new user.")
    
    with col2:
        # 사용자 추가
        st.subheader("Add New User")
        new_user_name = st.text_input("User Name")
        if st.button("Add User", use_container_width=True):
            if new_user_name:
                user_id = db.add_user(new_user_name)
                show_success_message(f"User '{new_user_name}' added (ID: {user_id})")
                st.rerun()
            else:
                show_error_message("Please enter a user name")
    
    st.divider()
    
    # 일정 확인
    if st.session_state.current_user_id:
        st.subheader("📅 Current Month Schedule")
        
        current_month = datetime.now().strftime('%Y-%m')
        schedules = db.get_schedule_items(user_id=st.session_state.current_user_id, 
                                         month=current_month)
        
        if len(schedules) > 0:
            # Gantt 차트 표시
            test_items_df = db.get_test_items()
            schedules_with_names = schedules.merge(
                test_items_df[['id', 'test_name', 'request_id']], 
                left_on='test_item_id', 
                right_on='id',
                how='left'
            )
            
            schedule_data = schedules_with_names.to_dict('records')
            fig = scheduling_manager.create_gantt_chart(
                schedule_data, 
                date_mode=True,
                title=f"Schedule for {current_month}"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No schedules for this month")
    
    st.divider()
    
    # 의뢰 선택 또는 새 의뢰
    if st.session_state.current_user_id:
        st.subheader("📋 Request Management")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 기존 의뢰 선택
            requests_df = db.get_all_requests(user_id=st.session_state.current_user_id)
            
            if len(requests_df) > 0:
                request_options = [f"{row['id']} - {row['client']} ({row['project']})" 
                                 for _, row in requests_df.iterrows()]
                selected_request = st.selectbox("Select Existing Request", 
                                               [""] + request_options)
                
                if selected_request and selected_request != "":
                    request_id = selected_request.split(" - ")[0]
                    
                    if st.button("Edit Request", use_container_width=True):
                        request_data = db.get_request_by_id(request_id)
                        st.session_state.current_request_id = request_id
                        st.session_state.extracted_data = request_data['final_data']
                        st.session_state.test_items = standardization.standardize_test_items(
                            request_data['final_data']
                        )
                        st.session_state.current_page = 'edit_items'
                        st.rerun()
            else:
                st.info("No existing requests")
        
        with col2:
            # 새 의뢰
            st.write("**Create New Request**")
            uploaded_file = st.file_uploader("Upload Test Specification", 
                                            type=['pdf', 'docx'])
            
            if uploaded_file and st.button("Process Document", use_container_width=True):
                llm_handler = get_llm_handler()
                
                if llm_handler:
                    with st.spinner("Processing document..."):
                        # 파일 읽기
                        file_bytes = uploaded_file.read()
                        mime_type = uploaded_file.type
                        
                        # 마스터 데이터 가져오기
                        masters_df = db.get_all_masters()
                        master_data = []
                        for _, row in masters_df.iterrows():
                            master_dict = row.to_dict()
                            if pd.notna(master_dict.get('aliases')):
                                master_dict['aliases'] = json.loads(master_dict['aliases'])
                            else:
                                master_dict['aliases'] = []
                            master_data.append(master_dict)
                        
                        # LLM으로 추출
                        result = llm_handler.extract_test_specifications(
                            file_bytes, mime_type, master_data
                        )
                        
                        if result:
                            # 의뢰 정보 저장
                            request_info = result.get('request_info', {})
                            test_items = result.get('test_items', [])
                            
                            request_id = db.add_request(
                                user_id=st.session_state.current_user_id,
                                extracted_data=test_items,
                                client=request_info.get('client', ''),
                                project=request_info.get('project', '')
                            )
                            
                            # 표준화 적용
                            standardized_items = standardization.standardize_test_items(test_items)
                            
                            st.session_state.current_request_id = request_id
                            st.session_state.extracted_data = standardized_items
                            st.session_state.test_items = standardized_items
                            
                            show_success_message("Document processed successfully!")
                            st.session_state.current_page = 'edit_items'
                            st.rerun()
                        else:
                            show_error_message("Failed to extract data from document")
                else:
                    show_error_message("LLM Handler not initialized")

elif st.session_state.current_page == 'edit_items':
    st.title("📝 Edit Test Items")
    
    if st.session_state.extracted_data:
        st.subheader("Extracted and Standardized Test Items")
        
        # 각 시험 항목을 expander로 표시
        for idx, item in enumerate(st.session_state.test_items):
            master_id = item.get('test_master_id', '')
            is_matched = master_id and master_id != ''
            
            # 아이콘 설정
            icon = "✅" if is_matched else "⚠️"
            status = f"[Master: {master_id}]" if is_matched else "[Unmatched]"
            
            with st.expander(f"{icon} {item.get('test_name', 'Unnamed Test')} {status}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Original Data**")
                    st.text_input("Original Name", 
                                 value=item.get('test_name_original', ''),
                                 key=f"orig_name_{idx}",
                                 disabled=True)
                    st.text_input("Original Category", 
                                 value=item.get('category_original', ''),
                                 key=f"orig_cat_{idx}",
                                 disabled=True)
                
                with col2:
                    st.write("**Standardized Data**")
                    item['test_name'] = st.text_input("Test Name", 
                                                     value=item.get('test_name', ''),
                                                     key=f"test_name_{idx}")
                    item['category'] = st.text_input("Category", 
                                                    value=item.get('category', ''),
                                                    key=f"category_{idx}")
                
                st.text_input("Master ID (Read-only)", 
                             value=master_id,
                             key=f"master_id_{idx}",
                             disabled=True,
                             help="Automatically matched by LLM")
                
                # 마스터 정보 표시
                if is_matched:
                    master = db.get_master_by_id(master_id)
                    if master:
                        st.json(master)
                
                # 편집 가능한 필드들
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    item['ref_standard'] = st.text_input("Reference Standard",
                                                        value=item.get('ref_standard', ''),
                                                        key=f"ref_std_{idx}")
                    item['sample_assembly'] = st.text_input("Sample Assembly",
                                                           value=item.get('sample_assembly', ''),
                                                           key=f"sample_asm_{idx}")
                
                with col2:
                    item['test_sample_no'] = st.text_input("Sample No",
                                                          value=item.get('test_sample_no', ''),
                                                          key=f"sample_no_{idx}")
                    item['sample_count'] = st.text_input("Sample Count",
                                                        value=item.get('sample_count', ''),
                                                        key=f"sample_cnt_{idx}")
                
                with col3:
                    item['test_duration'] = st.text_input("Duration (days)",
                                                         value=item.get('test_duration', ''),
                                                         key=f"duration_{idx}")
                    item['test_equipment'] = st.text_input("Test Equipment",
                                                          value=item.get('test_equipment', ''),
                                                          key=f"equipment_{idx}")
                
                # Custom Specs
                st.write("**Custom Specifications**")
                custom_specs = item.get('custom_specs', {})
                if isinstance(custom_specs, str):
                    try:
                        custom_specs = json.loads(custom_specs)
                    except:
                        custom_specs = {}
                
                custom_specs_text = st.text_area("Custom Specs (JSON)",
                                                 value=json.dumps(custom_specs, 
                                                                ensure_ascii=False, 
                                                                indent=2),
                                                 key=f"custom_{idx}",
                                                 height=150)
                try:
                    item['custom_specs'] = json.loads(custom_specs_text)
                except:
                    st.warning("Invalid JSON format")
        
        st.divider()
        
        # 버튼들
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("💾 Save Test Items", use_container_width=True):
                # 데이터 업데이트
                db.update_request(st.session_state.current_request_id, 
                                st.session_state.test_items)
                
                # 마스터 업데이트
                standardization.update_masters_from_test_items(st.session_state.test_items)
                
                show_success_message("Test items saved successfully!")
        
        with col2:
            if st.button("📊 Generate Plan", use_container_width=True):
                # 데이터 저장
                db.update_request(st.session_state.current_request_id, 
                                st.session_state.test_items)
                standardization.update_masters_from_test_items(st.session_state.test_items)
                
                # 계획서 생성 페이지로 이동
                st.session_state.current_page = 'create_plan'
                st.rerun()
    else:
        st.warning("No extracted data available")

elif st.session_state.current_page == 'create_plan':
    st.title("📊 Create Test Plan")
    
    if st.session_state.test_items:
        # 계획서 초안 생성
        if st.session_state.plan_df is None:
            with st.spinner("Generating plan..."):
                st.session_state.plan_df = planning_manager.create_draft_plan(
                    st.session_state.test_items
                )
        
        st.subheader("Test Plan Draft")
        
        # 편집 가능한 데이터프레임 표시
        edited_df = st.data_editor(
            st.session_state.plan_df,
            use_container_width=True,
            num_rows="dynamic",
            height=600
        )
        
        st.session_state.plan_df = edited_df
        
        st.divider()
        
        # 버튼들
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📥 Load Sample Data", use_container_width=True):
                # 샘플 데이터 로드
                sample_items = [
                    {
                        'test_name': 'Functional Test',
                        'category': 'Operational and Environmental tests',
                        'sample_assembly': 'Motor only',
                        'sample_count': '9',
                        'test_duration': '1',
                        'test_master_id': 'M006'
                    },
                    {
                        'test_name': 'High Temperature Test',
                        'category': 'Operational and Environmental tests',
                        'sample_assembly': 'Motor only',
                        'sample_count': '3',
                        'test_duration': '5',
                        'test_master_id': 'M002'
                    },
                    {
                        'test_name': 'Low Temperature Test',
                        'category': 'Operational and Environmental tests',
                        'sample_assembly': 'Motor only',
                        'sample_count': '3',
                        'test_duration': '3',
                        'test_master_id': 'M003'
                    }
                ]
                st.session_state.test_items = sample_items
                st.session_state.plan_df = planning_manager.create_draft_plan(sample_items)
                st.rerun()
        
        with col2:
            if st.button("💾 Export to Excel", use_container_width=True):
                filename = planning_manager.export_to_excel(
                    st.session_state.plan_df,
                    st.session_state.current_user_name
                )
                
                with open(filename, 'rb') as f:
                    st.download_button(
                        label="Download Excel",
                        data=f,
                        file_name=filename,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                
                show_success_message(f"Plan exported to {filename}")
        
        with col3:
            if st.button("📅 Create Schedule", use_container_width=True):
                st.session_state.current_page = 'schedule'
                st.rerun()
    else:
        st.warning("No test items available")

elif st.session_state.current_page == 'schedule':
    st.title("📅 Test Scheduling")
    
    if st.session_state.test_items:
        # D-day 일정 생성
        if st.session_state.dday_schedule is None:
            with st.spinner("Creating schedule..."):
                st.session_state.dday_schedule = scheduling_manager.create_dday_schedule(
                    st.session_state.test_items
                )
        
        st.subheader("D-day Timeline")
        
        # Gantt 차트 표시
        fig = scheduling_manager.create_gantt_chart(
            st.session_state.dday_schedule,
            date_mode=False,
            title="Test Schedule (D-day)"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        st.divider()
        
        # 시작일 설정 및 저장
        st.subheader("Set Start Date and Save")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # 기본 시작일 계산
            default_start = scheduling_manager.get_default_start_date(
                st.session_state.current_user_id
            )
            
            start_date = st.date_input("Test Start Date", value=default_start)
        
        with col2:
            st.write("")
            st.write("")
            if st.button("💾 Save Schedule", use_container_width=True):
                # 날짜 기반 일정으로 변환
                date_schedule = scheduling_manager.convert_to_date_schedule(
                    st.session_state.dday_schedule,
                    datetime.combine(start_date, datetime.min.time())
                )
                
                # DB에 저장
                db.add_schedule_items(date_schedule)
                
                show_success_message("Schedule saved successfully!")
                st.session_state.current_page = 'view_schedules'
                st.rerun()
    else:
        st.warning("No test items available")

elif st.session_state.current_page == 'view_schedules':
    st.title("📆 All Test Schedules")
    
    if st.session_state.current_user_id:
        # 월 선택
        col1, col2 = st.columns([3, 1])
        
        with col1:
            selected_month = st.date_input("Select Month", value=datetime.now())
            month_str = selected_month.strftime('%Y-%m')
        
        with col2:
            view_mode = st.radio("View Mode", ["Gantt Chart", "Calendar"])
        
        # 일정 조회
        schedules = db.get_schedule_items(
            user_id=st.session_state.current_user_id,
            month=month_str
        )
        
        if len(schedules) > 0:
            if view_mode == "Gantt Chart":
                # Gantt 차트
                test_items_df = db.get_test_items()
                schedules_with_names = schedules.merge(
                    test_items_df[['id', 'test_name', 'request_id']], 
                    left_on='test_item_id', 
                    right_on='id',
                    how='left'
                )
                
                # 의뢰별로 색상 구분
                schedule_data = schedules_with_names.to_dict('records')
                fig = scheduling_manager.create_gantt_chart(
                    schedule_data,
                    date_mode=True,
                    title=f"Test Schedule - {month_str}"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            else:
                # 캘린더 뷰 (간단한 테이블 형태)
                st.subheader(f"Calendar View - {month_str}")
                
                test_items_df = db.get_test_items()
                schedules_with_names = schedules.merge(
                    test_items_df[['id', 'test_name', 'request_id']], 
                    left_on='test_item_id', 
                    right_on='id',
                    how='left'
                )
                
                display_df = schedules_with_names[[
                    'test_name', 'start_date', 'end_date', 'duration', 'status', 'request_id'
                ]]
                display_df.columns = ['Test Name', 'Start Date', 'End Date', 
                                     'Duration (days)', 'Status', 'Request ID']
                
                st.dataframe(display_df, use_container_width=True)
        else:
            st.info(f"No schedules found for {month_str}")
    else:
        st.warning("Please select a user first")

# 푸터
st.divider()
st.caption("RPM - Reliable Planning Manager v1.0 | Blower Motor Test Support System")
