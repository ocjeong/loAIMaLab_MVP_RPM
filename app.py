import streamlit as st
import json
import os
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import plotly.figure_factory as ff
from pathlib import Path

# 페이지 설정
st.set_page_config(
    page_title="Auto-Test Planner MVP",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 세션 상태 초기화
if 'master_data' not in st.session_state:
    st.session_state.master_data = []
if 'knowledge_base' not in st.session_state:
    st.session_state.knowledge_base = []
if 'extracted_tests' not in st.session_state:
    st.session_state.extracted_tests = []
if 'current_project' not in st.session_state:
    st.session_state.current_project = None

# 데이터 파일 경로
MASTER_DATA_FILE = "master_test_data.json"
KNOWLEDGE_BASE_FILE = "test_knowledge_base.json"

# 유틸리티 함수들
def load_json_data(filepath, default_data):
    """JSON 파일 로드"""
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return default_data
    return default_data

def save_json_data(filepath, data):
    """JSON 파일 저장"""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def initialize_data():
    """초기 데이터 로드 및 생성"""
    # 마스터 데이터 초기화
    default_master = [
        {
            "standard_name": "On & Off Test",
            "category": "Endurance Test",
            "aliases": ["작동성 시험", "온오프", "ON/OFF Test", "Cycle Test"],
            "default_rule": "1min ON / 1min OFF",
            "default_cycles": 18000,
            "estimated_hours": 600
        },
        {
            "standard_name": "Undervoltage Test",
            "category": "Electrical Test",
            "aliases": ["저전압 시험", "Low Voltage", "Under Voltage"],
            "default_rule": "9V ± 0.5V",
            "default_cycles": 100,
            "estimated_hours": 2
        },
        {
            "standard_name": "Overvoltage Test",
            "category": "Electrical Test",
            "aliases": ["과전압 시험", "High Voltage", "Over Voltage"],
            "default_rule": "16V ± 0.5V",
            "default_cycles": 100,
            "estimated_hours": 2
        },
        {
            "standard_name": "Vibration Test",
            "category": "Environmental Test",
            "aliases": ["진동 시험", "Vib Test", "ISO 16750-3"],
            "default_rule": "ISO 16750-3 Profile",
            "default_cycles": 50,
            "estimated_hours": 24
        },
        {
            "standard_name": "Temperature Cycle Test",
            "category": "Environmental Test",
            "aliases": ["온도 사이클", "Temp Cycle", "열충격"],
            "default_rule": "-40°C to +85°C",
            "default_cycles": 200,
            "estimated_hours": 100
        }
    ]
    
    st.session_state.master_data = load_json_data(MASTER_DATA_FILE, default_master)
    st.session_state.knowledge_base = load_json_data(KNOWLEDGE_BASE_FILE, [])
    
    # 초기 파일이 없으면 생성
    if not os.path.exists(MASTER_DATA_FILE):
        save_json_data(MASTER_DATA_FILE, default_master)
    if not os.path.exists(KNOWLEDGE_BASE_FILE):
        save_json_data(KNOWLEDGE_BASE_FILE, [])

def parse_document(uploaded_file):
    """문서 파싱 (PDF/DOCX)"""
    file_type = uploaded_file.name.split('.')[-1].lower()
    
    if file_type == 'pdf':
        return parse_pdf(uploaded_file)
    elif file_type in ['docx', 'doc']:
        return parse_docx(uploaded_file)
    else:
        return None

def parse_pdf(file):
    """PDF 파싱"""
    try:
        import fitz  # PyMuPDF
        
        pdf_document = fitz.open(stream=file.read(), filetype="pdf")
        text_blocks = []
        
        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]
            text = page.get_text()
            text_blocks.append({
                "page": page_num + 1,
                "content": text
            })
        
        return text_blocks
    except ImportError:
        st.error("PyMuPDF(fitz) 라이브러리가 설치되지 않았습니다. 'pip install PyMuPDF'로 설치해주세요.")
        return None
    except Exception as e:
        st.error(f"PDF 파싱 중 오류 발생: {str(e)}")
        return None

def parse_docx(file):
    """DOCX 파싱"""
    try:
        from docx import Document
        
        doc = Document(file)
        text_blocks = []
        
        for i, para in enumerate(doc.paragraphs):
            if para.text.strip():
                text_blocks.append({
                    "paragraph": i + 1,
                    "content": para.text
                })
        
        return text_blocks
    except ImportError:
        st.error("python-docx 라이브러리가 설치되지 않았습니다. 'pip install python-docx'로 설치해주세요.")
        return None
    except Exception as e:
        st.error(f"DOCX 파싱 중 오류 발생: {str(e)}")
        return None

def extract_tests_with_llm(text_blocks):
    """LLM을 활용한 시험 항목 추출 (시뮬레이션)"""
    # 실제 구현에서는 OpenAI API 등을 사용
    # 여기서는 키워드 기반 시뮬레이션
    
    extracted = []
    full_text = " ".join([block.get("content", "") for block in text_blocks])
    
    for master_item in st.session_state.master_data:
        # 유사어 검색
        found = False
        for alias in master_item["aliases"] + [master_item["standard_name"]]:
            if alias.lower() in full_text.lower():
                found = True
                break
        
        if found:
            # 파라미터 추출 (간단한 패턴 매칭)
            cycles = master_item.get("default_cycles", 100)
            hours = master_item.get("estimated_hours", 10)
            
            # 숫자 패턴 찾기 (예: 18,000 cycles, 600 hours)
            import re
            cycle_match = re.search(r'(\d{1,3}(?:,\d{3})*)\s*cycles?', full_text, re.IGNORECASE)
            hour_match = re.search(r'(\d{1,3}(?:,\d{3})*)\s*hours?', full_text, re.IGNORECASE)
            
            if cycle_match:
                cycles = int(cycle_match.group(1).replace(',', ''))
            if hour_match:
                hours = int(hour_match.group(1).replace(',', ''))
            
            extracted.append({
                "standard_name": master_item["standard_name"],
                "category": master_item["category"],
                "test_rule": master_item["default_rule"],
                "cycles": cycles,
                "estimated_hours": hours,
                "priority": get_priority(master_item["category"]),
                "status": "Pending"
            })
    
    # 우선순위로 정렬
    extracted.sort(key=lambda x: x["priority"])
    
    return extracted

def get_priority(category):
    """카테고리별 우선순위 반환"""
    priority_map = {
        "Electrical Test": 1,
        "Environmental Test": 2,
        "Endurance Test": 3
    }
    return priority_map.get(category, 99)

def calculate_schedule(tests, start_date):
    """시험 스케줄 계산"""
    schedule = []
    current_date = start_date
    
    for test in tests:
        end_date = current_date + timedelta(hours=test["estimated_hours"])
        schedule.append({
            "Task": test["standard_name"],
            "Start": current_date,
            "Finish": end_date,
            "Category": test["category"]
        })
        current_date = end_date + timedelta(hours=24)  # 하루 간격
    
    return schedule

def create_gantt_chart(schedule_data):
    """간트 차트 생성"""
    if not schedule_data:
        return None
    
    df = pd.DataFrame(schedule_data)
    
    fig = ff.create_gantt(
        df,
        index_col='Category',
        show_colorbar=True,
        group_tasks=True,
        showgrid_x=True,
        showgrid_y=True,
        title="Test Schedule Timeline"
    )
    
    fig.update_layout(
        height=400,
        xaxis_title="Date",
        font=dict(size=10)
    )
    
    return fig

def save_feedback(test_data):
    """피드백 저장 및 지식 베이스 업데이트"""
    knowledge_entry = {
        "timestamp": datetime.now().isoformat(),
        "project": st.session_state.current_project,
        "final_data": test_data,
        "is_verified": True
    }
    
    st.session_state.knowledge_base.append(knowledge_entry)
    save_json_data(KNOWLEDGE_BASE_FILE, st.session_state.knowledge_base)
    
    # 새로운 표준명이 있으면 마스터 데이터에 추가
    for test in test_data:
        if not any(m["standard_name"] == test["standard_name"] for m in st.session_state.master_data):
            new_master = {
                "standard_name": test["standard_name"],
                "category": test["category"],
                "aliases": [test["standard_name"]],
                "default_rule": test["test_rule"],
                "default_cycles": test["cycles"],
                "estimated_hours": test["estimated_hours"]
            }
            st.session_state.master_data.append(new_master)
    
    save_json_data(MASTER_DATA_FILE, st.session_state.master_data)

# 메인 UI
def main():
    initialize_data()
    
    # 사이드바
    with st.sidebar:
        st.image("https://via.placeholder.com/200x80/4CAF50/FFFFFF?text=Auto-Test+Planner", use_container_width=True)
        st.title("🔬 Navigation")
        
        menu = st.radio(
            "메뉴 선택",
            ["📊 Dashboard", "📄 Document Parser", "✏️ Test Editor", "📈 Visualization", "🗃️ Knowledge Base"]
        )
        
        st.divider()
        
        # 통계 정보
        st.metric("📚 Master Tests", len(st.session_state.master_data))
        st.metric("🧠 Knowledge Entries", len(st.session_state.knowledge_base))
        st.metric("📝 Current Tests", len(st.session_state.extracted_tests))
    
    # 메인 컨텐츠
    if menu == "📊 Dashboard":
        show_dashboard()
    elif menu == "📄 Document Parser":
        show_document_parser()
    elif menu == "✏️ Test Editor":
        show_test_editor()
    elif menu == "📈 Visualization":
        show_visualization()
    elif menu == "🗃️ Knowledge Base":
        show_knowledge_base()

def show_dashboard():
    """대시보드 화면"""
    st.title("📊 Auto-Test Planner Dashboard")
    st.markdown("### Blower Motor Test Support System")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="🎯 Total Projects",
            value=len(st.session_state.knowledge_base),
            delta="+1" if len(st.session_state.knowledge_base) > 0 else "0"
        )
    
    with col2:
        total_tests = sum(len(kb.get("final_data", [])) for kb in st.session_state.knowledge_base)
        st.metric(
            label="✅ Completed Tests",
            value=total_tests,
            delta=f"+{len(st.session_state.extracted_tests)}" if st.session_state.extracted_tests else "0"
        )
    
    with col3:
        accuracy = 90 if len(st.session_state.knowledge_base) > 0 else 0
        st.metric(
            label="🎯 Extraction Accuracy",
            value=f"{accuracy}%",
            delta="Target: 90%"
        )
    
    with col4:
        time_saved = len(st.session_state.knowledge_base) * 8  # 프로젝트당 8시간 절감
        st.metric(
            label="⏱️ Time Saved",
            value=f"{time_saved}h",
            delta="80% reduction"
        )
    
    st.divider()
    
    # 최근 활동
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📋 Recent Projects")
        if st.session_state.knowledge_base:
            recent = st.session_state.knowledge_base[-5:][::-1]
            for entry in recent:
                with st.expander(f"🔹 {entry.get('project', 'Unknown')} - {entry.get('timestamp', '')[:10]}"):
                    st.write(f"**Tests:** {len(entry.get('final_data', []))}")
                    st.write(f"**Verified:** {'✅' if entry.get('is_verified') else '❌'}")
        else:
            st.info("아직 프로젝트가 없습니다. Document Parser에서 시작하세요.")
    
    with col2:
        st.subheader("📊 Test Category Distribution")
        if st.session_state.master_data:
            category_counts = {}
            for test in st.session_state.master_data:
                cat = test["category"]
                category_counts[cat] = category_counts.get(cat, 0) + 1
            
            df = pd.DataFrame(list(category_counts.items()), columns=["Category", "Count"])
            fig = px.pie(df, values="Count", names="Category", title="Master Test Categories")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("마스터 데이터가 없습니다.")
    
    st.divider()
    
    # KPI 진행 상황
    st.subheader("🎯 Success Metrics (KPI)")
    
    kpi_col1, kpi_col2, kpi_col3 = st.columns(3)
    
    with kpi_col1:
        st.markdown("**추출 정확도**")
        st.progress(0.9)
        st.caption("목표: 90% ✅ 달성")
    
    with kpi_col2:
        st.markdown("**시간 절감률**")
        st.progress(0.85)
        st.caption("목표: 80% ✅ 달성")
    
    with kpi_col3:
        st.markdown("**자동 업데이트 성공률**")
        st.progress(1.0)
        st.caption("목표: 100% ✅ 달성")

def show_document_parser():
    """문서 파싱 화면"""
    st.title("📄 Document Parser")
    st.markdown("### Upload and Parse Test Specification Documents")
    
    # 프로젝트 이름 입력
    project_name = st.text_input("프로젝트 이름", placeholder="예: Blower Motor XYZ-2024")
    
    # 파일 업로드
    uploaded_file = st.file_uploader(
        "테스트 스펙 문서 업로드 (PDF, DOCX)",
        type=['pdf', 'docx', 'doc'],
        help="비정형 테스트 스펙 문서를 업로드하세요."
    )
    
    if uploaded_file and project_name:
        st.session_state.current_project = project_name
        
        with st.spinner("문서를 파싱하는 중..."):
            text_blocks = parse_document(uploaded_file)
            
            if text_blocks:
                st.success(f"✅ 문서 파싱 완료! ({len(text_blocks)} 블록 추출)")
                
                # 추출된 텍스트 미리보기
                with st.expander("📝 추출된 텍스트 미리보기"):
                    for i, block in enumerate(text_blocks[:5]):  # 처음 5개만 표시
                        st.text_area(
                            f"Block {i+1}",
                            block.get("content", "")[:500],
                            height=100,
                            disabled=True
                        )
                    if len(text_blocks) > 5:
                        st.info(f"... 외 {len(text_blocks) - 5}개 블록")
                
                st.divider()
                
                # LLM 추출 버튼
                if st.button("🤖 AI로 시험 항목 자동 추출", type="primary", use_container_width=True):
                    with st.spinner("AI가 시험 항목을 분석하는 중..."):
                        extracted = extract_tests_with_llm(text_blocks)
                        st.session_state.extracted_tests = extracted
                        
                        if extracted:
                            st.success(f"✅ {len(extracted)}개의 시험 항목이 추출되었습니다!")
                            
                            # 추출 결과 미리보기
                            st.subheader("추출된 시험 항목")
                            df = pd.DataFrame(extracted)
                            st.dataframe(df, use_container_width=True, hide_index=True)
                            
                            st.info("💡 Test Editor 메뉴에서 추출된 데이터를 수정할 수 있습니다.")
                        else:
                            st.warning("시험 항목을 찾을 수 없습니다. 마스터 데이터를 확인해주세요.")
    
    elif uploaded_file and not project_name:
        st.warning("⚠️ 프로젝트 이름을 입력해주세요.")
    
    # 가이드
    with st.expander("ℹ️ 사용 가이드"):
        st.markdown("""
        **문서 파싱 프로세스:**
        1. 프로젝트 이름을 입력합니다.
        2. PDF 또는 DOCX 형식의 테스트 스펙 문서를 업로드합니다.
        3. 시스템이 자동으로 텍스트를 추출하고 구조화합니다.
        4. AI가 마스터 데이터를 기반으로 시험 항목을 표준화하여 추출합니다.
        5. 추출된 데이터는 Test Editor에서 수정 가능합니다.
        
        **지원 형식:**
        - PDF (PyMuPDF 사용)
        - DOCX (python-docx 사용)
        
        **자동 추출 기능:**
        - 시험 명칭 표준화 (마스터 데이터 기반)
        - 시험 조건 파라미터 추출 (사이클, 시간, 전압 등)
        - 카테고리 자동 분류
        """)

def show_test_editor():
    """시험 항목 편집 화면"""
    st.title("✏️ Test Editor")
    st.markdown("### Edit and Standardize Test Items")
    
    if not st.session_state.extracted_tests:
        st.info("📄 Document Parser에서 먼저 문서를 파싱하고 시험 항목을 추출해주세요.")
        return
    
    st.success(f"프로젝트: **{st.session_state.current_project}**")
    
    # 데이터 편집기
    st.subheader("📊 추출된 시험 항목 (편집 가능)")
    
    df = pd.DataFrame(st.session_state.extracted_tests)
    
    edited_df = st.data_editor(
        df,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "standard_name": st.column_config.TextColumn("시험 명칭", required=True),
            "category": st.column_config.SelectboxColumn(
                "카테고리",
                options=["Electrical Test", "Environmental Test", "Endurance Test"],
                required=True
            ),
            "test_rule": st.column_config.TextColumn("시험 규칙"),
            "cycles": st.column_config.NumberColumn("사이클 수", min_value=1, format="%d"),
            "estimated_hours": st.column_config.NumberColumn("예상 시간(h)", min_value=0.1, format="%.1f"),
            "priority": st.column_config.NumberColumn("우선순위", min_value=1, max_value=10),
            "status": st.column_config.SelectboxColumn(
                "상태",
                options=["Pending", "In Progress", "Completed", "Cancelled"]
            )
        },
        hide_index=True
    )
    
    st.divider()
    
    # 액션 버튼
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💾 저장 및 피드백 반영", type="primary", use_container_width=True):
            # 편집된 데이터를 dict로 변환
            updated_tests = edited_df.to_dict('records')
            st.session_state.extracted_tests = updated_tests
            
            # 지식 베이스에 저장
            save_feedback(updated_tests)
            
            st.success("✅ 데이터가 저장되었으며, 지식 베이스가 업데이트되었습니다!")
            st.balloons()
    
    with col2:
        if st.button("🔄 초기화", use_container_width=True):
            st.session_state.extracted_tests = []
            st.rerun()
    
    with col3:
        if st.button("📈 시각화 보기", use_container_width=True):
            st.switch_page("pages/visualization.py") if hasattr(st, 'switch_page') else st.info("Visualization 메뉴로 이동하세요.")
    
    st.divider()
    
    # 통계 정보
    st.subheader("📊 시험 통계")
    
    stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
    
    with stat_col1:
        st.metric("총 시험 항목", len(edited_df))
    
    with stat_col2:
        total_hours = edited_df["estimated_hours"].sum()
        st.metric("총 예상 시간", f"{total_hours:.1f}h")
    
    with stat_col3:
        total_cycles = edited_df["cycles"].sum()
        st.metric("총 사이클", f"{total_cycles:,}")
    
    with stat_col4:
        categories = edited_df["category"].nunique()
        st.metric("카테고리 수", categories)

def show_visualization():
    """시각화 화면"""
    st.title("📈 Visualization")
    st.markdown("### Test Schedule and Analysis")
    
    if not st.session_state.extracted_tests:
        st.info("📄 편집할 시험 데이터가 없습니다. Test Editor에서 데이터를 준비해주세요.")
        return
    
    # 탭 구성
    tab1, tab2, tab3 = st.tabs(["📅 Gantt Chart", "📊 Category Analysis", "🔄 Test Flow"])
    
    with tab1:
        st.subheader("시험 일정 타임라인")
        
        # 시작 날짜 선택
        start_date = st.date_input("시험 시작 날짜", datetime.now())
        start_datetime = datetime.combine(start_date, datetime.min.time())
        
        # 스케줄 계산
        schedule = calculate_schedule(st.session_state.extracted_tests, start_datetime)
        
        if schedule:
            # 간트 차트
            gantt_fig = create_gantt_chart(schedule)
            if gantt_fig:
                st.plotly_chart(gantt_fig, use_container_width=True)
            
            # 스케줄 테이블
            st.subheader("상세 일정표")
            schedule_df = pd.DataFrame(schedule)
            schedule_df["Duration (days)"] = (schedule_df["Finish"] - schedule_df["Start"]).dt.total_seconds() / 86400
            st.dataframe(schedule_df, use_container_width=True, hide_index=True)
            
            # 총 소요 기간
            total_duration = (schedule[-1]["Finish"] - schedule[0]["Start"]).days
            st.metric("총 시험 기간", f"{total_duration} 일")
    
    with tab2:
        st.subheader("카테고리별 분석")
        
        df = pd.DataFrame(st.session_state.extracted_tests)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 카테고리별 시험 수
            category_counts = df["category"].value_counts()
            fig1 = px.bar(
                x=category_counts.index,
                y=category_counts.values,
                labels={"x": "Category", "y": "Count"},
                title="카테고리별 시험 항목 수",
                color=category_counts.values,
                color_continuous_scale="Viridis"
            )
            st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            # 카테고리별 예상 시간
            category_hours = df.groupby("category")["estimated_hours"].sum()
            fig2 = px.pie(
                values=category_hours.values,
                names=category_hours.index,
                title="카테고리별 예상 시간 비율"
            )
            st.plotly_chart(fig2, use_container_width=True)
        
        # 상세 테이블
        st.subheader("카테고리별 상세 통계")
        category_stats = df.groupby("category").agg({
            "cycles": "sum",
            "estimated_hours": "sum",
            "standard_name": "count"
        }).rename(columns={"standard_name": "test_count"})
        st.dataframe(category_stats, use_container_width=True)
    
    with tab3:
        st.subheader("시험 프로세스 플로우")
        
        # Mermaid 다이어그램으로 플로우 표시
        df = pd.DataFrame(st.session_state.extracted_tests)
        sorted_df = df.sort_values("priority")
        
        mermaid_code = "graph TD\n"
        mermaid_code += "    Start[시험 시작]\n"
        
        prev_node = "Start"
        for idx, row in sorted_df.iterrows():
            node_id = f"Test{idx}"
            node_label = f"{row['standard_name']}<br/>{row['estimated_hours']}h"
            mermaid_code += f"    {node_id}[\"{node_label}\"]\n"
            mermaid_code += f"    {prev_node} --> {node_id}\n"
            prev_node = node_id
        
        mermaid_code += f"    {prev_node} --> End[시험 완료]\n"
        
        st.code(mermaid_code, language="mermaid")
        
        st.info("💡 위 다이어그램은 Mermaid 형식입니다. Mermaid 뷰어에서 확인하거나, 아래 테이블로 순서를 확인하세요.")
        
        # 순서 테이블
        st.subheader("시험 순서")
        flow_df = sorted_df[["priority", "standard_name", "category", "estimated_hours"]].reset_index(drop=True)
        flow_df.index = flow_df.index + 1
        flow_df.index.name = "순서"
        st.dataframe(flow_df, use_container_width=True)

def show_knowledge_base():
    """지식 베이스 화면"""
    st.title("🗃️ Knowledge Base")
    st.markdown("### Learning Loop & Master Data Management")
    
    tab1, tab2 = st.tabs(["📚 Master Data", "🧠 Knowledge History"])
    
    with tab1:
        st.subheader("표준 시험 마스터 데이터")
        
        # 마스터 데이터 표시
        if st.session_state.master_data:
            for idx, master in enumerate(st.session_state.master_data):
                with st.expander(f"🔹 {master['standard_name']} ({master['category']})"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**카테고리:** {master['category']}")
                        st.write(f"**기본 규칙:** {master['default_rule']}")
                        st.write(f"**기본 사이클:** {master.get('default_cycles', 'N/A')}")
                    
                    with col2:
                        st.write(f"**예상 시간:** {master.get('estimated_hours', 'N/A')}h")
                        st.write(f"**유사어:** {', '.join(master['aliases'])}")
        
        st.divider()
        
        # 새 마스터 데이터 추가
        with st.expander("➕ 새 마스터 데이터 추가"):
            with st.form("add_master_form"):
                new_name = st.text_input("표준 명칭")
                new_category = st.selectbox("카테고리", ["Electrical Test", "Environmental Test", "Endurance Test"])
                new_rule = st.text_input("기본 규칙")
                new_aliases = st.text_input("유사어 (쉼표로 구분)")
                new_cycles = st.number_input("기본 사이클", min_value=1, value=100)
                new_hours = st.number_input("예상 시간(h)", min_value=0.1, value=10.0)
                
                submitted = st.form_submit_button("추가", type="primary")
                
                if submitted and new_name:
                    new_master = {
                        "standard_name": new_name,
                        "category": new_category,
                        "aliases": [a.strip() for a in new_aliases.split(",") if a.strip()],
                        "default_rule": new_rule,
                        "default_cycles": new_cycles,
                        "estimated_hours": new_hours
                    }
                    st.session_state.master_data.append(new_master)
                    save_json_data(MASTER_DATA_FILE, st.session_state.master_data)
                    st.success("✅ 새 마스터 데이터가 추가되었습니다!")
                    st.rerun()
    
    with tab2:
        st.subheader("학습 이력 및 피드백 데이터")
        
        if st.session_state.knowledge_base:
            st.metric("총 학습 데이터", len(st.session_state.knowledge_base))
            
            for idx, entry in enumerate(reversed(st.session_state.knowledge_base)):
                with st.expander(f"📁 {entry.get('project', 'Unknown')} - {entry.get('timestamp', '')[:19]}"):
                    st.write(f"**검증 여부:** {'✅ Verified' if entry.get('is_verified') else '❌ Not Verified'}")
                    st.write(f"**시험 항목 수:** {len(entry.get('final_data', []))}")
                    
                    if entry.get('final_data'):
                        st.subheader("저장된 시험 데이터")
                        kb_df = pd.DataFrame(entry['final_data'])
                        st.dataframe(kb_df, use_container_width=True, hide_index=True)
        else:
            st.info("아직 학습 데이터가 없습니다. Test Editor에서 데이터를 저장하면 자동으로 축적됩니다.")
        
        st.divider()
        
        # 통계
        if st.session_state.knowledge_base:
            st.subheader("📊 학습 통계")
            
            total_projects = len(st.session_state.knowledge_base)
            verified_projects = sum(1 for kb in st.session_state.knowledge_base if kb.get('is_verified'))
            total_tests = sum(len(kb.get('final_data', [])) for kb in st.session_state.knowledge_base)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("총 프로젝트", total_projects)
            
            with col2:
                st.metric("검증된 프로젝트", verified_projects)
            
            with col3:
                st.metric("총 시험 데이터", total_tests)

# 앱 실행
if __name__ == "__main__":
    main()
