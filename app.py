import streamlit as st
import pandas as pd
from datetime import datetime
import os
from modules.data_manager import DataManager
from modules.document_parser import DocumentParser
from modules.llm_processor import LLMProcessor
from modules.scheduler import Scheduler
from utils.helpers import initialize_session_state, save_dataframe_to_csv

# 페이지 설정
st.set_page_config(
    page_title="RPM - Reliable Planning Manager",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 세션 상태 초기화
initialize_session_state()

# 데이터 매니저 초기화
data_manager = DataManager()

def render_sidebar():
    """사이드바 렌더링"""
    with st.sidebar:
        st.title("⚙️ RPM")
        st.markdown("### Reliable Planning Manager")
        st.divider()
        
        # 현재 세션 정보
        st.markdown("### 📋 세션 정보")
        if st.session_state.current_user:
            st.info(f"**사용자:** {st.session_state.current_user['user_name']}")
        if st.session_state.current_request_id:
            st.info(f"**의뢰 ID:** {st.session_state.current_request_id}")
        
        st.divider()
        
        # Database Export 기능
        st.markdown("### 💾 Database Export")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Master Test", use_container_width=True):
                df = data_manager.load_master_test_data()
                csv = df.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    "📥 Download",
                    csv,
                    "Master_Test.csv",
                    "text/csv",
                    key='download_master'
                )
        
        with col2:
            if st.button("Request Info", use_container_width=True):
                df = data_manager.load_request_info_data()
                csv = df.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    "📥 Download",
                    csv,
                    "Request_Info.csv",
                    "text/csv",
                    key='download_request'
                )
        
        col3, col4 = st.columns(2)
        with col3:
            if st.button("Test Item", use_container_width=True):
                df = data_manager.load_test_item_data()
                csv = df.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    "📥 Download",
                    csv,
                    "Test_Item.csv",
                    "text/csv",
                    key='download_test'
                )
        
        with col4:
            if st.button("User List", use_container_width=True):
                df = data_manager.load_user_list_data()
                csv = df.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    "📥 Download",
                    csv,
                    "User_List.csv",
                    "text/csv",
                    key='download_user'
                )

def user_selection_screen():
    """3.1. 사용자 선택 화면"""
    st.title("👤 사용자 선택")
    
    col1, col2 = st.columns([2, 3])
    
    with col1:
        st.markdown("### 사용자 관리")
        
        # 사용자 목록 로드
        users_df = data_manager.load_user_list_data()
        user_names = users_df['user_name'].tolist() if not users_df.empty else []
        
        # 사용자 선택
        selected_user_name = st.selectbox(
            "사용자 선택",
            options=user_names,
            index=0 if user_names else None
        )
        
        # 사용자 추가
        with st.expander("➕ 새 사용자 추가"):
            new_user_name = st.text_input("사용자 이름")
            if st.button("추가", use_container_width=True):
                if new_user_name and new_user_name.strip():
                    success = data_manager.add_user(new_user_name.strip())
                    if success:
                        st.success(f"'{new_user_name}' 사용자가 추가되었습니다.")
                        st.rerun()
                    else:
                        st.error("사용자 추가에 실패했습니다.")
                else:
                    st.warning("사용자 이름을 입력하세요.")
        
        # 사용자 선택 확인
        if selected_user_name:
            user_row = users_df[users_df['user_name'] == selected_user_name].iloc[0]
            st.session_state.current_user = user_row.to_dict()
            
            # 마지막 접속 시간 업데이트
            data_manager.update_last_access(user_row['id'])
            
            if st.button("✅ 사용자 확인", use_container_width=True, type="primary"):
                st.success(f"'{selected_user_name}' 사용자로 로그인되었습니다.")
        
        st.divider()
        
        # 의뢰 선택 메뉴
        if st.session_state.current_user:
            st.markdown("### 의뢰 선택")
            
            # 현재 사용자의 의뢰 목록
            requests_df = data_manager.load_request_info_data()
            user_requests = requests_df[
                requests_df['user_id'] == st.session_state.current_user['id']
            ]
            
            if not user_requests.empty:
                request_options = [
                    f"{row['id']} - {row['client']} ({row['project']})"
                    for _, row in user_requests.iterrows()
                ]
                
                selected_request = st.selectbox(
                    "의뢰 선택",
                    options=request_options
                )
                
                if selected_request:
                    request_id = selected_request.split(' - ')[0]
                    st.session_state.selected_request_id = request_id
                    
                    if st.button("📝 의뢰 수정", use_container_width=True):
                        st.session_state.current_request_id = request_id
                        st.session_state.page = "test_data"
                        st.rerun()
            else:
                st.info("저장된 의뢰가 없습니다.")
        
        st.divider()
        
        # 새 의뢰 버튼
        st.markdown("### 새 의뢰")
        uploaded_file = st.file_uploader(
            "시험 규격 파일 업로드",
            type=['pdf', 'docx'],
            help="PDF 또는 DOCX 형식의 파일을 업로드하세요."
        )
        
        if uploaded_file and st.button("🆕 새 의뢰 생성", use_container_width=True, type="primary"):
            with st.spinner("문서를 분석하고 있습니다..."):
                # 문서 파싱 및 데이터 추출
                parser = DocumentParser()
                llm_processor = LLMProcessor(data_manager)
                
                # 파일 처리
                file_content = uploaded_file.read()
                file_type = uploaded_file.type
                
                # LLM으로 데이터 추출
                extracted_data = llm_processor.extract_test_data(file_content, file_type)
                
                if extracted_data:
                    st.session_state.extracted_data = extracted_data
                    st.session_state.page = "test_data"
                    st.success("문서 분석이 완료되었습니다!")
                    st.rerun()
                else:
                    st.error("문서 분석에 실패했습니다.")
    
    with col2:
        st.markdown("### 📅 일정 확인")
        
        if st.session_state.current_user:
            # 사용자의 전체 시험 일정 Gantt Chart
            scheduler = Scheduler(data_manager)
            
            if st.session_state.selected_request_id:
                # 특정 의뢰의 일정
                fig = scheduler.create_gantt_chart(
                    st.session_state.current_user['id'],
                    st.session_state.selected_request_id
                )
            else:
                # 전체 일정
                fig = scheduler.create_gantt_chart(
                    st.session_state.current_user['id']
                )
            
            if fig:
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("표시할 일정이 없습니다.")
        else:
            st.info("사용자를 먼저 선택하세요.")

def test_data_screen():
    """3.2. 시험 의뢰 항목 데이터 화면"""
    st.title("📊 시험 의뢰 항목 데이터")
    
    # 데이터 로드
    if st.session_state.current_request_id:
        # 기존 의뢰 수정
        requests_df = data_manager.load_request_info_data()
        request_row = requests_df[
            requests_df['id'] == st.session_state.current_request_id
        ].iloc[0]
        
        test_items_df = data_manager.load_test_item_data()
        test_items = test_items_df[
            test_items_df['request_id'] == st.session_state.current_request_id
        ]
        
        st.info(f"**의뢰 ID:** {request_row['id']} | **발주처:** {request_row['client']} | **프로젝트:** {request_row['project']}")
    else:
        # 새 의뢰
        if 'extracted_data' not in st.session_state or not st.session_state.extracted_data:
            st.warning("추출된 데이터가 없습니다.")
            if st.button("← 돌아가기"):
                st.session_state.page = "user_selection"
                st.rerun()
            return
        
        test_items = pd.DataFrame(st.session_state.extracted_data.get('test_items', []))
        request_info = st.session_state.extracted_data.get('request_info', {})
        
        st.info(f"**발주처:** {request_info.get('client', 'N/A')} | **프로젝트:** {request_info.get('project', 'N/A')}")
    
    # 의뢰 추출 데이터 박스
    st.markdown("### 📋 추출된 시험 항목")
    
    if not test_items.empty:
        # Expandable tree view 구현
        for idx, row in test_items.iterrows():
            with st.expander(f"**{row.get('test_name', 'N/A')}** - {row.get('category', 'N/A')}"):
                # 편집 가능한 폼
                col1, col2 = st.columns(2)
                
                with col1:
                    test_name = st.text_input("시험명", value=row.get('test_name', ''), key=f"name_{idx}")
                    category = st.text_input("분류", value=row.get('category', ''), key=f"cat_{idx}")
                    ref_standard = st.text_input("참조 규격", value=row.get('ref_standard', ''), key=f"ref_{idx}")
                    sample_assembly = st.text_input("시료 구성", value=row.get('sample_assembly', ''), key=f"assembly_{idx}")
                    test_sample_no = st.text_input("샘플 번호", value=row.get('test_sample_no', ''), key=f"sample_no_{idx}")
                
                with col2:
                    sample_count = st.text_input("시료 수", value=row.get('sample_count', ''), key=f"count_{idx}")
                    test_duration = st.text_input("소요 일수", value=row.get('test_duration', ''), key=f"duration_{idx}")
                    test_equipment = st.text_input("시험 장비", value=row.get('test_equipment', ''), key=f"equipment_{idx}")
                    test_master_id = st.text_input("마스터 ID", value=row.get('test_master_id', ''), key=f"master_{idx}")
                
                # Custom specs
                st.markdown("**특수 요구사항**")
                custom_specs = row.get('custom_specs', {})
                if isinstance(custom_specs, str):
                    import json
                    try:
                        custom_specs = json.loads(custom_specs)
                    except:
                        custom_specs = {}
                
                custom_specs_text = st.text_area(
                    "Custom Specs (JSON)",
                    value=str(custom_specs),
                    key=f"custom_{idx}",
                    height=100
                )
                
                # 업데이트된 데이터 저장
                test_items.at[idx, 'test_name'] = test_name
                test_items.at[idx, 'category'] = category
                test_items.at[idx, 'ref_standard'] = ref_standard
                test_items.at[idx, 'sample_assembly'] = sample_assembly
                test_items.at[idx, 'test_sample_no'] = test_sample_no
                test_items.at[idx, 'sample_count'] = sample_count
                test_items.at[idx, 'test_duration'] = test_duration
                test_items.at[idx, 'test_equipment'] = test_equipment
                test_items.at[idx, 'test_master_id'] = test_master_id
                test_items.at[idx, 'custom_specs'] = custom_specs_text
        
        # 세션에 저장
        st.session_state.edited_test_items = test_items
    else:
        st.warning("시험 항목이 없습니다.")
    
    st.divider()
    
    # 버튼
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("← 돌아가기", use_container_width=True):
            st.session_state.page = "user_selection"
            st.rerun()
    
    with col2:
        if st.button("💾 의뢰 데이터 저장", use_container_width=True):
            if st.session_state.current_user:
                # 데이터 저장
                success = data_manager.save_request_data(
                    st.session_state.current_user['id'],
                    st.session_state.extracted_data.get('request_info', {}),
                    st.session_state.edited_test_items.to_dict('records')
                )
                
                if success:
                    st.success("✅ 데이터가 저장되었습니다.")
                else:
                    st.error("❌ 데이터 저장에 실패했습니다.")
            else:
                st.error("사용자를 먼저 선택하세요.")
    
    with col3:
        if st.button("📄 계획서 생성 →", use_container_width=True, type="primary"):
            st.session_state.page = "plan_draft"
            st.rerun()

def plan_draft_screen():
    """3.3. 계획서 초안 작성 화면"""
    st.title("📄 계획서 초안")
    
    if 'edited_test_items' not in st.session_state:
        st.warning("시험 항목 데이터가 없습니다.")
        if st.button("← 돌아가기"):
            st.session_state.page = "test_data"
            st.rerun()
        return
    
    st.markdown("### 📋 계획서 출력")
    
    # 계획서 데이터 준비
    test_items = st.session_state.edited_test_items.copy()
    
    # 체크박스 열 추가
    if 'include' not in test_items.columns:
        test_items['include'] = True
    
    # 편집 가능한 데이터프레임
    edited_df = st.data_editor(
        test_items,
        column_config={
            "include": st.column_config.CheckboxColumn(
                "포함",
                help="계획서에 포함할 항목을 선택하세요",
                default=True,
            ),
            "test_name": st.column_config.TextColumn("시험명", width="medium"),
            "category": st.column_config.TextColumn("분류", width="medium"),
            "sample_count": st.column_config.TextColumn("시료 수", width="small"),
            "test_duration": st.column_config.TextColumn("소요 일수", width="small"),
            "ref_standard": st.column_config.TextColumn("참조 규격", width="medium"),
        },
        hide_index=True,
        use_container_width=True,
        num_rows="dynamic"
    )
    
    st.session_state.plan_data = edited_df
    
    st.divider()
    
    # 버튼
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("← 돌아가기", use_container_width=True):
            st.session_state.page = "test_data"
            st.rerun()
    
    with col2:
        if st.button("💾 계획서 저장 (Excel)", use_container_width=True):
            # Excel 파일로 저장
            output_file = f"test_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            edited_df[edited_df['include'] == True].to_excel(output_file, index=False, engine='openpyxl')
            
            with open(output_file, 'rb') as f:
                st.download_button(
                    "📥 Excel 다운로드",
                    f,
                    file_name=output_file,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            
            st.success("✅ 계획서가 생성되었습니다.")
    
    with col3:
        if st.button("📅 일정 생성 →", use_container_width=True, type="primary"):
            st.session_state.page = "schedule"
            st.rerun()

def schedule_screen():
    """3.4. 시험 일정 관리 화면"""
    st.title("📅 시험 일정 관리")
    
    if 'plan_data' not in st.session_state:
        st.warning("계획서 데이터가 없습니다.")
        if st.button("← 돌아가기"):
            st.session_state.page = "plan_draft"
            st.rerun()
        return
    
    st.markdown("### 📊 타임라인 (D-Day)")
    
    # 포함된 항목만 필터링
    included_items = st.session_state.plan_data[
        st.session_state.plan_data['include'] == True
    ]
    
    # 스케줄러로 Gantt Chart 생성
    scheduler = Scheduler(data_manager)
    fig = scheduler.create_timeline_chart(included_items)
    
    if fig:
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("일정을 생성할 수 없습니다.")
    
    st.divider()
    
    # 버튼
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("← 돌아가기", use_container_width=True):
            st.session_state.page = "plan_draft"
            st.rerun()
    
    with col2:
        if st.button("💾 타임라인 저장", use_container_width=True, type="primary"):
            if st.session_state.current_user:
                # 일정 DB에 저장
                success = scheduler.save_schedule(
                    st.session_state.current_user['id'],
                    st.session_state.current_request_id,
                    included_items
                )
                
                if success:
                    st.success("✅ 일정이 저장되었습니다.")
                else:
                    st.error("❌ 일정 저장에 실패했습니다.")
            else:
                st.error("사용자를 먼저 선택하세요.")
    
    with col3:
        if st.button("🏠 홈으로", use_container_width=True):
            st.session_state.page = "user_selection"
            st.session_state.current_request_id = None
            st.session_state.selected_request_id = None
            st.rerun()

# 메인 앱 실행
def main():
    render_sidebar()
    
    # 페이지 라우팅
    if st.session_state.page == "user_selection":
        user_selection_screen()
    elif st.session_state.page == "test_data":
        test_data_screen()
    elif st.session_state.page == "plan_draft":
        plan_draft_screen()
    elif st.session_state.page == "schedule":
        schedule_screen()

if __name__ == "__main__":
    main()
