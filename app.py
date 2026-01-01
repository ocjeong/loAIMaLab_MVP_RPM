import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.figure_factory as ff
from datetime import datetime, timedelta
import graphviz
import io
import base64
import json
import random
import os

# 페이지 설정
st.set_page_config(
    page_title="Auto-Test Planner",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 앱 스타일 설정
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E3A8A;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #2563EB;
    }
    .card {
        padding: 1.5rem;
        border-radius: 0.5rem;
        background-color: #F3F4F6;
        margin-bottom: 1rem;
    }
    .success-msg {
        color: #047857;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# 세션 상태 초기화
if 'current_step' not in st.session_state:
    st.session_state.current_step = 1
if 'extracted_data' not in st.session_state:
    st.session_state.extracted_data = None
if 'test_items' not in st.session_state:
    st.session_state.test_items = None
if 'history' not in st.session_state:
    st.session_state.history = []
if 'current_project' not in st.session_state:
    st.session_state.current_project = None

# 사이드바 - 이력 관리
with st.sidebar:
    st.markdown("### 프로젝트 이력")
    
    # 샘플 이력 데이터
    if len(st.session_state.history) == 0:
        st.session_state.history = [
            {"id": 1, "name": "A사 블로워 모터 검증", "date": "2026-01-01"},
            {"id": 2, "name": "B사 신규 모델 평가", "date": "2025-12-15"}
        ]
    
    for item in st.session_state.history:
        if st.button(f"{item['name']} ({item['date']})", key=f"history_{item['id']}"):
            st.session_state.current_project = item['id']
            st.session_state.current_step = 2  # 데이터 확인/수정 단계로 이동
            st.experimental_rerun()
    
    st.divider()
    st.markdown("### 도움말")
    with st.expander("사용 방법"):
        st.markdown("""
        1. 테스트 스펙 문서를 업로드하세요
        2. 추출된 데이터를 확인하고 필요시 수정하세요
        3. 시험 계획 설정을 입력하세요
        4. 생성된 계획을 확인하고 내보내세요
        """)

# 메인 콘텐츠
st.markdown('<h1 class="main-header">Auto-Test Planner</h1>', unsafe_allow_html=True)
st.markdown("#### 블로워 모터 시험 업무 자동화 솔루션")

# 모의 데이터 생성 함수
def mock_extract_data(file):
    """문서에서 데이터를 추출하는 모의 함수"""
    # 실제 구현에서는 LLM API를 호출하여 문서 파싱
    mock_data = {
        "standard_name": "ISO-12345 / JASO D409",
        "product_name": "블로워 모터 XYZ-2000",
        "test_items": [
            {"id": 1, "name": "전압 변동 시험", "condition": "8V~16V", "criteria": "정상 작동", "duration_hours": 2, "priority": 3},
            {"id": 2, "name": "내구성 시험", "condition": "12V, 상온", "criteria": "500시간 후 성능 유지", "duration_hours": 500, "priority": 5},
            {"id": 3, "name": "소음 측정", "condition": "정격 전압", "criteria": "65dB 이하", "duration_hours": 1, "priority": 2},
            {"id": 4, "name": "온도 상승 시험", "condition": "-40°C ~ 85°C", "criteria": "기능 이상 없음", "duration_hours": 24, "priority": 4},
            {"id": 5, "name": "전류 소모 측정", "condition": "정격 전압", "criteria": "2A 이하", "duration_hours": 1, "priority": 1}
        ]
    }
    return mock_data

# 시험 항목 자동 시퀀싱 함수
def sequence_test_items(test_items):
    """시험 항목을 우선순위에 따라 정렬"""
    # 우선순위에 따라 정렬 (낮은 숫자가 높은 우선순위)
    return sorted(test_items, key=lambda x: x["priority"])

# Gantt 차트 생성 함수
def create_gantt_chart(test_items, start_date, sample_count):
    """시험 일정을 Gantt 차트로 시각화"""
    df = []
    current_date = datetime.strptime(start_date, "%Y-%m-%d")
    
    for i, item in enumerate(test_items):
        # 시료 수에 따라 병렬 처리 가능성 고려 (단순화를 위해 시료당 시간 증가)
        duration = item["duration_hours"] * (1 + (sample_count - 1) * 0.2)  # 시료가 증가할수록 시간도 일부 증가
        hours = int(duration)
        days = hours // 8  # 하루 8시간 작업 기준
        remainder_hours = hours % 8
        
        end_date = current_date + timedelta(days=days, hours=remainder_hours)
        
        df.append(dict(
            Task=item["name"],
            Start=current_date,
            Finish=end_date,
            Resource="시험장비 " + str(i % 3 + 1)  # 장비 번호 (모의)
        ))
        
        current_date = end_date
    
    return df

# 플로우차트 생성 함수
def create_flowchart(test_items):
    """시험 항목의 흐름을 시각화"""
    dot = graphviz.Digraph()
    dot.attr(rankdir='TB', size='8,5')
    
    # 노드 추가
    dot.node('start', '시작', shape='oval', style='filled', fillcolor='lightblue')
    for item in test_items:
        dot.node(str(item["id"]), item["name"], shape='box', style='filled', fillcolor='lightgreen')
    dot.node('end', '종료', shape='oval', style='filled', fillcolor='lightblue')
    
    # 엣지 추가
    dot.edge('start', str(test_items[0]["id"]))
    for i in range(len(test_items) - 1):
        dot.edge(str(test_items[i]["id"]), str(test_items[i + 1]["id"]))
    dot.edge(str(test_items[-1]["id"]), 'end')
    
    return dot

# 엑셀 다운로드 함수
def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Sheet1')
    processed_data = output.getvalue()
    return processed_data

# 단계별 UI 렌더링
if st.session_state.current_step == 1:
    # 단계 1: 파일 업로드
    st.markdown('<h2 class="sub-header">1. 테스트 스펙 문서 업로드</h2>', unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        uploaded_file = st.file_uploader("테스트 스펙 문서를 업로드하세요 (DOCX, PDF)", type=["docx", "pdf"])
        
        if uploaded_file is not None:
            st.success(f"파일이 업로드되었습니다.")
            
            # 파일 처리 중 표시
            with st.spinner('문서 분석 중...'):
                # 모의 데이터 추출
                extracted_data = mock_extract_data(uploaded_file)
                st.session_state.extracted_data = extracted_data
                st.session_state.test_items = extracted_data["test_items"]
            
            st.success('문서 분석이 완료되었습니다!')
            
            if st.button("다음 단계로", key="next_to_step2"):
                st.session_state.current_step = 2
                st.experimental_rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.current_step == 2:
    # 단계 2: 데이터 확인/수정
    st.markdown('<h2 class="sub-header">2. 추출된 데이터 확인 및 수정</h2>', unsafe_allow_html=True)
    
    if st.session_state.extracted_data:
        data = st.session_state.extracted_data
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### 기본 정보")
            standard_name = st.text_input("규격명", data["standard_name"])
            product_name = st.text_input("제품명", data["product_name"])
        
        with col2:
            st.markdown("#### 참조 문서")
            st.info("관련 표준 문서 2개가 자동으로 매핑되었습니다.")
            st.markdown("- ISO-12345: 자동차 전장부품 내구성 시험법")
            st.markdown("- JASO D409: 블로워 모터 성능 평가 기준")
        
        st.markdown("#### 시험 항목")
        
        # 데이터 에디터로 시험 항목 수정 가능하게 함
        test_items_df = pd.DataFrame(st.session_state.test_items)
        edited_df = st.data_editor(
            test_items_df,
            column_config={
                "id": "ID",
                "name": "시험 항목명",
                "condition": "시험 조건",
                "criteria": "판정 기준",
                "duration_hours": st.column_config.NumberColumn("소요 시간(시간)", min_value=0, format="%d"),
                "priority": st.column_config.NumberColumn("우선순위", min_value=1, max_value=5, format="%d")
            },
            use_container_width=True,
            num_rows="dynamic"
        )
        
        # 수정된 데이터 저장
        st.session_state.test_items = edited_df.to_dict('records')
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("이전 단계로", key="back_to_step1"):
                st.session_state.current_step = 1
                st.experimental_rerun()
        with col2:
            if st.button("다음 단계로", key="next_to_step3"):
                st.session_state.current_step = 3
                st.experimental_rerun()
    else:
        st.error("추출된 데이터가 없습니다. 문서를 다시 업로드해주세요.")
        if st.button("문서 업로드로 돌아가기"):
            st.session_state.current_step = 1
            st.experimental_rerun()

elif st.session_state.current_step == 3:
    # 단계 3: 계획 수립 설정
    st.markdown('<h2 class="sub-header">3. 시험 계획 설정</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        sample_count = st.number_input("시료 수량", min_value=1, max_value=10, value=3)
        start_date = st.date_input("시험 시작일", datetime.now()).strftime("%Y-%m-%d")
    
    with col2:
        st.markdown("#### 우선순위 조정")
        st.info("시험 항목의 우선순위를 조정하면 시험 순서가 변경됩니다.")
        
        # 우선순위 자동 조정 옵션
        auto_sequence = st.checkbox("자동 시퀀싱 사용", value=True)
        
        if auto_sequence:
            st.session_state.test_items = sequence_test_items(st.session_state.test_items)
            st.success("시험 항목이 우선순위에 따라 자동 정렬되었습니다.")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("이전 단계로", key="back_to_step2"):
            st.session_state.current_step = 2
            st.experimental_rerun()
    with col2:
        if st.button("계획 생성하기", key="next_to_step4"):
            st.session_state.current_step = 4
            st.session_state.sample_count = sample_count
            st.session_state.start_date = start_date
            st.experimental_rerun()

elif st.session_state.current_step == 4:
    # 단계 4: 결과 시각화
    st.markdown('<h2 class="sub-header">4. 시험 계획 결과</h2>', unsafe_allow_html=True)
    
    # 탭으로 다양한 시각화 제공
    tab1, tab2, tab3 = st.tabs(["시험 순서 플로우차트", "일정 간트차트", "상세 계획표"])
    
    with tab1:
        st.markdown("#### 시험 항목 흐름도")
        flowchart = create_flowchart(st.session_state.test_items)
        st.graphviz_chart(flowchart)
    
    with tab2:
        st.markdown("#### 예상 시험 일정")
        gantt_data = create_gantt_chart(
            st.session_state.test_items, 
            st.session_state.start_date,
            st.session_state.sample_count
        )
        
        fig = ff.create_gantt(
            gantt_data, 
            colors=['#779ECB', '#83C25A', '#F1CE63', '#E87653', '#9F53E8'],
            index_col='Resource',
            show_colorbar=True,
            group_tasks=True
        )
        fig.update_layout(autosize=True, height=500)
        st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        st.markdown("#### 시험 계획 상세표")
        
        # 계획표 생성
        plan_data = []
        start = datetime.strptime(st.session_state.start_date, "%Y-%m-%d")
        
        for i, item in enumerate(st.session_state.test_items):
            duration = item["duration_hours"]
            days = duration // 8
            end = start + timedelta(days=days, hours=duration % 8)
            
            plan_data.append({
                "순서": i+1,
                "시험 항목": item["name"],
                "시험 조건": item["condition"],
                "판정 기준": item["criteria"],
                "시작일": start.strftime("%Y-%m-%d"),
                "종료일": end.strftime("%Y-%m-%d"),
                "소요 시간(시간)": duration,
                "시료 수": st.session_state.sample_count
            })
            
            start = end
        
        plan_df = pd.DataFrame(plan_data)
        st.dataframe(plan_df, use_container_width=True)
    
    # 다음 단계 버튼
    col1, col2 = st.columns(2)
    with col1:
        if st.button("계획 수정하기", key="back_to_step3"):
            st.session_state.current_step = 3
            st.experimental_rerun()
    with col2:
        if st.button("계획 내보내기", key="next_to_step5"):
            st.session_state.current_step = 5
            st.session_state.plan_df = plan_df
            st.experimental_rerun()

elif st.session_state.current_step == 5:
    # 단계 5: 내보내기
    st.markdown('<h2 class="sub-header">5. 계획 내보내기</h2>', unsafe_allow_html=True)
    
    st.markdown("#### 시험 계획서가 생성되었습니다")
    st.success("모든 단계가 완료되었습니다. 아래 옵션에서 원하는 형식으로 내보내세요.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Excel 파일로 내보내기")
        excel_data = to_excel(st.session_state.plan_df)
        st.download_button(
            label="Excel 다운로드",
            data=excel_data,
            file_name="블로워모터_시험계획서.xlsx",
            mime="application/vnd.ms-excel"
        )
    
    with col2:
        st.markdown("#### 보고서 형식으로 내보내기")
        if st.button("PDF 보고서 생성"):
            st.info("PDF 보고서가 생성 중입니다...")
            # 실제 구현에서는 PDF 생성 로직 추가
            st.success("PDF 보고서가 생성되었습니다!")
            st.markdown("[보고서 다운로드](#)")  # 실제 구현 시 링크 추가
    
    # 프로젝트 저장
    st.markdown("#### 프로젝트 저장")
    project_name = st.text_input("프로젝트 이름", "블로워 모터 시험 계획")
    
    if st.button("프로젝트 저장하기"):
        # 현재 프로젝트를 이력에 추가
        new_project = {
            "id": len(st.session_state.history) + 1,
            "name": project_name,
            "date": datetime.now().strftime("%Y-%m-%d")
        }
        st.session_state.history.append(new_project)
        st.success(f"프로젝트 '{project_name}'이(가) 저장되었습니다!")
    
    if st.button("새 프로젝트 시작하기"):
        # 세션 상태 초기화
        st.session_state.current_step = 1
        st.session_state.extracted_data = None
        st.session_state.test_items = None
        st.session_state.current_project = None
        st.experimental_rerun()

# 푸터
st.markdown("---")
st.markdown("© 2026 Auto-Test Planner | 효성전기 연구지원팀")
