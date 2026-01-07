import streamlit as st
import json
import pandas as pd
from modules.data_manager import DataManager
from modules.standardizer import Standardizer

st.set_page_config(page_title="Edit Extraction", page_icon="📝", layout="wide")

dm = DataManager()
standardizer = Standardizer()

st.title("📝 추출 시험 규격 편집")

# 세션 체크
if not st.session_state.current_user:
    st.warning("⚠️ 먼저 사용자를 선택하세요.")
    st.info("👉 '🏠 User Selection' 페이지로 이동하세요.")
    st.stop()

if not st.session_state.extracted_data:
    st.warning("⚠️ 추출된 데이터가 없습니다.")
    st.info("👉 '🏠 User Selection' 페이지에서 의뢰를 생성하거나 선택하세요.")
    st.stop()

# 추출 데이터 로드
extracted_data = st.session_state.extracted_data
request_info = extracted_data.get('request_info', {})
test_items = extracted_data.get('test_items', [])

# 의뢰 정보 표시
st.header("📋 의뢰 정보")
col1, col2 = st.columns(2)
with col1:
    st.info(f"**발주처**: {request_info.get('client', 'N/A')}")
with col2:
    st.info(f"**프로젝트**: {request_info.get('project', 'N/A')}")

st.divider()

# 시험 항목 편집
st.header("🧪 시험 항목 데이터")

# 통계 정보
col1, col2, col3 = st.columns(3)
with col1:
    total_items = len(test_items)
    st.metric("총 시험 항목", total_items)
with col2:
    matched_items = sum(1 for item in test_items if item.get('test_master_id'))
    st.metric("매칭된 항목", matched_items, delta=f"{matched_items}/{total_items}")
with col3:
    unmatched_items = total_items - matched_items
    st.metric("미매칭 항목", unmatched_items)

st.divider()

# 시험 항목 표시 및 편집
if 'edited_test_items' not in st.session_state:
    st.session_state.edited_test_items = test_items.copy()

edited_items = st.session_state.edited_test_items

for idx, item in enumerate(edited_items):
    status = standardizer.get_standardization_status(item)
    
    # 상태에 따른 아이콘 및 색상
    if status == "matched":
        icon = "✅"
        color = "green"
        status_text = f"마스터: {item.get('test_master_id', 'N/A')}"
    else:
        icon = "⚠️"
        color = "orange"
        status_text = "미매칭"
    
    # Expander로 각 항목 표시
    with st.expander(
        f"{icon} **{idx + 1}. {item.get('test_name', 'Unknown Test')}** - [{status_text}]",
        expanded=False
    ):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### 📄 원본 데이터")
            st.text_input(
                "원본 시험명",
                value=item.get('test_name_original', ''),
                key=f"orig_name_{idx}",
                disabled=True
            )
            st.text_input(
                "원본 분류",
                value=item.get('category_original', ''),
                key=f"orig_cat_{idx}",
                disabled=True
            )
        
        with col2:
            st.markdown("##### ✨ 표준화 데이터")
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
        if status == "matched":
            master_info = item.get('master_info', {})
            if master_info:
                st.markdown("##### 🔗 매칭된 마스터 정보")
                st.json(master_info)
        
        # 기타 정보 편집
        st.markdown("##### 📊 상세 정보")
        
        col1, col2, col3 = st.columns(3)
        with col1:
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
        
        with col2:
            item['test_sample_no'] = st.text_input(
                "샘플 번호",
                value=item.get('test_sample_no', ''),
                key=f"sample_no_{idx}"
            )
            item['sample_count'] = st.text_input(
                "시료 수",
                value=item.get('sample_count', ''),
                key=f"sample_count_{idx}"
            )
        
        with col3:
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
        
        # 마스터 ID (읽기 전용)
        st.text_input(
            "마스터 ID (읽기 전용)",
            value=item.get('test_master_id', ''),
            key=f"master_id_{idx}",
            disabled=True,
            help="LLM이 자동으로 매칭한 마스터 ID입니다."
        )
        
        # Custom Specs 편집
        st.markdown("##### ⚙️ 특수 조건 (Custom Specs)")
        custom_specs = item.get('custom_specs', {})
        
        if isinstance(custom_specs, str):
            try:
                custom_specs = json.loads(custom_specs)
            except:
                custom_specs = {}
        
        custom_specs_json = st.text_area(
            "JSON 형식으로 입력",
            value=json.dumps(custom_specs, ensure_ascii=False, indent=2),
            height=150,
            key=f"custom_{idx}"
        )
        
        try:
            item['custom_specs'] = json.loads(custom_specs_json)
        except:
            st.error("⚠️ JSON 형식이 올바르지 않습니다.")

st.divider()

# 저장 버튼
col1, col2, col3 = st.columns([2, 1, 1])

with col2:
    if st.button("💾 데이터 저장", use_container_width=True):
        # 세션에 저장
        st.session_state.extracted_data['test_items'] = edited_items
        
        # DB에 저장
        if st.session_state.current_request:
            request_id = st.session_state.current_request['id']
            dm.update_request_final_data(request_id, st.session_state.extracted_data)
            
            # 시험 항목 저장
            dm.add_test_items(edited_items, request_id)
            
            st.success("✅ 데이터가 저장되었습니다!")
        else:
            st.error("❌ 의뢰 정보가 없습니다.")

with col3:
    if st.button("📋 계획서 생성", use_container_width=True, type="primary"):
        # 세션에 저장
        st.session_state.extracted_data['test_items'] = edited_items
        
        # DB에 저장
        if st.session_state.current_request:
            request_id = st.session_state.current_request['id']
            dm.update_request_final_data(request_id, st.session_state.extracted_data)
            
            # 시험 항목 저장
            test_items_with_id = dm.add_test_items(edited_items, request_id)
            st.session_state.extracted_data['test_items'] = test_items_with_id
            
            st.success("✅ 데이터가 저장되었습니다!")
            st.info("👉 '📋 Draft Plan' 페이지로 이동하세요.")
        else:
            st.error("❌ 의뢰 정보가 없습니다.")

# 데이터 미리보기
with st.expander("🔍 전체 데이터 미리보기 (JSON)", expanded=False):
    preview_data = {
        'request_info': request_info,
        'test_items': edited_items
    }
    st.json(preview_data)
