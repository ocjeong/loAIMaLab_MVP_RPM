import streamlit as st
import pandas as pd
from datetime import datetime
import json
from modules.database import DatabaseManager
from modules.llm_handler import LLMHandler
from modules.standardization import standardize_test_item, get_master_by_id
from modules.planning import PlanningModule
from modules.scheduling import SchedulingModule
from utils.helpers import format_date, generate_id

# 페이지 설정
st.set_page_config(
    page_title="RPM - Reliable Planning Manager",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 세션 상태 초기화
if 'db_manager' not in st.session_state:
    st.session_state.db_manager = DatabaseManager()
    
if 'current_user' not in st.session_state:
    st.session_state.current_user = None
    
if 'current_request' not in st.session_state:
    st.session_state.current_request = None
    
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'user_selection'
    
if 'extracted_data' not in st.session_state:
    st.session_state.extracted_data = None
    
if 'llm_handler' not in st.session_state:
    st.session_state.llm_handler = LLMHandler()

# 사이드바
with st.sidebar:
    st.title("🔧 RPM System")
    st.markdown("---")
    
    # 현재 세션 정보
    st.subheader("📊 현재 세션 정보")
    if st.session_state.current_user:
        st.info(f"**사용자:** {st.session_state.current_user['user_name']}")
    else:
        st.warning("사용자를 선택해주세요")
        
    if st.session_state.current_request:
        st.info(f"**의뢰 ID:** {st.session_state.current_request}")
    else:
        st.warning("의뢰를 선택하거나 생성해주세요")
    
    st.markdown("---")
    
    # Database Export 기능
    st.subheader("💾 Database Export")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Master Test", use_container_width=True):
            csv = st.session_state.db_manager.export_to_csv('master')
            st.download_button(
                label="Download",
                data=csv,
                file_name=f"Master_Test_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    
    with col2:
        if st.button("Request Info", use_container_width=True):
            csv = st.session_state.db_manager.export_to_csv('request')
            st.download_button(
                label="Download",
                data=csv,
                file_name=f"Request_Info_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    
    col3, col4 = st.columns(2)
    
    with col3:
        if st.button("Test Item", use_container_width=True):
            csv = st.session_state.db_manager.export_to_csv('test_item')
            st.download_button(
                label="Download",
                data=csv,
                file_name=f"Test_Item_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    
    with col4:
        if st.button("User List", use_container_width=True):
            csv = st.session_state.db_manager.export_to_csv('user')
            st.download_button(
                label="Download",
                data=csv,
                file_name=f"User_List_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )

# 메인 컨텐츠
def page_user_selection():
    """3.1. 사용자 선택 화면"""
    st.title("👤 사용자 선택")
    
    col1, col2 = st.columns([2, 3])
    
    with col1:
        st.subheader("사용자 선택 메뉴")
        
        # 사용자 목록 로드
        users = st.session_state.db_manager.load_users()
        user_names = users['user_name'].tolist() if not users.empty else []
        
        selected_user = st.selectbox(
            "사용자를 선택하세요",
            options=user_names,
            index=0 if user_names else None
        )
        
        # 사용자 추가
        with st.expander("➕ 새 사용자 추가"):
            new_user_name = st.text_input("사용자 이름")
            if st.button("추가", use_container_width=True):
                if new_user_name:
                    user_id = generate_id('U', len(users) + 1)
                    st.session_state.db_manager.add_user(user_id, new_user_name)
                    st.success(f"사용자 '{new_user_name}' 추가 완료!")
                    st.rerun()
                else:
                    st.error("사용자 이름을 입력해주세요")
        
        # 사용자 선택 확인
        if selected_user and st.button("선택 확인", type="primary", use_container_width=True):
            user_data = users[users['user_name'] == selected_user].iloc[0]
            st.session_state.current_user = user_data.to_dict()
            st.session_state.db_manager.update_user_access(user_data['id'])
            st.success(f"'{selected_user}' 사용자로 로그인했습니다")
            st.rerun()
    
    with col2:
        st.subheader("📅 일정 확인")
        
        if st.session_state.current_user:
            user_id = st.session_state.current_user['id']
            
            # 의뢰 목록 로드
            requests = st.session_state.db_manager.load_requests_by_user(user_id)
            
            if not requests.empty:
                # 의뢰 선택 메뉴
                request_options = [f"{r['id']} - {r['project']}" for _, r in requests.iterrows()]
                selected_request = st.selectbox(
                    "의뢰 선택",
                    options=["전체 일정"] + request_options
                )
                
                # Gantt Chart 표시
                if selected_request == "전체 일정":
                    st.info("전체 시험 일정을 표시합니다")
                    # 전체 일정 Gantt Chart (구현 필요)
                    st.plotly_chart(
                        SchedulingModule.create_gantt_chart(requests),
                        use_container_width=True
                    )
                else:
                    request_id = selected_request.split(" - ")[0]
                    st.session_state.current_request = request_id
                    
                    # 선택된 의뢰의 시험 항목 로드
                    test_items = st.session_state.db_manager.load_test_items_by_request(request_id)
                    
                    if not test_items.empty:
                        st.plotly_chart(
                            SchedulingModule.create_gantt_chart_from_items(test_items),
                            use_container_width=True
                        )
                    
                    # 의뢰 수정 버튼
                    if st.button("📝 의뢰 수정", use_container_width=True):
                        st.session_state.current_page = 'edit_extraction'
                        request_data = requests[requests['id'] == request_id].iloc[0]
                        st.session_state.extracted_data = json.loads(request_data['final_data'])
                        st.rerun()
            else:
                st.info("등록된 의뢰가 없습니다")
        else:
            st.warning("먼저 사용자를 선택해주세요")
    
    # 새 의뢰 버튼
    st.markdown("---")
    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
    with col_btn1:
        if st.button("📄 새 의뢰 생성", type="primary", use_container_width=True):
            if st.session_state.current_user:
                st.session_state.current_page = 'new_request'
                st.rerun()
            else:
                st.error("먼저 사용자를 선택해주세요")


def page_new_request():
    """새 의뢰 생성 페이지"""
    st.title("📄 새 의뢰 생성")
    
    st.info("시험 규격 파일을 업로드하여 새로운 의뢰를 생성합니다")
    
    uploaded_file = st.file_uploader(
        "시험 규격 파일 업로드 (PDF, DOCX)",
        type=['pdf', 'docx'],
        help="PDF 또는 DOCX 형식의 시험 규격 문서를 업로드하세요"
    )
    
    if uploaded_file is not None:
        st.success(f"파일 업로드 완료: {uploaded_file.name}")
        
        if st.button("🔍 문서 분석 시작", type="primary"):
            with st.spinner("문서를 분석 중입니다... 잠시만 기다려주세요"):
                try:
                    # LLM을 이용한 문서 파싱 및 추출
                    extracted_data = st.session_state.llm_handler.extract_test_data(uploaded_file)
                    
                    if extracted_data:
                        st.session_state.extracted_data = extracted_data
                        
                        # 새 의뢰 ID 생성
                        requests = st.session_state.db_manager.load_requests()
                        request_id = generate_id('R', len(requests) + 1)
                        st.session_state.current_request = request_id
                        
                        st.success("✅ 문서 분석이 완료되었습니다!")
                        st.session_state.current_page = 'edit_extraction'
                        st.rerun()
                    else:
                        st.error("문서 추출에 실패했습니다")
                        
                except Exception as e:
                    st.error(f"오류 발생: {str(e)}")
    
    if st.button("⬅️ 돌아가기"):
        st.session_state.current_page = 'user_selection'
        st.rerun()


def page_edit_extraction():
    """3.2. 추출 시험 규격 편집 화면"""
    st.title("📋 추출 시험 규격 편집")
    
    if not st.session_state.extracted_data:
        st.error("추출된 데이터가 없습니다")
        if st.button("⬅️ 돌아가기"):
            st.session_state.current_page = 'user_selection'
            st.rerun()
        return
    
    data = st.session_state.extracted_data
    
    # 의뢰 정보 표시
    st.subheader("📌 의뢰 정보")
    col1, col2 = st.columns(2)
    with col1:
        client = st.text_input("발주처", value=data.get('request_info', {}).get('client', ''))
    with col2:
        project = st.text_input("프로젝트명", value=data.get('request_info', {}).get('project', ''))
    
    data['request_info']['client'] = client
    data['request_info']['project'] = project
    
    st.markdown("---")
    st.subheader("🔬 시험 항목 데이터")
    
    # 시험 항목 편집
    test_items = data.get('test_items', [])
    
    for idx, item in enumerate(test_items):
        # 표준화 적용
        standardized_item = standardize_test_item(item.copy())
        
        # 매칭 상태 표시
        is_matched = bool(item.get('test_master_id'))
        
        if is_matched:
            master_info = get_master_by_id(item['test_master_id'])
            icon = "✅"
            status = f"[마스터: {item['test_master_id']}]"
            status_color = "green"
        else:
            master_info = None
            icon = "⚠️"
            status = "[미매칭]"
            status_color = "orange"
        
        with st.expander(f"{icon} {idx+1}. {standardized_item.get('test_name', '시험명 없음')} {status}"):
            col_left, col_right = st.columns(2)
            
            with col_left:
                st.markdown("**📄 원본 추출 데이터**")
                st.text_input(
                    "원본 시험명",
                    value=item.get('test_name_original', item.get('test_name', '')),
                    key=f"orig_name_{idx}",
                    disabled=True
                )
                st.text_input(
                    "원본 분류",
                    value=item.get('category_original', item.get('category', '')),
                    key=f"orig_cat_{idx}",
                    disabled=True
                )
            
            with col_right:
                st.markdown("**✨ 표준화된 데이터**")
                standardized_item['test_name'] = st.text_input(
                    "표준 시험명",
                    value=standardized_item.get('test_name', ''),
                    key=f"std_name_{idx}"
                )
                standardized_item['category'] = st.text_input(
                    "표준 분류",
                    value=standardized_item.get('category', ''),
                    key=f"std_cat_{idx}"
                )
            
            # 마스터 정보 표시
            if master_info:
                st.markdown("**🎯 매칭된 마스터 정보**")
                st.json(master_info)
            
            # 기타 필드 편집
            col1, col2, col3 = st.columns(3)
            
            with col1:
                standardized_item['ref_standard'] = st.text_input(
                    "참조 규격",
                    value=standardized_item.get('ref_standard', ''),
                    key=f"ref_{idx}"
                )
                standardized_item['sample_assembly'] = st.text_input(
                    "시료 구성",
                    value=standardized_item.get('sample_assembly', ''),
                    key=f"assembly_{idx}"
                )
            
            with col2:
                standardized_item['test_sample_no'] = st.text_input(
                    "샘플 번호",
                    value=standardized_item.get('test_sample_no', ''),
                    key=f"sample_no_{idx}"
                )
                standardized_item['sample_count'] = st.text_input(
                    "시료 수",
                    value=standardized_item.get('sample_count', ''),
                    key=f"count_{idx}"
                )
            
            with col3:
                standardized_item['test_duration'] = st.text_input(
                    "시험 기간 (days)",
                    value=standardized_item.get('test_duration', ''),
                    key=f"duration_{idx}"
                )
                standardized_item['test_equipment'] = st.text_input(
                    "시험 장비",
                    value=standardized_item.get('test_equipment', ''),
                    key=f"equipment_{idx}"
                )
            
            # test_master_id 표시 (읽기 전용)
            st.text_input(
                "마스터 ID (자동 매칭)",
                value=item.get('test_master_id', ''),
                key=f"master_id_{idx}",
                disabled=True,
                help="LLM이 자동으로 매칭한 마스터 ID입니다"
            )
            
            # Custom Specs 편집
            st.markdown("**⚙️ 특수 요구사항**")
            custom_specs = standardized_item.get('custom_specs', {})
            custom_specs_json = st.text_area(
                "Custom Specs (JSON)",
                value=json.dumps(custom_specs, ensure_ascii=False, indent=2),
                height=150,
                key=f"custom_{idx}"
            )
            
            try:
                standardized_item['custom_specs'] = json.loads(custom_specs_json)
            except:
                st.warning("JSON 형식이 올바르지 않습니다")
            
            # 업데이트
            test_items[idx] = standardized_item
    
    data['test_items'] = test_items
    
    # 버튼
    st.markdown("---")
    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
    
    with col_btn1:
        if st.button("📝 계획서 생성", type="primary", use_container_width=True):
            # 데이터 저장
            st.session_state.db_manager.save_request(
                request_id=st.session_state.current_request,
                user_id=st.session_state.current_user['id'],
                extracted_data=st.session_state.extracted_data,
                final_data=data,
                client=client,
                project=project
            )
            
            # 마스터 데이터 업데이트
            st.session_state.db_manager.update_master_aliases(data['test_items'])
            
            st.success("✅ 데이터가 저장되었습니다!")
            st.session_state.current_page = 'planning'
            st.rerun()
    
    with col_btn2:
        if st.button("💾 의뢰 데이터 저장", use_container_width=True):
            st.session_state.db_manager.save_request(
                request_id=st.session_state.current_request,
                user_id=st.session_state.current_user['id'],
                extracted_data=st.session_state.extracted_data,
                final_data=data,
                client=client,
                project=project
            )
            
            # 마스터 데이터 업데이트
            st.session_state.db_manager.update_master_aliases(data['test_items'])
            
            st.success("✅ 데이터가 저장되었습니다!")


def page_planning():
    """3.3. 계획서 초안 작성 화면"""
    st.title("📊 계획서 초안 작성")
    
    if not st.session_state.extracted_data:
        st.error("추출된 데이터가 없습니다")
        return
    
    data = st.session_state.extracted_data
    test_items = data.get('test_items', [])
    
    # 계획서 생성
    planning_module = PlanningModule()
    plan_data = planning_module.create_plan(test_items)
    
    # 시험 계획서 출력
    st.subheader("📋 시험 계획서")
    
    # 샘플 데이터 로드 버튼
    if st.button("🔄 샘플 데이터 로드"):
        sample_data = planning_module.load_sample_data()
        plan_data = sample_data
        st.success("샘플 데이터를 불러왔습니다")
    
    # 그룹별로 표시
    groups = {}
    for item in plan_data:
        category = item.get('category', 'Other')
        if category not in groups:
            groups[category] = []
        groups[category].append(item)
    
    for category, items in groups.items():
        st.markdown(f"### {category}")
        
        # 테이블 형태로 표시
        df_items = pd.DataFrame(items)
        
        # 편집 가능한 데이터 에디터
        edited_df = st.data_editor(
            df_items,
            use_container_width=True,
            num_rows="dynamic",
            column_config={
                "test_name": st.column_config.TextColumn("시험명", width="medium"),
                "category": st.column_config.TextColumn("분류", width="small"),
                "ref_standard": st.column_config.TextColumn("참조 규격", width="small"),
                "sample_count": st.column_config.NumberColumn("시료 수", width="small"),
                "test_duration": st.column_config.NumberColumn("기간(days)", width="small"),
            }
        )
        
        # 업데이트된 데이터 반영
        groups[category] = edited_df.to_dict('records')
    
    # 전체 계획 데이터 업데이트
    plan_data = []
    for items in groups.values():
        plan_data.extend(items)
    
    # 시료 수 검증
    total_samples = planning_module.calculate_total_samples(plan_data)
    st.info(f"**총 필요 시료 수:** {total_samples}개")
    
    # 버튼
    st.markdown("---")
    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
    
    with col_btn1:
        if st.button("📥 계획서 저장 (Excel)", type="primary", use_container_width=True):
            excel_file = planning_module.export_to_excel(
                plan_data,
                st.session_state.current_user['user_name']
            )
            
            st.download_button(
                label="📥 Excel 다운로드",
                data=excel_file,
                file_name=f"Test_Plan_{st.session_state.current_user['user_name']}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
    with col_btn2:
        if st.button("📅 일정 생성", use_container_width=True):
            st.session_state.plan_data = plan_data
            st.session_state.current_page = 'scheduling'
            st.rerun()


def page_scheduling():
    """3.4. 시험 일정 관리 화면"""
    st.title("📅 시험 일정 관리")
    
    if 'plan_data' not in st.session_state or not st.session_state.plan_data:
        st.error("계획서 데이터가 없습니다")
        return
    
    plan_data = st.session_state.plan_data
    
    # 일정 생성
    scheduling_module = SchedulingModule()
    schedule = scheduling_module.create_schedule(plan_data)
    
    st.subheader("📊 타임라인 (D-Day)")
    
    # Gantt Chart 표시
    gantt_fig = scheduling_module.create_gantt_chart_from_schedule(schedule)
    st.plotly_chart(gantt_fig, use_container_width=True)
    
    # 일정 테이블
    st.subheader("📋 상세 일정")
    df_schedule = pd.DataFrame(schedule)
    st.dataframe(df_schedule, use_container_width=True)
    
    # 버튼
    st.markdown("---")
    col_btn1, col_btn2 = st.columns([1, 3])
    
    with col_btn1:
        if st.button("💾 타임라인 저장", type="primary", use_container_width=True):
            # 일정을 DB에 저장
            st.session_state.db_manager.save_schedule(
                request_id=st.session_state.current_request,
                user_id=st.session_state.current_user['id'],
                schedule=schedule
            )
            st.success("✅ 일정이 저장되었습니다!")
            
            # 사용자 선택 화면으로 돌아가기
            if st.button("🏠 메인으로 돌아가기"):
                st.session_state.current_page = 'user_selection'
                st.rerun()


# 페이지 라우팅
page_map = {
    'user_selection': page_user_selection,
    'new_request': page_new_request,
    'edit_extraction': page_edit_extraction,
    'planning': page_planning,
    'scheduling': page_scheduling
}

# 현재 페이지 렌더링
current_page_func = page_map.get(st.session_state.current_page, page_user_selection)
current_page_func()
