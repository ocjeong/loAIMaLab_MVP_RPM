import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
import base64
from io import BytesIO

from database_manager import DatabaseManager
from llm_handler import LLMHandler
from plan_generator import PlanGenerator
from scheduler import Scheduler
from utils import create_gantt_chart, create_calendar_view
from config import *

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

if 'llm_handler' not in st.session_state:
    st.session_state.llm_handler = LLMHandler(st.session_state.db_manager)

if 'plan_generator' not in st.session_state:
    st.session_state.plan_generator = PlanGenerator(st.session_state.db_manager)

if 'scheduler' not in st.session_state:
    st.session_state.scheduler = Scheduler(st.session_state.db_manager)

if 'current_page' not in st.session_state:
    st.session_state.current_page = 'user_selection'

if 'selected_user_id' not in st.session_state:
    st.session_state.selected_user_id = None

if 'selected_request_id' not in st.session_state:
    st.session_state.selected_request_id = None

if 'current_test_items' not in st.session_state:
    st.session_state.current_test_items = []

if 'current_plan' not in st.session_state:
    st.session_state.current_plan = []

if 'current_schedule' not in st.session_state:
    st.session_state.current_schedule = []

# 사이드바
with st.sidebar:
    st.title("🔧 RPM")
    st.markdown("**Reliable Planning Manager**")
    st.divider()
    
    # 현재 세션 정보
    st.subheader("📊 현재 세션 정보")
    
    if st.session_state.selected_user_id:
        users = st.session_state.db_manager.get_all_users()
        user = users[users['id'] == st.session_state.selected_user_id]
        if len(user) > 0:
            st.info(f"👤 사용자: {user.iloc[0]['user_name']}")
    else:
        st.warning("사용자를 선택해주세요")
    
    if st.session_state.selected_request_id:
        request = st.session_state.db_manager.get_request_by_id(st.session_state.selected_request_id)
        if request:
            st.info(f"📋 의뢰: {request['client']} - {request['project']}")
    
    st.divider()
    
    # 네비게이션
    st.subheader("🧭 화면 전환")
    
    if st.button("🏠 사용자 선택", use_container_width=True):
        st.session_state.current_page = 'user_selection'
        st.rerun()
    
    if st.button("📝 시험 규격 편집", use_container_width=True, 
                disabled=not st.session_state.selected_request_id):
        st.session_state.current_page = 'test_spec_edit'
        st.rerun()
    
    if st.button("📄 계획서 작성", use_container_width=True,
                disabled=not st.session_state.current_test_items):
        st.session_state.current_page = 'plan_creation'
        st.rerun()
    
    if st.button("📅 일정 스케줄링", use_container_width=True,
                disabled=not st.session_state.current_plan):
        st.session_state.current_page = 'scheduling'
        st.rerun()
    
    if st.button("📆 전체 일정 보기", use_container_width=True,
                disabled=not st.session_state.selected_user_id):
        st.session_state.current_page = 'schedule_view'
        st.rerun()
    
    st.divider()
    
    # Database Export
    st.subheader("💾 Database Export")
    
    export_options = ['User List', 'Master Test', 'Request Info', 'Test Item', 'Schedule Item']
    selected_export = st.selectbox("테이블 선택", export_options)
    
    if st.button("CSV 다운로드", use_container_width=True):
        df = st.session_state.db_manager.export_csv(selected_export)
        if df is not None:
            csv = df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 파일 다운로드",
                data=csv,
                file_name=f"{selected_export.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )

# 메인 컨텐츠
def page_user_selection():
    """사용자 선택 화면"""
    st.title("👤 사용자 선택")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("사용자 선택")
        
        # 사용자 목록 불러오기
        users = st.session_state.db_manager.get_all_users()
        
        if len(users) == 0:
            st.warning("등록된 사용자가 없습니다. 새 사용자를 추가해주세요.")
            user_names = []
        else:
            user_names = users['user_name'].tolist()
        
        selected_user_name = st.selectbox(
            "사용자 선택",
            options=user_names,
            key='user_select'
        )
        
        # 사용자 추가
        st.divider()
        with st.expander("➕ 새 사용자 추가"):
            new_user_name = st.text_input("사용자 이름")
            if st.button("추가"):
                if new_user_name:
                    st.session_state.db_manager.add_user(new_user_name)
                    st.success(f"✅ '{new_user_name}' 사용자가 추가되었습니다.")
                    st.rerun()
                else:
                    st.error("사용자 이름을 입력해주세요.")
        
        # 사용자 선택 시 세션 업데이트
        if selected_user_name and len(users) > 0:
            user = users[users['user_name'] == selected_user_name].iloc[0]
            st.session_state.selected_user_id = user['id']
            st.session_state.db_manager.update_last_access(user['id'])
            
            st.success(f"✅ '{selected_user_name}' 선택됨")
        
        st.divider()
        
        # 의뢰 선택
        if st.session_state.selected_user_id:
            st.subheader("기존 의뢰 선택")
            
            requests = st.session_state.db_manager.get_all_requests(st.session_state.selected_user_id)
            
            if len(requests) > 0:
                request_options = [
                    f"{row['id']} - {row['client']} ({row['project']})"
                    for _, row in requests.iterrows()
                ]
                
                selected_request = st.selectbox(
                    "의뢰 선택",
                    options=[''] + request_options,
                    key='request_select'
                )
                
                if selected_request:
                    request_id = selected_request.split(' - ')[0]
                    st.session_state.selected_request_id = request_id
                    
                    if st.button("📝 의뢰 수정"):
                        st.session_state.current_page = 'test_spec_edit'
                        st.rerun()
            else:
                st.info("등록된 의뢰가 없습니다.")
        
        st.divider()
        
        # 새 의뢰 버튼
        if st.session_state.selected_user_id:
            st.subheader("새 의뢰 생성")
            
            uploaded_file = st.file_uploader(
                "시험 규격 파일 업로드",
                type=['pdf', 'docx'],
                key='file_upload'
            )
            
            if uploaded_file and st.button("🆕 새 의뢰 생성", type="primary"):
                with st.spinner("문서를 분석하는 중..."):
                    # 파일 처리
                    file_content = uploaded_file.read()
                    file_type = uploaded_file.type
                    
                    # LLM으로 데이터 추출
                    result = st.session_state.llm_handler.extract_test_data(
                        BytesIO(file_content),
                        file_type
                    )
                    
                    if result:
                        # 의뢰 정보 저장
                        request_info = result.get('request_info', {})
                        test_items = result.get('test_items', [])
                        
                        # 표준화 적용
                        standardized_items = []
                        for item in test_items:
                            standardized_item = st.session_state.llm_handler.standardize_test_item(item)
                            standardized_items.append(standardized_item)
                        
                        # 의뢰 추가
                        request_id = st.session_state.db_manager.add_request(
                            st.session_state.selected_user_id,
                            standardized_items,
                            request_info.get('client', ''),
                            request_info.get('project', '')
                        )
                        
                        st.session_state.selected_request_id = request_id
                        st.session_state.current_test_items = standardized_items
                        
                        st.success("✅ 문서 분석 완료!")
                        st.session_state.current_page = 'test_spec_edit'
                        st.rerun()
                    else:
                        st.error("❌ 문서 분석에 실패했습니다. API 키를 확인해주세요.")
    
    with col2:
        st.subheader("📅 일정 확인")
        
        if st.session_state.selected_user_id:
            # 현재 월 선택
            current_month = datetime.now().strftime('%Y-%m')
            selected_month = st.text_input("조회할 월 (YYYY-MM)", value=current_month)
            
            # 일정 데이터 가져오기
            schedule_df = st.session_state.db_manager.get_schedule_by_user(
                st.session_state.selected_user_id,
                selected_month
            )
            
            if len(schedule_df) > 0:
                # 시험 항목 정보 결합
                test_items_df = pd.read_csv(TEST_ITEM_FILE, encoding='utf-8-sig')
                schedule_with_info = schedule_df.merge(
                    test_items_df[['id', 'test_name', 'request_id', 'category']],
                    left_on='test_item_id',
                    right_on='id',
                    how='left'
                )
                
                # Gantt 차트 생성
                fig = create_gantt_chart(
                    schedule_with_info.to_dict('records'),
                    color_by='request',
                    title=f'{selected_month} 시험 일정'
                )
                
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                
                # 의뢰별 필터링
                if st.session_state.selected_request_id:
                    st.divider()
                    st.subheader("선택된 의뢰의 일정")
                    
                    request_schedule = schedule_with_info[
                        schedule_with_info['request_id'] == st.session_state.selected_request_id
                    ]
                    
                    if len(request_schedule) > 0:
                        fig2 = create_gantt_chart(
                            request_schedule.to_dict('records'),
                            color_by='category',
                            title=f'의뢰 {st.session_state.selected_request_id} 일정'
                        )
                        
                        if fig2:
                            st.plotly_chart(fig2, use_container_width=True)
                    else:
                        st.info("선택된 의뢰의 일정이 없습니다.")
            else:
                st.info("등록된 일정이 없습니다.")
        else:
            st.warning("사용자를 먼저 선택해주세요.")

def page_test_spec_edit():
    """시험 규격 편집 화면"""
    st.title("📝 추출 시험 규격 편집")
    
    if not st.session_state.selected_request_id:
        st.warning("의뢰를 먼저 선택해주세요.")
        return
    
    # 의뢰 정보 불러오기
    request = st.session_state.db_manager.get_request_by_id(st.session_state.selected_request_id)
    
    if not request:
        st.error("의뢰 정보를 찾을 수 없습니다.")
        return
    
    st.info(f"📋 의뢰: {request['client']} - {request['project']}")
    
    # 데이터 로드
    if request['is_verified'] and request['final_data']:
        test_items = request['final_data']
    else:
        test_items = request['extracted_data']
    
    st.session_state.current_test_items = test_items
    
    st.subheader("시험 항목 목록")
    
    # 시험 항목 표시 및 편집
    for idx, item in enumerate(test_items):
        with st.expander(
            f"{'✅' if item.get('test_master_id') else '⚠️'} "
            f"{idx + 1}. {item.get('test_name', 'Unknown Test')}"
        ):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**원본 추출 데이터**")
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
            
            with col2:
                st.markdown("**표준화된 데이터**")
                item['test_name'] = st.text_input(
                    "표준 시험명",
                    value=item.get('test_name', ''),
                    key=f"std_name_{idx}"
                )
                item['category'] = st.text_input(
                    "표준 분류",
                    value=item.get('category', ''),
                    key=f"std_cat_{idx}"
                )
            
            # 마스터 정보 표시
            if item.get('test_master_id'):
                master = st.session_state.db_manager.get_master_by_id(item['test_master_id'])
                if master:
                    st.success(f"✅ 매칭됨: [마스터 ID: {master['id']}]")
                    st.json({
                        'master_id': master['id'],
                        'std_name': master['std_name'],
                        'std_category': master['std_category'],
                        'ref_standard': master['ref_standard'],
                        'aliases': master['aliases']
                    })
            else:
                st.warning("⚠️ [미매칭] - 마스터 데이터와 매칭되지 않음")
            
            st.divider()
            
            # 상세 정보 편집
            col3, col4, col5 = st.columns(3)
            
            with col3:
                item['ref_standard'] = st.text_input(
                    "참조 규격",
                    value=item.get('ref_standard', ''),
                    key=f"ref_{idx}"
                )
                item['sample_assembly'] = st.text_input(
                    "시료 구성",
                    value=item.get('sample_assembly', ''),
                    key=f"assembly_{idx}"
                )
            
            with col4:
                item['test_sample_no'] = st.text_input(
                    "샘플 번호",
                    value=item.get('test_sample_no', ''),
                    key=f"sample_no_{idx}"
                )
                item['sample_count'] = st.text_input(
                    "시료 수",
                    value=item.get('sample_count', ''),
                    key=f"count_{idx}"
                )
            
            with col5:
                item['test_duration'] = st.text_input(
                    "소요 기간 (일)",
                    value=item.get('test_duration', ''),
                    key=f"duration_{idx}"
                )
                item['test_equipment'] = st.text_input(
                    "시험 장비",
                    value=item.get('test_equipment', ''),
                    key=f"equipment_{idx}"
                )
            
            # Custom Specs
            st.markdown("**특수 조건 (Custom Specs)**")
            custom_specs = item.get('custom_specs', {})
            
            if custom_specs:
                for key, value in custom_specs.items():
                    custom_specs[key] = st.text_area(
                        key,
                        value=value,
                        key=f"custom_{idx}_{key}",
                        height=100
                    )
            
            item['custom_specs'] = custom_specs
    
    # 버튼
    col_btn1, col_btn2 = st.columns(2)
    
    with col_btn1:
        if st.button("📄 계획서 생성", type="primary", use_container_width=True):
            # 데이터 저장
            st.session_state.db_manager.update_request_final_data(
                st.session_state.selected_request_id,
                test_items
            )
            
            # 시험 항목 DB에 저장
            test_item_ids = st.session_state.db_manager.add_test_items(
                test_items,
                st.session_state.selected_request_id
            )
            
            # 마스터 업데이트
            for item in test_items:
                if item.get('test_master_id'):
                    # 유사어 추가
                    if item.get('test_name_original'):
                        st.session_state.db_manager.update_master_aliases(
                            item['test_master_id'],
                            item['test_name_original']
                        )
                else:
                    # 새 마스터 추가
                    new_master_id = st.session_state.db_manager.add_master(item)
                    item['test_master_id'] = new_master_id
            
            st.success("✅ 데이터가 저장되었습니다!")
            st.session_state.current_page = 'plan_creation'
            st.rerun()
    
    with col_btn2:
        if st.button("💾 의뢰 데이터 저장", use_container_width=True):
            # 데이터 저장
            st.session_state.db_manager.update_request_final_data(
                st.session_state.selected_request_id,
                test_items
            )
            
            # 시험 항목 DB에 저장
            test_item_ids = st.session_state.db_manager.add_test_items(
                test_items,
                st.session_state.selected_request_id
            )
            
            # 마스터 업데이트
            for item in test_items:
                if item.get('test_master_id'):
                    if item.get('test_name_original'):
                        st.session_state.db_manager.update_master_aliases(
                            item['test_master_id'],
                            item['test_name_original']
                        )
                else:
                    new_master_id = st.session_state.db_manager.add_master(item)
                    item['test_master_id'] = new_master_id
            
            st.success("✅ 데이터가 저장되었습니다!")

def page_plan_creation():
    """계획서 작성 화면"""
    st.title("📄 시험 계획서 초안 작성")
    
    if not st.session_state.current_test_items:
        st.warning("시험 항목 데이터가 없습니다.")
        return
    
    # 계획서 생성
    if not st.session_state.current_plan:
        with st.spinner("계획서를 생성하는 중..."):
            plan_data = st.session_state.plan_generator.generate_plan(
                st.session_state.current_test_items
            )
            st.session_state.current_plan = plan_data
    
    st.subheader("시험 계획서 초안")
    
    # 샘플 데이터 로드 버튼
    if st.button("🔄 추출 데이터 로드"): # 문구 수
        st.session_state.current_plan = []
        st.rerun()
    
    # 카테고리별로 그룹화하여 표시
    current_category = None
    
    for idx, item in enumerate(st.session_state.current_plan):
        # 카테고리 헤더
        if item['_category'] != current_category:
            current_category = item['_category']
            st.markdown(f"### {current_category}")
        
        # 항목 편집
        with st.expander(f"{item['No']}. {item['Test Title']}", expanded=False):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                item['Group'] = st.selectbox(
                    "Group",
                    options=['Individual', 'Sequence'],
                    index=0 if item['Group'] == 'Individual' else 1,
                    key=f"group_{idx}"
                )
                item['Specification'] = st.text_input(
                    "Specification",
                    value=item['Specification'],
                    key=f"spec_{idx}"
                )
                item['§'] = st.text_input(
                    "§",
                    value=item['§'],
                    key=f"section_{idx}"
                )
            
            with col2:
                item['Test Title'] = st.text_input(
                    "Test Title",
                    value=item['Test Title'],
                    key=f"title_{idx}"
                )
                item['Component'] = st.text_input(
                    "Component",
                    value=item['Component'],
                    key=f"component_{idx}"
                )
                item['Test by'] = st.text_input(
                    "Test by",
                    value=item['Test by'],
                    key=f"testby_{idx}"
                )
            
            with col3:
                item['Sample quantity'] = st.text_input(
                    "Sample quantity",
                    value=item['Sample quantity'],
                    key=f"quantity_{idx}"
                )
                item['Test Timing'] = st.text_input(
                    "Test Timing",
                    value=item['Test Timing'],
                    key=f"timing_{idx}"
                )
            
            # 삭제 버튼
            if item['_is_functional']:
                if st.button(f"🗑️ 삭제 (Functional Test)", key=f"del_{idx}"):
                    if st.checkbox(f"정말 삭제하시겠습니까? (중요 항목)", key=f"confirm_{idx}"):
                        st.session_state.current_plan.pop(idx)
                        st.rerun()
            else:
                if st.button(f"🗑️ 삭제", key=f"del_{idx}"):
                    st.session_state.current_plan.pop(idx)
                    st.rerun()
    
    # 항목 추가
    st.divider()
    with st.expander("➕ 새 시험 항목 추가"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            new_group = st.selectbox("Group", options=['Individual', 'Sequence'], key='new_group')
            new_spec = st.text_input("Specification", key='new_spec')
            new_section = st.text_input("§", key='new_section')
        
        with col2:
            new_title = st.text_input("Test Title", key='new_title')
            new_component = st.text_input("Component", key='new_component')
            new_testby = st.text_input("Test by", key='new_testby')
        
        with col3:
            new_quantity = st.text_input("Sample quantity", key='new_quantity')
            new_timing = st.text_input("Test Timing", key='new_timing')
        
        if st.button("추가"):
            if new_title:
                new_item = {
                    'No': len(st.session_state.current_plan) + 1,
                    'Group': new_group,
                    'Specification': new_spec,
                    '§': new_section,
                    'Test Title': new_title,
                    'Component': new_component,
                    'Test by': new_testby,
                    'Sample quantity': new_quantity,
                    'Test Timing': new_timing,
                    'Start': '',
                    'End': '',
                    'OK/NOK': '',
                    'Result': '',
                    'Remark': '',
                    'Customer Feedback': '',
                    '_category': 'Other',
                    '_is_functional': False,
                    '_original_item': {}
                }
                st.session_state.current_plan.append(new_item)
                st.success("✅ 항목이 추가되었습니다!")
                st.rerun()
            else:
                st.error("Test Title을 입력해주세요.")
    
    # 버튼
    st.divider()
    col_btn1, col_btn2 = st.columns(2)
    
    with col_btn1:
        if st.button("💾 계획서 초안 저장 (Excel)", type="primary", use_container_width=True):
            # 사용자 이름 가져오기
            users = st.session_state.db_manager.get_all_users()
            user = users[users['id'] == st.session_state.selected_user_id]
            user_name = user.iloc[0]['user_name'] if len(user) > 0 else 'User'
            
            # 엑셀 파일 생성
            filename = st.session_state.plan_generator.export_to_excel(
                st.session_state.current_plan,
                user_name
            )
            
            # 다운로드 버튼
            with open(filename, 'rb') as f:
                st.download_button(
                    label="📥 Excel 파일 다운로드",
                    data=f,
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            
            st.success("✅ 계획서가 저장되었습니다!")
    
    with col_btn2:
        if st.button("📅 일정 생성", use_container_width=True):
            st.session_state.current_page = 'scheduling'
            st.rerun()

def page_scheduling():
    """일정 스케줄링 화면"""
    st.title("📅 시험 일정 스케줄링")
    
    if not st.session_state.current_plan:
        st.warning("계획서 데이터가 없습니다.")
        return
    
    # 계획서에서 시험 항목 추출
    test_items_for_schedule = []
    for item in st.session_state.current_plan:
        original_item = item.get('_original_item', {})
        if not original_item:
            original_item = {
                'test_name': item['Test Title'],
                'category': item.get('_category', 'Other'),
                'test_duration': '1',
                'sample_count': item.get('Sample quantity', '3')
            }
        test_items_for_schedule.append(original_item)
    
    # 일정 생성 (D-day)
    if not st.session_state.current_schedule:
        with st.spinner("일정을 생성하는 중..."):
            schedule = st.session_state.scheduler.create_schedule(test_items_for_schedule)
            st.session_state.current_schedule = schedule
    
    st.subheader("타임라인 (D-day)")
    
    # Gantt 차트 표시
    schedule_data = []
    for item in st.session_state.current_schedule:
        schedule_data.append({
            'test_name': item['test_item'].get('test_name', 'Unknown'),
            'category': item['test_item'].get('category', 'Other'),
            'start_day': item['start_day'],
            'end_day': item['end_day'],
            'duration': item['duration']
        })
    
    fig = create_gantt_chart(
        schedule_data,
        color_by='category',
        title='시험 일정 (D-day 기준)'
    )
    
    if fig:
        st.plotly_chart(fig, use_container_width=True)
    
    # 일정 테이블
    st.dataframe(
        pd.DataFrame(schedule_data),
        use_container_width=True
    )
    
    # 시작일 설정 및 저장
    st.divider()
    st.subheader("일정 저장")
    
    # 기본 시작일 설정
    last_end_date = st.session_state.db_manager.get_last_end_date(st.session_state.selected_user_id)
    if last_end_date:
        default_start = last_end_date + timedelta(days=1)
    else:
        default_start = datetime.now()
    
    start_date = st.date_input(
        "시험 시작일",
        value=default_start,
        key='start_date_input'
    )
    
    if st.button("💾 일정 저장", type="primary", use_container_width=True):
        # 날짜로 변환
        dated_schedule = st.session_state.scheduler.convert_to_dates(
            st.session_state.current_schedule,
            start_date.strftime('%Y-%m-%d')
        )
        
        # 시험 항목 ID 가져오기
        test_item_ids = st.session_state.db_manager.get_test_items_by_request(
            st.session_state.selected_request_id
        )
        test_item_ids = [item['id'] for item in test_item_ids]
        
        # 일정 저장
        st.session_state.scheduler.save_schedule(dated_schedule, test_item_ids)
        
        st.success("✅ 일정이 저장되었습니다!")
        st.session_state.current_page = 'schedule_view'
        st.rerun()

def page_schedule_view():
    """전체 일정 보기 화면"""
    st.title("📆 전체 시험 일정 보기")
    
    if not st.session_state.selected_user_id:
        st.warning("사용자를 먼저 선택해주세요.")
        return
    
    # 월 선택
    col1, col2 = st.columns([3, 1])
    
    with col1:
        current_month = datetime.now().strftime('%Y-%m')
        selected_month = st.text_input("조회할 월 (YYYY-MM)", value=current_month, key='month_input')
    
    with col2:
        view_mode = st.selectbox("보기 모드", options=['Gantt Chart', 'Calendar'], key='view_mode')
    
    # 일정 데이터 가져오기
    schedule_df = st.session_state.db_manager.get_schedule_by_user(
        st.session_state.selected_user_id,
        selected_month
    )
    
    if len(schedule_df) == 0:
        st.info("해당 월에 등록된 일정이 없습니다.")
        return
    
    # 시험 항목 정보 결합
    test_items_df = pd.read_csv(TEST_ITEM_FILE, encoding='utf-8-sig')
    schedule_with_info = schedule_df.merge(
        test_items_df[['id', 'test_name', 'request_id', 'category']],
        left_on='test_item_id',
        right_on='id',
        how='left'
    )
    
    # 의뢰 정보 결합
    requests_df = pd.read_csv(REQUEST_INFO_FILE, encoding='utf-8-sig')
    schedule_with_info = schedule_with_info.merge(
        requests_df[['id', 'client', 'project']],
        left_on='request_id',
        right_on='id',
        how='left',
        suffixes=('', '_req')
    )
    
    if view_mode == 'Gantt Chart':
        st.subheader(f"{selected_month} 시험 일정")
        
        # Gantt 차트
        fig = create_gantt_chart(
            schedule_with_info.to_dict('records'),
            color_by='request',
            title=f'{selected_month} 전체 시험 일정'
        )
        
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        
        # 일정 테이블
        st.dataframe(
            schedule_with_info[[
                'test_name', 'category', 'client', 'project',
                'start_date', 'end_date', 'duration', 'status'
            ]],
            use_container_width=True
        )
    
    else:  # Calendar View
        st.subheader(f"{selected_month} 캘린더 뷰")
        
        calendar_data = create_calendar_view(
            schedule_with_info.to_dict('records'),
            selected_month
        )
        
        if calendar_data is not None and len(calendar_data) > 0:
            # 주별로 나누어 표시
            calendar_data['week'] = (calendar_data['day'] - 1) // 7
            
            for week in calendar_data['week'].unique():
                week_data = calendar_data[calendar_data['week'] == week]
                
                cols = st.columns(7)
                for idx, (_, day_data) in enumerate(week_data.iterrows()):
                    if idx < 7:
                        with cols[idx]:
                            st.markdown(f"**{day_data['weekday'][:3]}**")
                            st.markdown(f"### {day_data['day']}")
                            
                            if day_data['test_count'] > 0:
                                st.info(f"📋 {day_data['test_count']}개 시험")
                                with st.expander("상세"):
                                    st.text(day_data['tests'])
                            else:
                                st.text("일정 없음")

# 페이지 라우팅
page_functions = {
    'user_selection': page_user_selection,
    'test_spec_edit': page_test_spec_edit,
    'plan_creation': page_plan_creation,
    'scheduling': page_scheduling,
    'schedule_view': page_schedule_view
}

# 현재 페이지 렌더링
if st.session_state.current_page in page_functions:
    page_functions[st.session_state.current_page]()
else:
    st.error("페이지를 찾을 수 없습니다.")

