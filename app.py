import streamlit as st
import pandas as pd
from datetime import datetime
import json
import os
from utils.database import DatabaseManager
from utils.llm_handler import LLMHandler
from utils.scheduler import SchedulerManager

# 페이지 설정
st.set_page_config(
    page_title="RPM - Reliable Planning Manager",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 세션 상태 초기화
if 'current_user' not in st.session_state:
    st.session_state.current_user = None
if 'current_request' not in st.session_state:
    st.session_state.current_request = None
if 'page' not in st.session_state:
    st.session_state.page = 'user_selection'
if 'extracted_data' not in st.session_state:
    st.session_state.extracted_data = None
if 'db_manager' not in st.session_state:
    st.session_state.db_manager = DatabaseManager()

db_manager = st.session_state.db_manager

# 사이드바
def render_sidebar():
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
        
        st.markdown("---")
        
        # Database Export 기능
        st.subheader("💾 Database Export")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Master Test", use_container_width=True):
                export_csv('Master_Test')
            if st.button("Test Item", use_container_width=True):
                export_csv('Test_Item')
        
        with col2:
            if st.button("Request Info", use_container_width=True):
                export_csv('Request_Info')
            if st.button("User List", use_container_width=True):
                export_csv('User_List')
        
        st.markdown("---")
        
        # 페이지 네비게이션
        st.subheader("📑 페이지 이동")
        if st.button("🏠 사용자 선택", use_container_width=True):
            st.session_state.page = 'user_selection'
            st.rerun()

def export_csv(data_type):
    """CSV 파일 다운로드"""
    if data_type == 'Master_Test':
        df = db_manager.load_master_data()
        filename = 'Master_Test.csv'
    elif data_type == 'Request_Info':
        df = db_manager.load_request_data()
        filename = 'Request_Info.csv'
    elif data_type == 'Test_Item':
        df = db_manager.load_test_item_data()
        filename = 'Test_Item.csv'
    elif data_type == 'User_List':
        df = db_manager.load_user_data()
        filename = 'User_List.csv'
    
    csv = df.to_csv(index=False, encoding='utf-8-sig')
    st.download_button(
        label=f"Download {filename}",
        data=csv,
        file_name=filename,
        mime='text/csv',
        key=f'download_{data_type}'
    )

# 페이지 1: 사용자 선택 화면
def page_user_selection():
    st.title("👤 사용자 선택 및 의뢰 관리")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("사용자 선택")
        
        # 사용자 목록 로드
        users_df = db_manager.load_user_data()
        user_names = users_df['user_name'].tolist()
        
        # 사용자 선택 드롭다운
        selected_user = st.selectbox(
            "사용자를 선택하세요",
            options=user_names,
            index=0 if user_names else None
        )
        
        if selected_user:
            user_info = users_df[users_df['user_name'] == selected_user].iloc[0]
            st.session_state.current_user = user_info.to_dict()
            
            # 마지막 접속 시간 업데이트
            db_manager.update_user_last_access(user_info['id'])
            
            st.success(f"✅ {selected_user} 선택됨")
        
        # 사용자 추가
        st.markdown("---")
        with st.expander("➕ 새 사용자 추가"):
            new_user_name = st.text_input("사용자 이름")
            if st.button("사용자 추가", use_container_width=True):
                if new_user_name:
                    user_id = db_manager.add_user(new_user_name)
                    st.success(f"사용자 '{new_user_name}' 추가됨 (ID: {user_id})")
                    st.rerun()
                else:
                    st.error("사용자 이름을 입력하세요")
        
        # 의뢰 선택
        st.markdown("---")
        st.subheader("기존 의뢰 선택")
        
        if st.session_state.current_user:
            user_requests = db_manager.get_user_requests(st.session_state.current_user['id'])
            
            if not user_requests.empty:
                request_options = [f"{row['id']} - {row['project']}" for _, row in user_requests.iterrows()]
                selected_request = st.selectbox("의뢰 선택", options=request_options)
                
                if selected_request:
                    request_id = selected_request.split(' - ')[0]
                    st.session_state.current_request = request_id
                    
                    if st.button("📝 의뢰 수정", use_container_width=True):
                        # 기존 의뢰 데이터 로드
                        request_data = db_manager.get_request_by_id(request_id)
                        st.session_state.extracted_data = json.loads(request_data['final_data'])
                        st.session_state.page = 'edit_extraction'
                        st.rerun()
            else:
                st.info("저장된 의뢰가 없습니다")
        
        # 새 의뢰 버튼
        st.markdown("---")
        uploaded_file = st.file_uploader(
            "📄 시험 규격 파일 업로드",
            type=['pdf', 'docx'],
            help="PDF 또는 DOCX 형식의 시험 규격 문서를 업로드하세요"
        )
        
        if st.button("🆕 새 의뢰 생성", use_container_width=True, type="primary"):
            if uploaded_file and st.session_state.current_user:
                with st.spinner("문서를 분석하고 있습니다..."):
                    llm_handler = LLMHandler(db_manager)
                    extracted_data = llm_handler.extract_test_data(uploaded_file)
                    
                    if extracted_data:
                        st.session_state.extracted_data = extracted_data
                        st.session_state.page = 'edit_extraction'
                        st.success("✅ 데이터 추출 완료!")
                        st.rerun()
                    else:
                        st.error("데이터 추출에 실패했습니다")
            elif not st.session_state.current_user:
                st.error("먼저 사용자를 선택하세요")
            else:
                st.error("파일을 업로드하세요")
    
    with col2:
        st.subheader("📅 일정 확인")
        
        if st.session_state.current_user:
            # 사용자의 전체 일정 표시
            scheduler = SchedulerManager(db_manager)
            gantt_fig = scheduler.create_user_gantt_chart(st.session_state.current_user['id'])
            
            if gantt_fig:
                st.plotly_chart(gantt_fig, use_container_width=True)
            else:
                st.info("등록된 시험 일정이 없습니다")
            
            # 선택된 의뢰의 일정 표시
            if st.session_state.current_request:
                st.markdown("---")
                st.subheader(f"의뢰 {st.session_state.current_request} 일정")
                
                request_gantt = scheduler.create_request_gantt_chart(st.session_state.current_request)
                if request_gantt:
                    st.plotly_chart(request_gantt, use_container_width=True)
        else:
            st.info("사용자를 선택하면 일정이 표시됩니다")

# 페이지 2: 추출 시험 규격 편집 화면
def page_edit_extraction():
    st.title("📝 추출 시험 규격 편집")
    
    if not st.session_state.extracted_data:
        st.warning("추출된 데이터가 없습니다. 사용자 선택 화면으로 돌아가세요.")
        if st.button("🏠 사용자 선택으로 돌아가기"):
            st.session_state.page = 'user_selection'
            st.rerun()
        return
    
    data = st.session_state.extracted_data
    
    # 의뢰 정보 표시
    st.subheader("📋 의뢰 정보")
    col1, col2 = st.columns(2)
    with col1:
        client = st.text_input("발주처", value=data.get('request_info', {}).get('client', ''))
    with col2:
        project = st.text_input("프로젝트명", value=data.get('request_info', {}).get('project', ''))
    
    data['request_info'] = {'client': client, 'project': project}
    
    st.markdown("---")
    st.subheader("🔬 시험 항목 데이터")
    
    # 시험 항목 편집
    test_items = data.get('test_items', [])
    
    for idx, item in enumerate(test_items):
        # 표준화 적용
        standardized_item = db_manager.standardize_test_item(item)
        test_items[idx] = standardized_item
        
        # 매칭 상태 표시
        is_matched = bool(standardized_item.get('test_master_id'))
        icon = "✅" if is_matched else "⚠️"
        match_status = f"[마스터: {standardized_item.get('test_master_id')}]" if is_matched else "[미매칭]"
        
        with st.expander(f"{icon} {standardized_item.get('test_name', '시험 항목')} {match_status}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**원본 데이터**")
                st.text_input("원본 시험명", value=standardized_item.get('test_name_original', ''), 
                            key=f"orig_name_{idx}", disabled=True)
                st.text_input("원본 분류", value=standardized_item.get('category_original', ''), 
                            key=f"orig_cat_{idx}", disabled=True)
            
            with col2:
                st.markdown("**표준화된 데이터**")
                test_items[idx]['test_name'] = st.text_input(
                    "표준 시험명", 
                    value=standardized_item.get('test_name', ''),
                    key=f"test_name_{idx}"
                )
                test_items[idx]['category'] = st.text_input(
                    "표준 분류", 
                    value=standardized_item.get('category', ''),
                    key=f"category_{idx}"
                )
            
            # 마스터 정보 표시
            if is_matched:
                master_data = db_manager.get_master_by_id(standardized_item.get('test_master_id'))
                if master_data:
                    st.info(f"**마스터 정보:** {json.dumps(master_data, ensure_ascii=False, indent=2)}")
            
            st.text_input("마스터 ID (읽기 전용)", 
                         value=standardized_item.get('test_master_id', ''), 
                         key=f"master_id_{idx}", 
                         disabled=True)
            
            # 기타 필드
            col3, col4, col5 = st.columns(3)
            with col3:
                test_items[idx]['ref_standard'] = st.text_input(
                    "참조 규격", 
                    value=standardized_item.get('ref_standard', ''),
                    key=f"ref_{idx}"
                )
            with col4:
                test_items[idx]['sample_assembly'] = st.text_input(
                    "시료 구성", 
                    value=standardized_item.get('sample_assembly', ''),
                    key=f"assembly_{idx}"
                )
            with col5:
                test_items[idx]['sample_count'] = st.text_input(
                    "시료 수", 
                    value=standardized_item.get('sample_count', ''),
                    key=f"count_{idx}"
                )
            
            col6, col7, col8 = st.columns(3)
            with col6:
                test_items[idx]['test_sample_no'] = st.text_input(
                    "샘플 번호", 
                    value=standardized_item.get('test_sample_no', ''),
                    key=f"sample_no_{idx}"
                )
            with col7:
                test_items[idx]['test_duration'] = st.text_input(
                    "시험 기간(일)", 
                    value=standardized_item.get('test_duration', ''),
                    key=f"duration_{idx}"
                )
            with col8:
                test_items[idx]['test_equipment'] = st.text_input(
                    "시험 장비", 
                    value=standardized_item.get('test_equipment', ''),
                    key=f"equipment_{idx}"
                )
            
            # Custom Specs
            st.markdown("**특수 요구사항 (Custom Specs)**")
            custom_specs = standardized_item.get('custom_specs', {})
            custom_specs_json = st.text_area(
                "JSON 형식으로 입력",
                value=json.dumps(custom_specs, ensure_ascii=False, indent=2),
                key=f"custom_{idx}",
                height=150
            )
            try:
                test_items[idx]['custom_specs'] = json.loads(custom_specs_json)
            except:
                st.error("올바른 JSON 형식이 아닙니다")
    
    # 업데이트된 데이터 저장
    data['test_items'] = test_items
    st.session_state.extracted_data = data
    
    # 버튼
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📄 계획서 생성", use_container_width=True, type="primary"):
            # 데이터 저장
            request_id = save_request_data(data)
            st.session_state.current_request = request_id
            
            # 마스터 데이터 업데이트
            db_manager.update_master_from_extraction(data['test_items'])
            
            st.success("✅ 데이터가 저장되었습니다")
            st.session_state.page = 'create_plan'
            st.rerun()
    
    with col2:
        if st.button("💾 의뢰 데이터 저장", use_container_width=True):
            request_id = save_request_data(data)
            st.session_state.current_request = request_id
            
            # 마스터 데이터 업데이트
            db_manager.update_master_from_extraction(data['test_items'])
            
            st.success(f"✅ 데이터가 저장되었습니다 (의뢰 ID: {request_id})")

def save_request_data(data):
    """의뢰 데이터 저장"""
    if st.session_state.current_request:
        # 기존 의뢰 업데이트
        request_id = st.session_state.current_request
        db_manager.update_request(request_id, data)
    else:
        # 새 의뢰 생성
        request_id = db_manager.create_request(
            user_id=st.session_state.current_user['id'],
            extracted_data=data,
            client=data['request_info'].get('client', ''),
            project=data['request_info'].get('project', '')
        )
    
    return request_id

# 페이지 3: 계획서 초안 작성 화면
def page_create_plan():
    st.title("📊 계획서 초안 작성")
    
    if not st.session_state.extracted_data:
        st.warning("추출된 데이터가 없습니다")
        return
    
    data = st.session_state.extracted_data
    test_items = data.get('test_items', [])
    
    st.subheader("📋 시험 계획서")
    
    # 계획서 테이블 생성
    plan_data = []
    for idx, item in enumerate(test_items):
        plan_data.append({
            '포함': True,
            '순번': idx + 1,
            '시험명': item.get('test_name', ''),
            '분류': item.get('category', ''),
            '참조 규격': item.get('ref_standard', ''),
            '시료 구성': item.get('sample_assembly', ''),
            '시료 수': item.get('sample_count', ''),
            '시험 기간(일)': item.get('test_duration', ''),
            '시험 장비': item.get('test_equipment', ''),
        })
    
    plan_df = pd.DataFrame(plan_data)
    
    # 편집 가능한 데이터프레임
    edited_df = st.data_editor(
        plan_df,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "포함": st.column_config.CheckboxColumn(
                "포함",
                help="계획서에 포함할 항목 선택",
                default=True,
            )
        },
        hide_index=True,
    )
    
    st.session_state.plan_data = edited_df
    
    # 버튼
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("💾 계획서 저장 (Excel)", use_container_width=True):
            # Excel 파일로 저장
            output_df = edited_df[edited_df['포함'] == True].drop(columns=['포함'])
            
            # 파일명 생성
            project_name = data['request_info'].get('project', 'project')
            filename = f"계획서_{project_name}_{datetime.now().strftime('%Y%m%d')}.xlsx"
            
            # Excel 저장
            output_df.to_excel(filename, index=False, engine='openpyxl')
            
            with open(filename, 'rb') as f:
                st.download_button(
                    label="📥 Excel 파일 다운로드",
                    data=f,
                    file_name=filename,
                    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
            
            st.success("✅ 계획서가 저장되었습니다")
    
    with col2:
        if st.button("📅 일정 생성", use_container_width=True, type="primary"):
            st.session_state.page = 'schedule'
            st.rerun()

# 페이지 4: 시험 일정 관리 화면
def page_schedule():
    st.title("📅 시험 일정 관리")
    
    if 'plan_data' not in st.session_state:
        st.warning("계획서 데이터가 없습니다")
        return
    
    plan_df = st.session_state.plan_data
    included_items = plan_df[plan_df['포함'] == True]
    
    st.subheader("📊 타임라인 (D-Day)")
    
    # Gantt 차트 생성
    scheduler = SchedulerManager(db_manager)
    gantt_fig = scheduler.create_timeline_chart(included_items, st.session_state.current_request)
    
    if gantt_fig:
        st.plotly_chart(gantt_fig, use_container_width=True)
    
    # 일정 저장
    st.markdown("---")
    if st.button("💾 타임라인 저장", use_container_width=True, type="primary"):
        # 일정 데이터를 데이터베이스에 저장
        scheduler.save_schedule(
            user_id=st.session_state.current_user['id'],
            request_id=st.session_state.current_request,
            schedule_data=included_items
        )
        
        st.success("✅ 일정이 저장되었습니다")
        
        if st.button("🏠 사용자 선택으로 돌아가기"):
            st.session_state.page = 'user_selection'
            st.rerun()

# 메인 라우팅
def main():
    render_sidebar()
    
    if st.session_state.page == 'user_selection':
        page_user_selection()
    elif st.session_state.page == 'edit_extraction':
        page_edit_extraction()
    elif st.session_state.page == 'create_plan':
        page_create_plan()
    elif st.session_state.page == 'schedule':
        page_schedule()

if __name__ == "__main__":
    main()
