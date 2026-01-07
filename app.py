import streamlit as st
import os
from pathlib import Path

# 페이지 설정
st.set_page_config(
    page_title="RPM - Reliable Planning Manager",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 데이터 디렉토리 생성
data_dir = Path("data")
data_dir.mkdir(exist_ok=True)

# CSV 파일 초기화
from modules.data_manager import DataManager
DataManager.initialize_csv_files()

# 세션 상태 초기화
if 'current_user' not in st.session_state:
    st.session_state.current_user = None
if 'current_request' not in st.session_state:
    st.session_state.current_request = None
if 'extracted_data' not in st.session_state:
    st.session_state.extracted_data = None
if 'draft_plan' not in st.session_state:
    st.session_state.draft_plan = None

# 메인 페이지
st.title("⚙️ RPM - Reliable Planning Manager")
st.subheader("Blower Motor Test Support System")

st.markdown("""
---
### 🎯 시스템 개요

**RPM**은 비정형 시험 규격 문서를 자동으로 파싱하고, 
지능형 시험 항목 표준화를 통해 시험 계획 초안을 작성하는 시스템입니다.

#### 핵심 기능
- 📄 **자동 문서 파싱**: PDF/DOCX 형식의 시험 규격 문서 자동 분석
- 🤖 **지능형 표준화**: AI 기반 시험 항목 표준화 및 매칭
- 📋 **계획서 자동 생성**: 표준화된 데이터 기반 시험 계획서 초안 작성
- 📅 **스케줄 관리**: Gantt Chart 기반 시험 일정 관리

#### 시작하기
왼쪽 사이드바에서 **🏠 User Selection** 페이지로 이동하여 시작하세요.

---
""")

# 사이드바 정보
with st.sidebar:
    st.markdown("### 📌 현재 세션 정보")
    
    if st.session_state.current_user:
        st.success(f"👤 사용자: {st.session_state.current_user['user_name']}")
    else:
        st.info("👤 사용자: 미선택")
    
    if st.session_state.current_request:
        st.success(f"📁 의뢰: {st.session_state.current_request.get('id', 'N/A')}")
    else:
        st.info("📁 의뢰: 미선택")
    
    st.markdown("---")
    st.markdown("### 🗂️ 데이터베이스 관리")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📥 Master", use_container_width=True):
            dm = DataManager()
            df = dm.load_master_test()
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                "⬇️ Download",
                csv,
                "Master_Test.csv",
                "text/csv",
                key='download-master'
            )
    
    with col2:
        if st.button("📥 Request", use_container_width=True):
            dm = DataManager()
            df = dm.load_request_info()
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                "⬇️ Download",
                csv,
                "Request_Info.csv",
                "text/csv",
                key='download-request'
            )
    
    col3, col4 = st.columns(2)
    with col3:
        if st.button("📥 Test Item", use_container_width=True):
            dm = DataManager()
            df = dm.load_test_item()
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                "⬇️ Download",
                csv,
                "Test_Item.csv",
                "text/csv",
                key='download-testitem'
            )
    
    with col4:
        if st.button("📥 Schedule", use_container_width=True):
            dm = DataManager()
            df = dm.load_schedule_item()
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                "⬇️ Download",
                csv,
                "Schedule_Item.csv",
                "text/csv",
                key='download-schedule'
            )

# 통계 정보 표시
col1, col2, col3, col4 = st.columns(4)

dm = DataManager()

with col1:
    user_count = len(dm.load_user_list())
    st.metric("👥 총 사용자", user_count)

with col2:
    master_count = len(dm.load_master_test())
    st.metric("📚 마스터 데이터", master_count)

with col3:
    request_count = len(dm.load_request_info())
    st.metric("📋 총 의뢰", request_count)

with col4:
    test_item_count = len(dm.load_test_item())
    st.metric("🧪 시험 항목", test_item_count)

st.markdown("---")
st.info("💡 **Tip**: 사이드바의 네비게이션을 통해 각 단계로 이동할 수 있습니다.")
