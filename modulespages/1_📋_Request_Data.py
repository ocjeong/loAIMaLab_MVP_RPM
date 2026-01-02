import streamlit as st
import sys
from pathlib import Path
from datetime import datetime
import json

# 모듈 경로 추가
sys.path.append(str(Path(__file__).parent.parent))

from modules.database import (
    get_master_data, create_request, get_request_data, 
    update_request_data, save_test_items, get_test_items,
    update_master_aliases
)
from modules.gemini_api import extract_test_data, match_to_master
from modules.data_processing import validate_test_items

# 페이지 설정
st.set_page_config(
    page_title="시험 의뢰 데이터",
    page_icon="📋",
    layout="wide"
)

# 세션 상태 확인
if 'current_user' not in st.session_state or st.session_state.current_user is None:
    st.error("❌ 먼저 사용자를 선택해주세요.")
    if st.button("🏠 홈으로 돌아가기"):
        st.switch_page("app.py")
    st.stop()

# 메인 로직
def main():
    st.title("📋 시험 의뢰 항목 데이터")
    
    user_id = st.session_state.current_user
    
    # 세션 정보 표시
    st.info(f"👤 사용자: {user_id}")
    
    # 새 의뢰 생성 모드
    if 'uploaded_file' in st.session_state and st.session_state.uploaded_file is not None:
        handle_new_request()
    
    # 기존 의뢰 수정 모드
    elif st.session_state.current_request:
        handle_existing_request()
    
    else:
        st.warning("⚠️ 의뢰를 선택하거나 새 파일을 업로드해주세요.")
        if st.button("🏠 홈으로 돌아가기"):
            st.switch_page("app.py")

def handle_new_request():
    """새 의뢰 생성 처리"""
    
    st.header("🆕 새 의뢰 생성")
    
    uploaded_file = st.session_state.uploaded_file
    
    # 파일 정보 표시
    st.success(f"✅ 업로드된 파일 처리 중")
    
    # 마스터 데이터 로드
    master_data = get_master_data()
    
    # 파일 파싱
    if 'extracted_data' not in st.session_state or st.session_state.extracted_data is None:
        with st.spinner("🤖 AI가 문서를 분석하고 있습니다... (최대 30초 소요)"):
            try:
                file_bytes = uploaded_file.getvalue()
                file_type = "application/pdf" if uploaded_file.name.endswith('.pdf') else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                
                extracted_data = extract_test_data(file_bytes, file_type, master_data)
                st.session_state.extracted_data = extracted_data
                
                st.success("✅ 데이터 추출 완료!")
                
            except Exception as e:
                st.error(f"❌ 데이터 추출 실패: {str(e)}")
                if st.button("🏠 홈으로 돌아가기"):
                    st.session_state.uploaded_file = None
                    st.switch_page("app.py")
                st.stop()
    
    extracted_data = st.session_state.extracted_data
    
    # 의뢰 정보 입력
    st.markdown("---")
    st.subheader("📝 의뢰 기본 정보")
    
    col1, col2 = st.columns(2)
    
    with col1:
        client = st.text_input(
            "발주처",
            value=extracted_data.get('request_info', {}).get('client', ''),
            key="client_input"
        )
    
    with col2:
        project = st.text_input(
            "프로젝트명",
            value=extracted_data.get('request_info', {}).get('project', ''),
            key="project_input"
        )
    
    # 추출된 시험 항목 표시 및 편집
    st.markdown("---")
    st.subheader("🔬 추출된 시험 항목 데이터")
    
    test_items = extracted_data.get('test_items', [])
    
    if not test_items:
        st.warning("⚠️ 추출된 시험 항목이 없습니다.")
        if st.button("🏠 홈으로 돌아가기"):
            st.session_state.uploaded_file = None
            st.session_state.extracted_data = None
            st.switch_page("app.py")
        st.stop()
    
    # 시험 항목 편집
    edited_items = []
    
    for idx, item in enumerate(test_items):
        with st.expander(f"#{idx+1} {item.get('test_name', 'Unknown Test')}", expanded=(idx < 3)):
            col1, col2 = st.columns(2)
            
            with col1:
                test_name = st.text_input(
                    "시험명",
                    value=item.get('test_name', ''),
                    key=f"name_{idx}"
                )
                
                category = st.selectbox(
                    "분류",
                    options=['Environmental', 'Electrical', 'Endurance', 'Mechanical', 'Other'],
                    index=['Environmental', 'Electrical', 'Endurance', 'Mechanical', 'Other'].index(
                        item.get('category', 'Other')
                    ) if item.get('category', 'Other') in ['Environmental', 'Electrical', 'Endurance', 'Mechanical', 'Other'] else 4,
                    key=f"cat_{idx}"
                )
                
                ref_standard = st.text_input(
                    "참조 규격",
                    value=item.get('ref_standard', ''),
                    key=f"ref_{idx}"
                )
                
                sample_assembly = st.text_input(
                    "시료 구성",
                    value=item.get('sample_assembly', ''),
                    key=f"assembly_{idx}"
                )
            
            with col2:
                sample_count = st.number_input(
                    "시료 수",
                    min_value=0,
                    value=int(item.get('sample_count', 1)),
                    key=f"count_{idx}"
                )
                
                test_duration = st.number_input(
                    "소요 일수",
                    min_value=0.0,
                    value=float(item.get('test_duration', 1.0)),
                    step=0.5,
                    key=f"dur_{idx}"
                )
                
                test_equipment = st.text_input(
                    "시험 장비",
                    value=item.get('test_equipment', ''),
                    key=f"equip_{idx}"
                )
                
                test_master_id = st.text_input(
                    "마스터 ID",
                    value=item.get('test_master_id', ''),
                    key=f"master_{idx}",
                    help="자동 매칭된 표준 시험 ID"
                )
            
            # Custom Specs 표시
            st.markdown("**세부 조건 (Custom Specs)**")
            custom_specs = item.get('custom_specs', {})
            st.json(custom_specs)
            
            # 편집된 항목 저장
            edited_items.append({
                'test_name': test_name,
                'category': category,
                'ref_standard': ref_standard,
                'sample_assembly': sample_assembly,
                'test_sample_no': item.get('test_sample_no', 0),
                'sample_count': sample_count,
                'test_duration': test_duration,
                'test_equipment': test_equipment,
                'test_master_id': test_master_id,
                'custom_specs': custom_specs
            })
    
    # 버튼 섹션
    st.markdown("---")
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        if st.button("📊 계획서 생성", type="primary", use_container_width=True):
            # 데이터 검증
            validated_items = validate_test_items(edited_items)
            
            # 의뢰 생성
            request_id = create_request(
                st.session_state.current_user,
                client,
                project,
                {
                    'request_info': {'client': client, 'project': project},
                    'test_items': validated_items
                }
            )
            
            # 시험 항목 저장
            save_test_items(request_id, validated_items)
            
            # 마스터 데이터 학습
            for item in validated_items:
                if item.get('test_master_id'):
                    update_master_aliases(item['test_master_id'], item['test_name'])
            
            st.session_state.current_request = request_id
            st.session_state.uploaded_file = None
            st.session_state.extracted_data = None
            
            st.success(f"✅ 의뢰 {request_id}가 생성되었습니다!")
            st.balloons()
            
            # 계획서 페이지로 이동
            st.switch_page("pages/2_📊_Planning.py")
    
    with col2:
        if st.button("💾 임시 저장", use_container_width=True):
            # 임시 저장 로직
            validated_items = validate_test_items(edited_items)
            
            request_id = create_request(
                st.session_state.current_user,
                client,
                project,
                {
                    'request_info': {'client': client, 'project': project},
                    'test_items': validated_items
                }
            )
            
            save_test_items(request_id, validated_items)
            
            st.session_state.current_request = request_id
            st.session_state.uploaded_file = None
            st.session_state.extracted_data = None
            
            st.success(f"✅ 의뢰 {request_id}가 임시 저장되었습니다!")
    
    with col3:
        if st.button("🏠 홈", use_container_width=True):
            st.session_state.uploaded_file = None
            st.session_state.extracted_data = None
            st.switch_page("app.py")

def handle_existing_request():
    """기존 의뢰 수정 처리"""
    
    request_id = st.session_state.current_request
    request_data = get_request_data(request_id)
    
    if not request_data:
        st.error("❌ 의뢰 데이터를 찾을 수 없습니다.")
        if st.button("🏠 홈으로 돌아가기"):
            st.switch_page("app.py")
        st.stop()
    
    st.header(f"📝 의뢰 수정: {request_id}")
    
    # 의뢰 정보 표시
    st.info(f"📋 발주처: {request_data['client']} | 프로젝트: {request_data['project']}")
    
    # 시험 항목 조회
    test_items = get_test_items(request_id)
    
    if not test_items:
        st.warning("⚠️ 시험 항목이 없습니다.")
        if st.button("🏠 홈으로 돌아가기"):
            st.switch_page("app.py")
        st.stop()
    
    st.markdown("---")
    st.subheader("🔬 시험 항목 데이터")
    
    # 시험 항목 편집
    edited_items = []
    
    for idx, item in enumerate(test_items):
        with st.expander(f"#{idx+1} {item.get('test_name', 'Unknown Test')}", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                test_name = st.text_input(
                    "시험명",
                    value=item.get('test_name', ''),
                    key=f"name_{idx}"
                )
                
                category = st.selectbox(
                    "분류",
                    options=['Environmental', 'Electrical', 'Endurance', 'Mechanical', 'Other'],
                    index=['Environmental', 'Electrical', 'Endurance', 'Mechanical', 'Other'].index(
                        item.get('category', 'Other')
                    ) if item.get('category', 'Other') in ['Environmental', 'Electrical', 'Endurance', 'Mechanical', 'Other'] else 4,
                    key=f"cat_{idx}"
                )
                
                ref_standard = st.text_input(
                    "참조 규격",
                    value=item.get('ref_standard', ''),
                    key=f"ref_{idx}"
                )
                
                sample_assembly = st.text_input(
                    "시료 구성",
                    value=item.get('sample_assembly', ''),
                    key=f"assembly_{idx}"
                )
            
            with col2:
                sample_count = st.number_input(
                    "시료 수",
                    min_value=0,
                    value=int(item.get('sample_count', 1)),
                    key=f"count_{idx}"
                )
                
                test_duration = st.number_input(
                    "소요 일수",
                    min_value=0.0,
                    value=float(item.get('test_duration', 1.0)),
                    step=0.5,
                    key=f"dur_{idx}"
                )
                
                test_equipment = st.text_input(
                    "시험 장비",
                    value=item.get('test_equipment', ''),
                    key=f"equip_{idx}"
                )
                
                test_master_id = st.text_input(
                    "마스터 ID",
                    value=item.get('test_master_id', ''),
                    key=f"master_{idx}"
                )
            
            # Custom Specs
            st.markdown("**세부 조건**")
            st.json(item.get('custom_specs', {}))
            
            # 편집된 항목 저장
            edited_item = {
                'id': item.get('id'),
                'test_name': test_name,
                'category': category,
                'ref_standard': ref_standard,
                'sample_assembly': sample_assembly,
                'test_sample_no': item.get('test_sample_no', 0),
                'sample_count': sample_count,
                'test_duration': test_duration,
                'test_equipment': test_equipment,
                'test_master_id': test_master_id,
                'custom_specs': item.get('custom_specs', {}),
                'priority_order': item.get('priority_order', idx + 1),
                'start_date': item.get('start_date'),
                'end_date': item.get('end_date'),
                'is_included': item.get('is_included', True)
            }
            edited_items.append(edited_item)
    
    # 버튼 섹션
    st.markdown("---")
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        if st.button("💾 변경사항 저장", type="primary", use_container_width=True):
            # 데이터 업데이트
            validated_items = validate_test_items(edited_items)
            save_test_items(request_id, validated_items)
            
            # 마스터 데이터 학습
            for item in validated_items:
                if item.get('test_master_id'):
                    update_master_aliases(item['test_master_id'], item['test_name'])
            
            st.success("✅ 변경사항이 저장되었습니다!")
    
    with col2:
        if st.button("📊 계획서 보기", use_container_width=True):
            st.switch_page("pages/2_📊_Planning.py")
    
    with col3:
        if st.button("🏠 홈", use_container_width=True):
            st.switch_page("app.py")

if __name__ == "__main__":
    main()
