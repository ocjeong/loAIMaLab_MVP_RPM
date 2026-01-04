import streamlit as st
import pandas as pd
from datetime import datetime
import os
from modules.database import DatabaseManager
from modules.gemini_api import GeminiAPI
from modules.parser import DocumentParser
from modules.scheduler import SchedulerManager
from utils.helpers import init_session_state, save_excel

# 페이지 설정
st.set_page_config(
    page_title="RPM - Reliable Planning Manager",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 세션 상태 초기화
init_session_state()

# 데이터베이스 매니저 초기화
db = DatabaseManager()

# 사이드바
with st.sidebar:
    st.title("⚙️ RPM")
    st.markdown("### Reliable Planning Manager")
    st.markdown("---")
    
    # Database Export 기능
    st.markdown("### 📊 Database Export")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📋 Master Test", use_container_width=True):
            csv = db.export_to_csv('master')
            st.download_button(
                label="Download",
                data=csv,
                file_name=f"Master_Test_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                key="download_master"
            )
    
    with col2:
        if st.button("📝 Request Info", use_container_width=True):
            csv = db.export_to_csv('request')
            st.download_button(
                label="Download",
                data=csv,
                file_name=f"Request_Info_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                key="download_request"
            )
    
    col3, col4 = st.columns(2)
    
    with col3:
        if st.button("🧪 Test Item", use_container_width=True):
            csv = db.export_to_csv('test_item')
            st.download_button(
                label="Download",
                data=csv,
                file_name=f"Test_Item_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                key="download_test"
            )
    
    with col4:
        if st.button("👥 User List", use_container_width=True):
            csv = db.export_to_csv('user')
            st.download_button(
                label="Download",
                data=csv,
                file_name=f"User_List_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                key="download_user"
            )
    
    st.markdown("---")
    st.markdown("### ℹ️ 정보")
    st.info("Blower Motor Test Support System")

# 메인 화면 라우팅
if 'current_screen' not in st.session_state:
    st.session_state.current_screen = 'user_selection'

# 3.1. 사용자 선택 화면
if st.session_state.current_screen == 'user_selection':
    st.title("👤 사용자 선택")
    
    # 3.1.1. 사용자 선택 메뉴
    col1, col2 = st.columns([3, 1])
    
    with col1:
        users = db.get_users()
        user_names = users['user_name'].tolist() if not users.empty else []
        
        selected_user = st.selectbox(
            "사용자 선택",
            options=user_names,
            key="selected_user"
        )
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("➕ 사용자 추가", use_container_width=True):
            st.session_state.show_add_user = True
    
    # 사용자 추가 다이얼로그
    if st.session_state.get('show_add_user', False):
        with st.form("add_user_form"):
            new_user_name = st.text_input("새 사용자 이름")
            col1, col2 = st.columns(2)
            
            with col1:
                submitted = st.form_submit_button("추가", use_container_width=True)
            with col2:
                cancelled = st.form_submit_button("취소", use_container_width=True)
            
            if submitted and new_user_name:
                db.add_user(new_user_name)
                st.success(f"사용자 '{new_user_name}' 추가 완료!")
                st.session_state.show_add_user = False
                st.rerun()
            
            if cancelled:
                st.session_state.show_add_user = False
                st.rerun()
    
    # 사용자 선택 시 마지막 접속 시간 업데이트
    if selected_user:
        user_id = users[users['user_name'] == selected_user]['id'].values[0]
        db.update_last_access(user_id)
        st.session_state.current_user_id = user_id
        st.session_state.current_user_name = selected_user
    
    st.markdown("---")
    
    # 3.1.2. 일정 확인 박스
    st.subheader("📅 시험 일정")
    
    if selected_user:
        schedule_data = db.get_user_schedule(user_id)
        
        if not schedule_data.empty:
            # 월별 필터
            current_month = datetime.now().strftime("%Y-%m")
            selected_month = st.date_input(
                "월 선택",
                value=datetime.now(),
                key="month_selector"
            ).strftime("%Y-%m")
            
            # 간단한 일정 표시
            st.dataframe(
                schedule_data,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("등록된 시험 일정이 없습니다.")
    
    st.markdown("---")
    
    # 3.1.3. 의뢰 선택 메뉴
    st.subheader("📋 의뢰 관리")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        if selected_user:
            requests = db.get_user_requests(user_id)
            request_options = ["선택하세요..."] + [
                f"{req['id']} - {req['project']}" 
                for _, req in requests.iterrows()
            ]
            
            selected_request = st.selectbox(
                "기존 의뢰 선택",
                options=request_options,
                key="selected_request"
            )
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("✏️ 의뢰 수정", use_container_width=True):
            if selected_request and selected_request != "선택하세요...":
                request_id = selected_request.split(" - ")[0]
                st.session_state.editing_request_id = request_id
                st.session_state.current_screen = 'test_item_data'
                st.rerun()
            else:
                st.warning("수정할 의뢰를 선택해주세요.")
    
    # 3.1.4. 새 의뢰 버튼
    st.markdown("---")
    
    uploaded_file = st.file_uploader(
        "테스트 스펙 파일 업로드 (PDF, DOCX)",
        type=['pdf', 'docx'],
        key="spec_file_upload"
    )
    
    if uploaded_file and st.button("🆕 새 의뢰 생성", type="primary", use_container_width=True):
        with st.spinner("문서를 분석하고 있습니다..."):
            # API 키 확인
            api_key = os.getenv('GEMINI_API_KEY', '')
            
            if not api_key:
                st.error("⚠️ GEMINI_API_KEY가 설정되지 않았습니다. Streamlit Cloud Secrets에 API 키를 추가해주세요.")
            else:
                try:
                    # 문서 파싱
                    parser = DocumentParser(api_key)
                    extracted_data = parser.parse_document(uploaded_file)
                    
                    st.session_state.extracted_data = extracted_data
                    st.session_state.editing_request_id = None
                    st.session_state.current_screen = 'test_item_data'
                    st.success("문서 분석 완료!")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"문서 분석 중 오류가 발생했습니다: {str(e)}")

# 3.2. 시험 의뢰 항목 데이터 화면
elif st.session_state.current_screen == 'test_item_data':
    st.title("📝 시험 의뢰 항목 데이터")
    
    # 뒤로 가기 버튼
    if st.button("← 사용자 선택으로 돌아가기"):
        st.session_state.current_screen = 'user_selection'
        st.rerun()
    
    st.markdown("---")
    
    # 3.2.1. 의뢰 추출 데이터 박스
    st.subheader("🔍 추출된 데이터")
    
    # 기존 의뢰 수정 또는 새 의뢰
    if st.session_state.get('editing_request_id'):
        request_data = db.get_request_data(st.session_state.editing_request_id)
        test_items = db.get_test_items(st.session_state.editing_request_id)
        
        st.info(f"의뢰 ID: {request_data['id']} | 발주처: {request_data['client']} | 프로젝트: {request_data['project']}")
    else:
        if 'extracted_data' in st.session_state:
            test_items = pd.DataFrame(st.session_state.extracted_data.get('test_items', []))
            request_info = st.session_state.extracted_data.get('request_info', {})
            
            st.info(f"발주처: {request_info.get('client', 'N/A')} | 프로젝트: {request_info.get('project', 'N/A')}")
        else:
            st.warning("추출된 데이터가 없습니다.")
            test_items = pd.DataFrame()
    
    # Expandable tree view 형태로 표시
    if not test_items.empty:
        edited_items = []
        
        for idx, item in test_items.iterrows():
            with st.expander(f"🧪 {item.get('test_name', 'Unknown Test')}"):
                edited_item = {}
                
                col1, col2 = st.columns(2)
                
                with col1:
                    edited_item['test_name'] = st.text_input(
                        "시험명",
                        value=item.get('test_name', ''),
                        key=f"test_name_{idx}"
                    )
                    edited_item['category'] = st.text_input(
                        "분류",
                        value=item.get('category', ''),
                        key=f"category_{idx}"
                    )
                    edited_item['ref_standard'] = st.text_input(
                        "참조 규격",
                        value=item.get('ref_standard', ''),
                        key=f"ref_standard_{idx}"
                    )
                    edited_item['sample_assembly'] = st.text_input(
                        "시료 구성",
                        value=item.get('sample_assembly', ''),
                        key=f"sample_assembly_{idx}"
                    )
                    edited_item['test_sample_no'] = st.text_input(
                        "샘플 번호",
                        value=item.get('test_sample_no', ''),
                        key=f"test_sample_no_{idx}"
                    )
                
                with col2:
                    edited_item['sample_count'] = st.text_input(
                        "시료 수",
                        value=item.get('sample_count', ''),
                        key=f"sample_count_{idx}"
                    )
                    edited_item['test_duration'] = st.text_input(
                        "시험 기간 (days)",
                        value=item.get('test_duration', ''),
                        key=f"test_duration_{idx}"
                    )
                    edited_item['test_equipment'] = st.text_input(
                        "시험 장비",
                        value=item.get('test_equipment', ''),
                        key=f"test_equipment_{idx}"
                    )
                    edited_item['test_master_id'] = st.text_input(
                        "마스터 ID",
                        value=item.get('test_master_id', ''),
                        key=f"test_master_id_{idx}"
                    )
                
                # Custom specs (JSON)
                st.markdown("**특수 요구사항**")
                custom_specs = item.get('custom_specs', {})
                if isinstance(custom_specs, str):
                    import json
                    try:
                        custom_specs = json.loads(custom_specs)
                    except:
                        custom_specs = {}
                
                edited_item['custom_specs'] = st.text_area(
                    "Custom Specs (JSON)",
                    value=str(custom_specs),
                    key=f"custom_specs_{idx}",
                    height=100
                )
                
                edited_items.append(edited_item)
        
        st.session_state.edited_test_items = edited_items
    else:
        st.info("시험 항목이 없습니다.")
    
    st.markdown("---")
    
    # 3.2.2. 계획서 생성 버튼 & 3.2.3. 의뢰 데이터 저장 버튼
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📋 계획서 생성", type="primary", use_container_width=True):
            if st.session_state.get('edited_test_items'):
                # 데이터 저장
                if st.session_state.get('editing_request_id'):
                    request_id = st.session_state.editing_request_id
                else:
                    request_id = db.save_request(
                        st.session_state.current_user_id,
                        st.session_state.extracted_data.get('request_info', {}),
                        st.session_state.edited_test_items
                    )
                    st.session_state.current_request_id = request_id
                
                st.success("✅ 데이터가 저장되었습니다!")
                st.session_state.current_screen = 'plan_draft'
                st.rerun()
            else:
                st.warning("저장할 데이터가 없습니다.")
    
    with col2:
        if st.button("💾 의뢰 데이터 저장", use_container_width=True):
            if st.session_state.get('edited_test_items'):
                if st.session_state.get('editing_request_id'):
                    db.update_request(
                        st.session_state.editing_request_id,
                        st.session_state.edited_test_items
                    )
                else:
                    request_id = db.save_request(
                        st.session_state.current_user_id,
                        st.session_state.extracted_data.get('request_info', {}),
                        st.session_state.edited_test_items
                    )
                    st.session_state.current_request_id = request_id
                
                st.success("✅ 데이터가 저장되었습니다!")
            else:
                st.warning("저장할 데이터가 없습니다.")

# 3.3. 계획서 초안 작성 화면
elif st.session_state.current_screen == 'plan_draft':
    st.title("📊 계획서 초안 작성")
    
    # 뒤로 가기 버튼
    if st.button("← 시험 항목 데이터로 돌아가기"):
        st.session_state.current_screen = 'test_item_data'
        st.rerun()
    
    st.markdown("---")
    
    # 3.3.1. 계획서 출력 박스
    st.subheader("📋 계획서 초안")
    
    if st.session_state.get('edited_test_items'):
        # 계획서 데이터 생성
        plan_data = []
        
        for idx, item in enumerate(st.session_state.edited_test_items):
            plan_row = {
                '포함': True,
                '순번': idx + 1,
                '시험명': item.get('test_name', ''),
                '분류': item.get('category', ''),
                '참조 규격': item.get('ref_standard', ''),
                '시료 구성': item.get('sample_assembly', ''),
                '시료 수': item.get('sample_count', ''),
                '시험 기간': item.get('test_duration', ''),
                '시험 장비': item.get('test_equipment', ''),
            }
            plan_data.append(plan_row)
        
        plan_df = pd.DataFrame(plan_data)
        
        # 편집 가능한 데이터 에디터
        edited_plan = st.data_editor(
            plan_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                '포함': st.column_config.CheckboxColumn(
                    '포함',
                    help="계획서에 포함 여부",
                    default=True
                )
            },
            key="plan_editor"
        )
        
        st.session_state.final_plan = edited_plan
    else:
        st.warning("계획서를 생성할 데이터가 없습니다.")
    
    st.markdown("---")
    
    # 3.3.2. 계획서 저장 버튼 & 3.3.3. 일정 생성 버튼
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("💾 계획서 저장 (Excel)", use_container_width=True):
            if st.session_state.get('final_plan') is not None:
                excel_data = save_excel(st.session_state.final_plan)
                
                st.download_button(
                    label="📥 Excel 다운로드",
                    data=excel_data,
                    file_name=f"Test_Plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
                st.success("✅ 계획서가 준비되었습니다!")
            else:
                st.warning("저장할 계획서가 없습니다.")
    
    with col2:
        if st.button("📅 일정 생성", type="primary", use_container_width=True):
            if st.session_state.get('final_plan') is not None:
                st.session_state.current_screen = 'schedule'
                st.rerun()
            else:
                st.warning("일정을 생성할 계획서가 없습니다.")

# 3.4. 시험 일정 관리 화면
elif st.session_state.current_screen == 'schedule':
    st.title("📅 시험 일정 관리")
    
    # 뒤로 가기 버튼
    if st.button("← 계획서 초안으로 돌아가기"):
        st.session_state.current_screen = 'plan_draft'
        st.rerun()
    
    st.markdown("---")
    
    # 3.4.1. 타임라인(d-day) 확인 박스
    st.subheader("📊 Gantt Chart")
    
    if st.session_state.get('final_plan') is not None:
        scheduler = SchedulerManager()
        
        # 포함된 항목만 필터링
        included_items = st.session_state.final_plan[
            st.session_state.final_plan['포함'] == True
        ]
        
        if not included_items.empty:
            # Gantt 차트 생성
            fig = scheduler.create_gantt_chart(included_items)
            st.plotly_chart(fig, use_container_width=True)
            
            # 상세 일정 테이블
            st.subheader("📋 상세 일정")
            schedule_details = scheduler.calculate_schedule(included_items)
            st.dataframe(schedule_details, use_container_width=True, hide_index=True)
            
            st.session_state.schedule_details = schedule_details
        else:
            st.info("포함된 시험 항목이 없습니다.")
    else:
        st.warning("일정을 생성할 데이터가 없습니다.")
    
    st.markdown("---")
    
    # 3.4.2. 타임라인(d-day) 저장 버튼
    if st.button("💾 일정 저장", type="primary", use_container_width=True):
        if st.session_state.get('schedule_details') is not None:
            # DB에 일정 저장
            request_id = st.session_state.get('current_request_id') or st.session_state.get('editing_request_id')
            
            if request_id:
                db.save_schedule(
                    st.session_state.current_user_id,
                    request_id,
                    st.session_state.schedule_details
                )
                st.success("✅ 일정이 저장되었습니다!")
                
                # 완료 후 사용자 선택 화면으로
                if st.button("🏠 처음으로 돌아가기"):
                    st.session_state.current_screen = 'user_selection'
                    st.rerun()
            else:
                st.error("의뢰 ID를 찾을 수 없습니다.")
        else:
            st.warning("저장할 일정이 없습니다.")

# 푸터
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666; padding: 20px;'>
        <p>RPM - Reliable Planning Manager v1.0</p>
        <p>Blower Motor Test Support System</p>
    </div>
    """,
    unsafe_allow_html=True
)
