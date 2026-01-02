import streamlit as st
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd

# 모듈 경로 추가
sys.path.append(str(Path(__file__).parent.parent))

from modules.database import get_request_data, get_test_items, update_test_schedule
from modules.data_processing import (
    sort_test_items_by_priority, 
    generate_planning_dataframe,
    convert_df_to_excel
)
from modules.visualization import create_category_distribution_chart

# 페이지 설정
st.set_page_config(
    page_title="계획서 작성",
    page_icon="📊",
    layout="wide"
)

# 세션 상태 확인
if 'current_user' not in st.session_state or st.session_state.current_user is None:
    st.error("❌ 먼저 사용자를 선택해주세요.")
    if st.button("🏠 홈으로 돌아가기"):
        st.switch_page("app.py")
    st.stop()

if 'current_request' not in st.session_state or st.session_state.current_request is None:
    st.error("❌ 먼저 의뢰를 선택해주세요.")
    if st.button("🏠 홈으로 돌아가기"):
        st.switch_page("app.py")
    st.stop()

# 메인 로직
def main():
    st.title("📊 시험 계획서 초안 작성")
    
    user_id = st.session_state.current_user
    request_id = st.session_state.current_request
    
    # 의뢰 데이터 조회
    request_data = get_request_data(request_id)
    
    if not request_data:
        st.error("❌ 의뢰 데이터를 찾을 수 없습니다.")
        if st.button("🏠 홈으로 돌아가기"):
            st.switch_page("app.py")
        st.stop()
    
    # 세션 정보 표시
    st.info(f"👤 사용자: {user_id} | 📋 의뢰: {request_id} - {request_data['client']}")
    
    # 시험 항목 조회
    test_items = get_test_items(request_id)
    
    if not test_items:
        st.warning("⚠️ 시험 항목이 없습니다.")
        if st.button("📋 의뢰 데이터로 돌아가기"):
            st.switch_page("pages/1_📋_Request_Data.py")
        st.stop()
    
    # 우선순위 정렬
    sorted_items = sort_test_items_by_priority(test_items)
    
    # 통계 정보
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("총 시험 항목", len(test_items))
    
    with col2:
        total_duration = sum(item.get('test_duration', 0) for item in test_items)
        st.metric("총 소요 일수", f"{total_duration:.1f}일")
    
    with col3:
        total_samples = sum(item.get('sample_count', 0) for item in test_items)
        st.metric("총 시료 수", total_samples)
    
    with col4:
        categories = set(item.get('category', 'Other') for item in test_items)
        st.metric("시험 분류 수", len(categories))
    
    # 분류별 분포 차트
    st.markdown("---")
    col1, col2 = st.columns([2, 1])
    
    with col2:
        st.subheader("📈 시험 분류 분포")
        try:
            fig = create_category_distribution_chart(test_items)
            st.plotly_chart(fig, use_container_width=True)
        except:
            st.info("차트를 생성할 수 없습니다.")
    
    with col1:
        st.subheader("📋 시험 계획서 초안")
        
        # 계획서 데이터프레임 생성
        planning_df = generate_planning_dataframe(sorted_items)
        
        # 편집 가능한 데이터프레임
        edited_df = st.data_editor(
            planning_df,
            column_config={
                "순번": st.column_config.NumberColumn("순번", disabled=True),
                "분류": st.column_config.TextColumn("분류", width="small"),
                "시험명": st.column_config.TextColumn("시험명", width="large", required=True),
                "시료수": st.column_config.NumberColumn("시료수", min_value=0),
                "소요일수": st.column_config.NumberColumn("소요일수", min_value=0, format="%.1f"),
                "시작일": st.column_config.TextColumn("시작일", disabled=True),
                "종료일": st.column_config.TextColumn("종료일", disabled=True),
                "비고": st.column_config.TextColumn("비고"),
                "포함": st.column_config.CheckboxColumn("포함", default=True)
            },
            hide_index=True,
            use_container_width=True,
            num_rows="dynamic"
        )
    
    # 상세 항목 정보
    st.markdown("---")
    st.subheader("🔍 상세 시험 항목 정보")
    
    with st.expander("상세 정보 보기"):
        for idx, item in enumerate(sorted_items):
            st.markdown(f"**{idx+1}. {item.get('test_name', 'Unknown')}**")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write(f"- 분류: {item.get('category', '')}")
                st.write(f"- 참조 규격: {item.get('ref_standard', '')}")
            
            with col2:
                st.write(f"- 시료 수: {item.get('sample_count', 0)}")
                st.write(f"- 소요 일수: {item.get('test_duration', 0)}일")
            
            with col3:
                st.write(f"- 시험 장비: {item.get('test_equipment', '')}")
                st.write(f"- 마스터 ID: {item.get('test_master_id', '')}")
            
            if item.get('custom_specs'):
                st.json(item['custom_specs'])
            
            st.markdown("---")
    
    # 버튼 섹션
    st.markdown("---")
    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
    
    with col1:
        # Excel 다운로드
        excel_data = convert_df_to_excel(edited_df)
        st.download_button(
            label="📥 Excel 다운로드",
            data=excel_data,
            file_name=f"계획서_{request_id}_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True
        )
    
    with col2:
        if st.button("💾 계획서 저장", use_container_width=True):
            st.success("✅ 계획서가 저장되었습니다!")
            st.balloons()
    
    with col3:
        if st.button("📅 일정 생성", type="primary", use_container_width=True):
            # 편집된 데이터를 세션에 저장
            st.session_state.planning_data = edited_df
            st.switch_page("pages/3_📅_Scheduling.py")
    
    with col4:
        if st.button("🏠 홈", use_container_width=True):
            st.switch_page("app.py")
    
    # 사이드바 - 정렬 옵션
    with st.sidebar:
        st.header("⚙️ 정렬 옵션")
        
        sort_option = st.selectbox(
            "정렬 기준",
            options=["우선순위", "소요일수", "시험명", "분류"]
        )
        
        if sort_option != "우선순위":
            st.info("💡 정렬 기준을 변경하려면 페이지를 새로고침하세요.")
        
        st.markdown("---")
        
        st.header("📊 계획서 옵션")
        
        show_master_id = st.checkbox("마스터 ID 표시", value=False)
        show_equipment = st.checkbox("장비 정보 표시", value=False)
        
        if show_master_id or show_equipment:
            st.info("💡 추가 정보는 상세 정보에서 확인할 수 있습니다.")

if __name__ == "__main__":
    main()
