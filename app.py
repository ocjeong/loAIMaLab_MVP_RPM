import streamlit as st
import pandas as pd
from datetime import datetime
import json
from modules.document_parser import DocumentParser
from modules.data_manager import DataManager
from modules.scheduler import SchedulerManager
from modules.utils import initialize_session_state, show_success_popup

# 페이지 설정
st.set_page_config(
    page_title="RPM - Reliable Planning Manager",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 세션 상태 초기화
initialize_session_state()

# 데이터 매니저 초기화
@st.cache_resource
def get_data_manager():
    return DataManager()

data_manager = get_data_manager()

# 사이드바 - 네비게이션
st.sidebar.title("🔧 RPM")
st.sidebar.markdown("**Reliable Planning Manager**")
st.sidebar.markdown("---")

# 페이지 선택
if 'current_page' not in st.session_state:
    st.session_state.current_page = "user_selection"

# 메인 타이틀
st.title("RPM - Reliable Planning Manager")
st.markdown("### Blower Motor Test Support System")
st.markdown("---")

# ============================================================================
# 5.1. 사용자 선택 화면
# ============================================================================
def user_selection_page():
    st.header("👤 사용자 선택")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("사용자 관리")
        
        # 5.1.1. 사용자 선택 메뉴
        users = data_manager.get_user_list()
        user_names = [user['user_id'] for user in users]
        
        if not user_names:
            st.warning("등록된 사용자가 없습니다. 새 사용자를 추가해주세요.")
            user_names = ["기본사용자"]
        
        selected_user = st.selectbox(
            "사용자 선택",
            user_names,
            key="user_selector"
        )
        
        # 사용자 추가
        st.markdown("---")
        with st.expander("➕ 새 사용자 추가"):
            new_user_name = st.text_input("사용자 이름", key="new_user_input")
            if st.button("사용자 추가", key="add_user_btn"):
                if new_user_name and new_user_name.strip():
                    success = data_manager.add_user(new_user_name.strip())
                    if success:
                        st.success(f"✅ '{new_user_name}' 사용자가 추가되었습니다.")
                        st.rerun()
                    else:
                        st.error("❌ 사용자 추가에 실패했습니다.")
                else:
                    st.warning("⚠️ 사용자 이름을 입력해주세요.")
        
        # 사용자 선택 시 마지막 접속 시간 업데이트
        if selected_user:
            data_manager.update_last_access(selected_user)
            st.session_state.current_user = selected_user
            
            user_info = data_manager.get_user_info(selected_user)
            if user_info:
                st.info(f"📅 마지막 접속: {user_info.get('last_access', 'N/A')}")
        
        st.markdown("---")
        
        # 5.1.3. 의뢰 선택 메뉴
        st.subheader("의뢰 관리")
        
        requests = data_manager.get_user_requests(selected_user)
        request_options = ["선택하세요"] + [
            f"{req['id']} - {req.get('client', 'N/A')} ({req.get('project', 'N/A')})"
            for req in requests
        ]
        
        selected_request = st.selectbox(
            "의뢰 선택",
            request_options,
            key="request_selector"
        )
        
        # 5.1.5. 의뢰 수정 버튼
        if selected_request != "선택하세요":
            request_id = selected_request.split(" - ")[0]
            if st.button("📝 의뢰 수정", key="edit_request_btn", use_container_width=True):
                st.session_state.current_request_id = request_id
                st.session_state.current_page = "test_items"
                st.rerun()
        
        st.markdown("---")
        
        # 5.1.4. 새 의뢰 버튼
        st.subheader("새 의뢰 생성")
        uploaded_file = st.file_uploader(
            "테스트 스펙 파일 업로드",
            type=['pdf', 'docx'],
            key="file_uploader"
        )
        
        if uploaded_file is not None:
            if st.button("🆕 새 의뢰 생성", key="new_request_btn", use_container_width=True):
                with st.spinner("문서를 파싱하고 있습니다..."):
                    parser = DocumentParser()
                    extracted_data = parser.parse_document(uploaded_file)
                    
                    if extracted_data:
                        st.session_state.extracted_data = extracted_data
                        st.session_state.current_request_id = None
                        st.session_state.current_page = "test_items"
                        st.success("✅ 문서 파싱 완료!")
                        st.rerun()
                    else:
                        st.error("❌ 문서 파싱에 실패했습니다.")
    
    with col2:
        # 5.1.2. 일정 확인 박스
        st.subheader("📅 시험 일정")
        
        if selected_user:
            # 월 선택
            current_date = datetime.now()
            selected_month = st.date_input(
                "월 선택",
                value=current_date,
                key="month_selector"
            )
            
            # 선택된 의뢰의 일정 또는 전체 일정 표시
            if selected_request != "선택하세요":
                request_id = selected_request.split(" - ")[0]
                schedule_data = data_manager.get_request_schedule(request_id)
                st.markdown(f"**의뢰 ID: {request_id}의 일정**")
            else:
                schedule_data = data_manager.get_user_schedule(
                    selected_user, 
                    selected_month.year, 
                    selected_month.month
                )
                st.markdown(f"**{selected_user}의 전체 일정**")
            
            if schedule_data and len(schedule_data) > 0:
                # 일정 데이터프레임 표시
                df_schedule = pd.DataFrame(schedule_data)
                st.dataframe(df_schedule, use_container_width=True, height=400)
            else:
                st.info("📭 표시할 일정이 없습니다.")
        else:
            st.info("👈 사용자를 선택해주세요.")


# ============================================================================
# 5.2. 시험 의뢰 항목 데이터 화면
# ============================================================================
def test_items_page():
    st.header("📋 시험 의뢰 항목 데이터")
    
    # 뒤로가기 버튼
    if st.button("← 사용자 선택으로 돌아가기", key="back_to_user"):
        st.session_state.current_page = "user_selection"
        st.rerun()
    
    st.markdown("---")
    
    # 데이터 로드
    if st.session_state.current_request_id:
        # 기존 의뢰 수정
        request_data = data_manager.get_request_data(st.session_state.current_request_id)
        if request_data:
            st.info(f"📝 의뢰 ID: {st.session_state.current_request_id} 수정 중")
            test_items = request_data.get('extracted_data', [])
            request_info = {
                'client': request_data.get('client', ''),
                'project': request_data.get('project', '')
            }
        else:
            st.error("의뢰 데이터를 불러올 수 없습니다.")
            return
    else:
        # 새 의뢰
        if 'extracted_data' in st.session_state:
            extracted = st.session_state.extracted_data
            test_items = extracted.get('test_items', [])
            request_info = extracted.get('request_info', {})
            st.success("🆕 새 의뢰 생성 중")
        else:
            st.warning("추출된 데이터가 없습니다.")
            return
    
    # 의뢰 정보 표시
    col1, col2 = st.columns(2)
    with col1:
        client = st.text_input("발주처", value=request_info.get('client', ''), key="client_input")
    with col2:
        project = st.text_input("프로젝트명", value=request_info.get('project', ''), key="project_input")
    
    st.markdown("---")
    
    # 5.2.1. 의뢰 추출 데이터 박스
    st.subheader("🔍 추출된 시험 항목")
    
    if test_items:
        # 세션 상태에 편집 가능한 데이터 저장
        if 'editable_test_items' not in st.session_state:
            st.session_state.editable_test_items = test_items.copy()
        
        # Expandable tree view로 각 시험 항목 표시
        for idx, item in enumerate(st.session_state.editable_test_items):
            with st.expander(f"**{idx+1}. {item.get('test_name', 'N/A')}**"):
                col1, col2 = st.columns(2)
                
                with col1:
                    item['test_name'] = st.text_input(
                        "시험명", 
                        value=item.get('test_name', ''),
                        key=f"test_name_{idx}"
                    )
                    item['category'] = st.text_input(
                        "분류", 
                        value=item.get('category', ''),
                        key=f"category_{idx}"
                    )
                    item['ref_standard'] = st.text_input(
                        "참조 규격", 
                        value=item.get('ref_standard', ''),
                        key=f"ref_standard_{idx}"
                    )
                    item['sample_assembly'] = st.text_input(
                        "시료 구성", 
                        value=item.get('sample_assembly', ''),
                        key=f"sample_assembly_{idx}"
                    )
                    item['test_sample_no'] = st.text_input(
                        "샘플 번호", 
                        value=item.get('test_sample_no', ''),
                        key=f"test_sample_no_{idx}"
                    )
                
                with col2:
                    item['sample_count'] = st.text_input(
                        "시료 수", 
                        value=item.get('sample_count', ''),
                        key=f"sample_count_{idx}"
                    )
                    item['test_duration'] = st.text_input(
                        "소요 일수", 
                        value=item.get('test_duration', ''),
                        key=f"test_duration_{idx}"
                    )
                    item['test_equipment'] = st.text_input(
                        "시험 장비", 
                        value=item.get('test_equipment', ''),
                        key=f"test_equipment_{idx}"
                    )
                    item['test_master_id'] = st.text_input(
                        "마스터 ID", 
                        value=item.get('test_master_id', ''),
                        key=f"test_master_id_{idx}"
                    )
                
                # Custom specs (JSON)
                st.markdown("**특수 요구사항 (Custom Specs)**")
                custom_specs = item.get('custom_specs', {})
                custom_specs_str = st.text_area(
                    "JSON 형식으로 입력",
                    value=json.dumps(custom_specs, ensure_ascii=False, indent=2),
                    height=150,
                    key=f"custom_specs_{idx}"
                )
                try:
                    item['custom_specs'] = json.loads(custom_specs_str)
                except:
                    st.warning("⚠️ JSON 형식이 올바르지 않습니다.")
    else:
        st.info("추출된 시험 항목이 없습니다.")
    
    st.markdown("---")
    
    # 버튼 영역
    col1, col2, col3 = st.columns([1, 1, 2])
    
    # 5.2.2. 계획서 생성 버튼
    with col1:
        if st.button("📄 계획서 생성", key="generate_plan_btn", use_container_width=True):
            # 데이터 저장
            request_id = save_request_data(client, project)
            if request_id:
                st.session_state.current_request_id = request_id
                st.session_state.current_page = "plan_draft"
                show_success_popup("데이터가 저장되었습니다.")
                st.rerun()
    
    # 5.2.3. 의뢰 데이터 저장 버튼
    with col2:
        if st.button("💾 의뢰 데이터 저장", key="save_request_btn", use_container_width=True):
            request_id = save_request_data(client, project)
            if request_id:
                show_success_popup("데이터가 저장되었습니다.")
                st.session_state.current_request_id = request_id


def save_request_data(client, project):
    """의뢰 데이터 저장 함수"""
    try:
        request_data = {
            'user_id': st.session_state.current_user,
            'client': client,
            'project': project,
            'extracted_data': st.session_state.editable_test_items,
            'final_data': st.session_state.editable_test_items,
            'is_verified': False
        }
        
        if st.session_state.current_request_id:
            # 기존 의뢰 업데이트
            success = data_manager.update_request(
                st.session_state.current_request_id,
                request_data
            )
            return st.session_state.current_request_id if success else None
        else:
            # 새 의뢰 생성
            request_id = data_manager.create_request(request_data)
            return request_id
    except Exception as e:
        st.error(f"❌ 저장 중 오류 발생: {str(e)}")
        return None


# ============================================================================
# 5.3. 계획서 초안 작성 화면
# ============================================================================
def plan_draft_page():
    st.header("📝 계획서 초안 작성")
    
    # 뒤로가기 버튼
    if st.button("← 시험 항목으로 돌아가기", key="back_to_items"):
        st.session_state.current_page = "test_items"
        st.rerun()
    
    st.markdown("---")
    
    # 의뢰 데이터 로드
    if not st.session_state.current_request_id:
        st.warning("의뢰 ID가 없습니다.")
        return
    
    request_data = data_manager.get_request_data(st.session_state.current_request_id)
    if not request_data:
        st.error("의뢰 데이터를 불러올 수 없습니다.")
        return
    
    # 5.3.1. 계획서 출력 박스
    st.subheader("📋 계획서 초안")
    
    test_items = request_data.get('final_data', [])
    
    if test_items:
        # 계획서 데이터프레임 생성
        plan_data = []
        for idx, item in enumerate(test_items):
            plan_row = {
                '포함': True,
                '번호': idx + 1,
                '시험명': item.get('test_name', ''),
                '분류': item.get('category', ''),
                '참조규격': item.get('ref_standard', ''),
                '시료구성': item.get('sample_assembly', ''),
                '시료수': item.get('sample_count', ''),
                '소요일수': item.get('test_duration', ''),
                '시험장비': item.get('test_equipment', ''),
                '특수요구사항': json.dumps(item.get('custom_specs', {}), ensure_ascii=False)
            }
            plan_data.append(plan_row)
        
        # 세션 상태에 저장
        if 'plan_dataframe' not in st.session_state:
            st.session_state.plan_dataframe = pd.DataFrame(plan_data)
        
        # 데이터 에디터로 편집 가능하게 표시
        edited_df = st.data_editor(
            st.session_state.plan_dataframe,
            use_container_width=True,
            num_rows="dynamic",
            column_config={
                "포함": st.column_config.CheckboxColumn(
                    "포함",
                    help="계획서에 포함 여부",
                    default=True,
                )
            },
            hide_index=True,
            key="plan_editor"
        )
        
        st.session_state.plan_dataframe = edited_df
    else:
        st.info("시험 항목이 없습니다.")
    
    st.markdown("---")
    
    # 버튼 영역
    col1, col2, col3 = st.columns([1, 1, 2])
    
    # 5.3.2. 계획서 저장 버튼
    with col1:
        if st.button("💾 계획서 저장 (Excel)", key="save_plan_btn", use_container_width=True):
            try:
                # 포함된 항목만 필터링
                filtered_df = edited_df[edited_df['포함'] == True].copy()
                filtered_df = filtered_df.drop(columns=['포함'])
                
                # Excel 파일로 저장
                filename = f"계획서_{st.session_state.current_request_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                filtered_df.to_excel(filename, index=False, engine='openpyxl')
                
                # 다운로드 버튼
                with open(filename, 'rb') as f:
                    st.download_button(
                        label="📥 계획서 다운로드",
                        data=f,
                        file_name=filename,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                
                show_success_popup("계획서가 저장되었습니다.")
            except Exception as e:
                st.error(f"❌ 저장 중 오류 발생: {str(e)}")
    
    # 5.3.3. 일정 생성 버튼
    with col2:
        if st.button("📅 일정 생성", key="generate_schedule_btn", use_container_width=True):
            # 포함된 항목만 전달
            filtered_items = []
            for idx, row in edited_df.iterrows():
                if row['포함']:
                    filtered_items.append(test_items[idx])
            
            st.session_state.schedule_items = filtered_items
            st.session_state.current_page = "schedule"
            st.rerun()


# ============================================================================
# 5.4. 시험 일정 관리 화면
# ============================================================================
def schedule_page():
    st.header("📅 시험 일정 관리")
    
    # 뒤로가기 버튼
    if st.button("← 계획서로 돌아가기", key="back_to_plan"):
        st.session_state.current_page = "plan_draft"
        st.rerun()
    
    st.markdown("---")
    
    # 일정 데이터 로드
    if 'schedule_items' not in st.session_state or not st.session_state.schedule_items:
        st.warning("일정을 생성할 항목이 없습니다.")
        return
    
    # 5.4.2. 타임라인(d-day) 확인 박스
    st.subheader("📊 Gantt Chart")
    
    # 시작일 선택
    start_date = st.date_input(
        "시험 시작일 (Day 0)",
        value=datetime.now(),
        key="start_date_input"
    )
    
    # 스케줄러 초기화
    scheduler = SchedulerManager()
    
    # Gantt 차트 생성
    gantt_fig = scheduler.create_gantt_chart(
        st.session_state.schedule_items,
        start_date
    )
    
    if gantt_fig:
        st.plotly_chart(gantt_fig, use_container_width=True)
        
        # 일정 요약 테이블
        st.subheader("📋 일정 요약")
        schedule_summary = scheduler.create_schedule_summary(
            st.session_state.schedule_items,
            start_date
        )
        st.dataframe(schedule_summary, use_container_width=True)
    else:
        st.error("Gantt 차트 생성에 실패했습니다.")
    
    st.markdown("---")
    
    # 5.4.3. 타임라인(d-day) 저장 버튼
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("💾 일정 저장", key="save_schedule_btn", use_container_width=True):
            try:
                success = data_manager.save_schedule(
                    st.session_state.current_user,
                    st.session_state.current_request_id,
                    st.session_state.schedule_items,
                    start_date
                )
                
                if success:
                    show_success_popup("일정이 저장되었습니다.")
                    st.success("✅ 일정이 데이터베이스에 저장되었습니다.")
                else:
                    st.error("❌ 일정 저장에 실패했습니다.")
            except Exception as e:
                st.error(f"❌ 저장 중 오류 발생: {str(e)}")


# ============================================================================
# 페이지 라우팅
# ============================================================================
def main():
    # 현재 사용자 표시
    if 'current_user' in st.session_state:
        st.sidebar.success(f"👤 현재 사용자: **{st.session_state.current_user}**")
    
    st.sidebar.markdown("---")
    
    # 페이지 네비게이션
    pages = {
        "user_selection": ("👤 사용자 선택", user_selection_page),
        "test_items": ("📋 시험 항목", test_items_page),
        "plan_draft": ("📝 계획서 작성", plan_draft_page),
        "schedule": ("📅 일정 관리", schedule_page)
    }
    
    # 현재 페이지 표시
    current_page_info = pages.get(st.session_state.current_page)
    if current_page_info:
        st.sidebar.info(f"현재 페이지: **{current_page_info[0]}**")
        current_page_info[1]()
    else:
        user_selection_page()


if __name__ == "__main__":
    main()
