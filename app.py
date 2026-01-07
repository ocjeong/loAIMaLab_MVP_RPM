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
        
        # 3.1.4. 새 의뢰 버튼 (수정됨)
        st.markdown("### 새 의뢰 생성")
        
        # 샘플 파일 목록 가져오기
        from utils.helpers import get_sample_pdf_files, load_sample_pdf
        sample_files = get_sample_pdf_files()
        
        # 샘플 파일 선택 메뉴 (2개 이상 있을 때만 표시)
        selected_sample = None
        if sample_files:
            st.markdown("#### 📁 샘플 파일 선택")
            
            sample_options = ["직접 업로드"] + [f['display_name'] for f in sample_files]
            selected_option = st.selectbox(
                "샘플 파일을 선택하거나 직접 업로드하세요",
                options=sample_options,
                help="sample 폴더의 PDF 파일을 선택하거나 직접 파일을 업로드할 수 있습니다."
            )
            
            if selected_option != "직접 업로드":
                # 선택된 샘플 파일 찾기
                for sample in sample_files:
                    if sample['display_name'] == selected_option:
                        selected_sample = sample
                        st.info(f"📄 선택된 샘플: {selected_sample['name']}")
                        break
        
        # 파일 업로드 또는 샘플 사용
        uploaded_file = None
        
        if selected_sample:
            # 샘플 파일 사용
            st.markdown("#### 샘플 파일로 의뢰 생성")
            if st.button("🚀 샘플로 의뢰 생성", use_container_width=True, type="primary"):
                with st.spinner("샘플 문서를 분석하고 있습니다..."):
                    # 샘플 파일 로드
                    sample_file = load_sample_pdf(selected_sample['path'])
                    
                    if sample_file:
                        # 파일 처리 및 LLM 추출
                        extracted_data = llm_handler.extract_from_document(sample_file)
                        
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
                            st.success("✅ 샘플 의뢰가 생성되었습니다!")
                            st.session_state.current_page = "test_spec_edit"
                            st.rerun()
                        else:
                            st.error("문서 추출에 실패했습니다.")
                    else:
                        st.error("샘플 파일을 로드할 수 없습니다.")
        else:
            # 직접 파일 업로드
            st.markdown("#### 파일 직접 업로드")
            uploaded_file = st.file_uploader(
                "시험 규격 파일 업로드",
                type=['pdf', 'docx'],
                help="PDF 또는 DOCX 형식의 파일만 업로드 가능합니다."
            )
            
            if uploaded_file:
                if st.button("🚀 새 의뢰 생성", use_container_width=True, type="primary"):
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
            
            with col2:
                item['test_sample_no'] = st.text_input(
                    "샘플 번호",
                    value=item.get('test_sample_no', ''),
                    key=f"test_sample_no_{idx}"
                )
                
                item['sample_count'] = st.text_input(
                    "시료 수",
                    value=item.get('sample_count', ''),
                    key=f"sample_count_{idx}"
                )
                
                item['test_duration'] = st.text_input(
                    "시험 기간 (일)",
                    value=item.get('test_duration', ''),
                    key=f"test_duration_{idx}"
                )
                
                item['test_equipment'] = st.text_input(
                    "시험 장비",
                    value=item.get('test_equipment', ''),
                    key=f"test_equipment_{idx}"
                )
            
            # test_master_id는 읽기 전용
            st.text_input(
                "마스터 ID (읽기 전용)",
                value=item.get('test_master_id', ''),
                key=f"test_master_id_{idx}",
                disabled=True
            )
            
            # custom_specs 편집
            st.markdown("#### Custom Specifications")
            custom_specs = item.get('custom_specs', {})
            
            if isinstance(custom_specs, dict):
                for key, value in custom_specs.items():
                    custom_specs[key] = st.text_input(
                        key,
                        value=value,
                        key=f"custom_{idx}_{key}"
                    )
                item['custom_specs'] = custom_specs
    
    st.divider()
    
    # 버튼들
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        # 3.2.2. 계획서 생성 버튼
        if st.button("📋 계획서 생성", use_container_width=True):
            # 데이터 저장
            db.update_request_final_data(
                st.session_state.current_request['id'],
                final_data
            )
            
            # 마스터 데이터 업데이트
            for item in final_data:
                if item.get('test_master_id') and item.get('test_name_original'):
                    db.update_master_aliases(
                        item['test_master_id'],
                        item['test_name_original']
                    )
                elif not item.get('test_master_id'):
                    # 새 마스터 추가
                    db.add_master_test(
                        std_name=item.get('test_name', ''),
                        std_category=item.get('category', ''),
                        ref_standard=item.get('ref_standard', ''),
                        aliases=[item.get('test_name_original', '')]
                    )
            
            st.success("✅ 데이터가 저장되었습니다!")
            st.session_state.current_page = "plan_draft"
            st.rerun()
    
    with col2:
        # 3.2.3. 의뢰 데이터 저장 버튼
        if st.button("💾 데이터 저장", use_container_width=True):
            db.update_request_final_data(
                st.session_state.current_request['id'],
                final_data
            )
            
            # 마스터 데이터 업데이트
            for item in final_data:
                if item.get('test_master_id') and item.get('test_name_original'):
                    db.update_master_aliases(
                        item['test_master_id'],
                        item['test_name_original']
                    )
                elif not item.get('test_master_id'):
                    # 새 마스터 추가
                    db.add_master_test(
                        std_name=item.get('test_name', ''),
                        std_category=item.get('category', ''),
                        ref_standard=item.get('ref_standard', ''),
                        aliases=[item.get('test_name_original', '')]
                    )
            
            st.success("✅ 데이터가 저장되었습니다!")


def page_plan_draft():
    """3.3. 계획서 초안 작성 화면"""
    st.title("📋 계획서 초안 작성")
    
    if not st.session_state.current_request:
        st.warning("의뢰를 선택해주세요.")
        return
    
    # 3.3.1. 시험 계획서 출력 박스
    st.markdown("### 시험 항목 목록")
    
    final_data = st.session_state.current_request.get('final_data', [])
    
    if not final_data:
        st.warning("시험 항목이 없습니다.")
        return
    
    # 샘플 데이터 로드 버튼
    if st.button("🔄 샘플 데이터 로드"):
        sample_data = [
            {
                "test_name": "Functional Test",
                "category": "Operational Test",
                "ref_standard": "",
                "sample_assembly": "HVAC",
                "test_sample_no": "S001",
                "sample_count": "3",
                "test_duration": "1",
                "test_equipment": "Test Bench"
            },
            {
                "test_name": "High Temperature Test",
                "category": "Environmental Test",
                "ref_standard": "ISO 16750-4",
                "sample_assembly": "Motor only",
                "test_sample_no": "S002",
                "sample_count": "3",
                "test_duration": "5",
                "test_equipment": "Temperature Chamber"
            }
        ]
        final_data = sample_data
        st.session_state.current_request['final_data'] = final_data
        st.rerun()
    
    # 그룹별로 분류
    grouped_data = {}
    for item in final_data:
        category = item.get('category', 'Other')
        if category not in grouped_data:
            grouped_data[category] = []
        grouped_data[category].append(item)
    
    # 테이블 형태로 표시
    for category, items in grouped_data.items():
        st.markdown(f"#### {category}")
        
        # 데이터프레임 생성
        df_data = []
        for item in items:
            df_data.append({
                "시험명": item.get('test_name', ''),
                "참조 규격": item.get('ref_standard', ''),
                "시료 구성": item.get('sample_assembly', ''),
                "샘플 번호": item.get('test_sample_no', ''),
                "시료 수": item.get('sample_count', ''),
                "시험 기간": item.get('test_duration', ''),
                "시험 장비": item.get('test_equipment', '')
            })
        
        df = pd.DataFrame(df_data)
        st.dataframe(df, use_container_width=True)
    
    st.divider()
    
    # CRUD 기능
    st.markdown("### ✏️ 시험 항목 편집")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("➕ 항목 추가", use_container_width=True):
            st.session_state.show_add_modal = True
    
    with col2:
        if st.button("🗑️ 항목 삭제", use_container_width=True):
            st.session_state.show_delete_modal = True
    
    # 추가 모달
    if st.session_state.get('show_add_modal', False):
        with st.form("add_item_form"):
            st.markdown("#### 새 시험 항목 추가")
            
            col1, col2 = st.columns(2)
            
            with col1:
                new_test_name = st.text_input("시험명")
                new_category = st.text_input("분류")
                new_ref_standard = st.text_input("참조 규격")
                new_sample_assembly = st.text_input("시료 구성")
            
            with col2:
                new_test_sample_no = st.text_input("샘플 번호")
                new_sample_count = st.text_input("시료 수")
                new_test_duration = st.text_input("시험 기간")
                new_test_equipment = st.text_input("시험 장비")
            
            col_submit, col_cancel = st.columns(2)
            
            with col_submit:
                if st.form_submit_button("추가", use_container_width=True):
                    new_item = {
                        "test_name": new_test_name,
                        "category": new_category,
                        "ref_standard": new_ref_standard,
                        "sample_assembly": new_sample_assembly,
                        "test_sample_no": new_test_sample_no,
                        "sample_count": new_sample_count,
                        "test_duration": new_test_duration,
                        "test_equipment": new_test_equipment
                    }
                    final_data.append(new_item)
                    st.session_state.current_request['final_data'] = final_data
                    st.session_state.show_add_modal = False
                    st.success("✅ 항목이 추가되었습니다!")
                    st.rerun()
            
            with col_cancel:
                if st.form_submit_button("취소", use_container_width=True):
                    st.session_state.show_add_modal = False
                    st.rerun()
    
    # 삭제 모달
    if st.session_state.get('show_delete_modal', False):
        st.markdown("#### 항목 삭제")
        
        delete_options = [item.get('test_name', f'항목 {i}') for i, item in enumerate(final_data)]
        selected_delete = st.selectbox("삭제할 항목 선택", delete_options)
        
        col_delete, col_cancel = st.columns(2)
        
        with col_delete:
            if st.button("삭제 확인", use_container_width=True):
                delete_idx = delete_options.index(selected_delete)
                
                # Functional Test 삭제 시 재확인
                if "functional" in final_data[delete_idx].get('test_name', '').lower():
                    if st.checkbox("⚠️ Functional Test를 삭제하시겠습니까?"):
                        final_data.pop(delete_idx)
                        st.session_state.current_request['final_data'] = final_data
                        st.session_state.show_delete_modal = False
                        st.success("✅ 항목이 삭제되었습니다!")
                        st.rerun()
                else:
                    final_data.pop(delete_idx)
                    st.session_state.current_request['final_data'] = final_data
                    st.session_state.show_delete_modal = False
                    st.success("✅ 항목이 삭제되었습니다!")
                    st.rerun()
        
        with col_cancel:
            if st.button("취소", use_container_width=True):
                st.session_state.show_delete_modal = False
                st.rerun()
    
    st.divider()
    
    # 버튼들
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        # 3.3.2. 계획서 저장 버튼
        if st.button("💾 계획서 저장 (Excel)", use_container_width=True):
            excel_file = export_manager.export_to_excel(
                final_data,
                st.session_state.current_user['user_name'],
                st.session_state.current_request.get('project', 'Project')
            )
            
            st.download_button(
                "⬇️ Excel 다운로드",
                excel_file,
                f"TestPlan_{st.session_state.current_user['user_name']}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
    
    with col2:
        # 3.3.3. 일정 생성 버튼
        if st.button("📅 일정 생성", use_container_width=True):
            st.session_state.schedule_data = final_data
            st.session_state.current_page = "schedule_management"
            st.rerun()


def page_schedule_management():
    """3.4. 시험 일정 관리 화면"""
    st.title("📅 시험 일정 관리")
    
    if not st.session_state.schedule_data:
        st.warning("일정 데이터가 없습니다. 계획서를 먼저 작성해주세요.")
        return
    
    # 3.4.1. 타임라인(d-day) 확인 박스
    st.markdown("### 시험 일정 (Gantt Chart)")
    
    schedule_data = st.session_state.schedule_data
    
    # 일정 생성
    schedules = schedule_manager.generate_schedule(
        schedule_data,
        st.session_state.current_request['id']
    )
    
    # Gantt Chart 생성
    fig = schedule_manager.create_gantt_chart(schedules, use_dday=True)
    st.plotly_chart(fig, use_container_width=True)
    
    # 일정 테이블 표시
    st.markdown("### 📋 일정 상세")
    
    df_schedule = pd.DataFrame(schedules)
    if not df_schedule.empty:
        display_df = df_schedule[['test_name', 'start_day', 'end_day', 'duration']]
        display_df.columns = ['시험명', '시작일 (D+)', '종료일 (D+)', '소요 기간 (일)']
        st.dataframe(display_df, use_container_width=True)
    
    st.divider()
    
    # 3.4.2. 타임라인(d-day) 저장 버튼
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("💾 일정 저장", use_container_width=True):
            db.save_schedules(
                st.session_state.current_user['id'],
                st.session_state.current_request['id'],
                schedules
            )
            st.success("✅ 일정이 저장되었습니다!")


def main():
    """메인 함수"""
    render_sidebar()
    
    # 현재 페이지 렌더링
    if st.session_state.current_page == "user_selection":
        page_user_selection()
    elif st.session_state.current_page == "test_spec_edit":
        page_test_spec_edit()
    elif st.session_state.current_page == "plan_draft":
        page_plan_draft()
    elif st.session_state.current_page == "schedule_management":
        page_schedule_management()


if __name__ == "__main__":
    main()
