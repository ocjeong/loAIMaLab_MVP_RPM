import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.figure_factory as ff
from database import Database
from llm_processor import LLMProcessor
from utils import create_gantt_chart, export_to_excel
import json

# 페이지 설정
st.set_page_config(
    page_title="RPM - Reliable Planning Manager",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 세션 상태 초기화
if 'db' not in st.session_state:
    st.session_state.db = Database()
if 'llm' not in st.session_state:
    st.session_state.llm = LLMProcessor()
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'user_selection'
if 'selected_user' not in st.session_state:
    st.session_state.selected_user = None
if 'selected_request' not in st.session_state:
    st.session_state.selected_request = None
if 'extracted_data' not in st.session_state:
    st.session_state.extracted_data = None
if 'plan_data' not in st.session_state:
    st.session_state.plan_data = None

# 스타일링
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2c3e50;
        margin-top: 1rem;
        margin-bottom: 1rem;
    }
    .info-box {
        background-color: #e8f4f8;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin-bottom: 1rem;
    }
    .success-box {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #28a745;
        margin-bottom: 1rem;
    }
    </style>
""", unsafe_allow_html=True)


def user_selection_page():
    """5.1 사용자 선택 화면"""
    st.markdown('<div class="main-header">🔧 RPM - Reliable Planning Manager</div>', unsafe_allow_html=True)
    
    # 5.1.1 사용자 선택 메뉴
    st.markdown('<div class="sub-header">👤 사용자 선택</div>', unsafe_allow_html=True)
    users = st.session_state.db.get_all_users()
    
    col1, col2 = st.columns([3, 1])
    with col1:
        selected_user = st.selectbox(
            "사용자를 선택하세요",
            options=users,
            key="user_selector"
        )
    with col2:
        if st.button("➕ 새 사용자 추가"):
            with st.form("new_user_form"):
                new_user = st.text_input("사용자 이름")
                if st.form_submit_button("추가"):
                    st.session_state.db.add_user(new_user)
                    st.success(f"사용자 '{new_user}' 추가 완료!")
                    st.rerun()
    
    if selected_user:
        st.session_state.selected_user = selected_user
        
        # 5.1.2 일정 확인 박스
        st.markdown('<div class="sub-header">📅 이번 달 시험 일정</div>', unsafe_allow_html=True)
        current_month = datetime.now().strftime("%Y-%m")
        schedule_data = st.session_state.db.get_user_schedule(selected_user, current_month)
        
        if schedule_data:
            fig = create_gantt_chart(schedule_data, title=f"{selected_user}의 전체 시험 일정")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("📋 등록된 시험 일정이 없습니다.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 5.1.3 의뢰 선택 메뉴
            st.markdown('<div class="sub-header">📂 기존 의뢰 선택</div>', unsafe_allow_html=True)
            requests = st.session_state.db.get_user_requests(selected_user)
            
            if requests:
                selected_request = st.selectbox(
                    "의뢰를 선택하세요",
                    options=requests,
                    format_func=lambda x: f"{x['request_id']} - {x['created_at']}"
                )
                
                if selected_request:
                    st.session_state.selected_request = selected_request
                    
                    # 선택된 의뢰의 일정 표시
                    request_schedule = st.session_state.db.get_request_schedule(
                        selected_request['request_id']
                    )
                    if request_schedule:
                        fig = create_gantt_chart(
                            request_schedule, 
                            title=f"의뢰 {selected_request['request_id']} 일정"
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # 5.1.5 의뢰 수정 버튼
                    if st.button("✏️ 의뢰 수정", use_container_width=True):
                        st.session_state.extracted_data = st.session_state.db.get_request_data(
                            selected_request['request_id']
                        )
                        st.session_state.current_page = 'test_data'
                        st.rerun()
            else:
                st.info("📋 등록된 의뢰가 없습니다.")
        
        with col2:
            # 5.1.4 새 의뢰 버튼
            st.markdown('<div class="sub-header">📤 새 의뢰 생성</div>', unsafe_allow_html=True)
            uploaded_file = st.file_uploader(
                "테스트 스펙 파일 업로드",
                type=['pdf', 'docx'],
                help="PDF 또는 DOCX 형식의 테스트 스펙 파일을 업로드하세요"
            )
            
            if uploaded_file:
                if st.button("🚀 새 의뢰 생성", use_container_width=True):
                    with st.spinner("📄 문서 분석 중..."):
                        # LLM을 통한 문서 파싱 및 데이터 추출
                        extracted_data = st.session_state.llm.parse_document(uploaded_file)
                        
                        # 새 의뢰 ID 생성
                        new_request_id = st.session_state.db.create_new_request(
                            selected_user,
                            uploaded_file.name
                        )
                        
                        st.session_state.selected_request = {
                            'request_id': new_request_id,
                            'user': selected_user,
                            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        st.session_state.extracted_data = extracted_data
                        st.session_state.current_page = 'test_data'
                        st.success("✅ 문서 추출 완료!")
                        st.rerun()


def test_data_page():
    """5.2 시험 의뢰 항목 데이터 화면"""
    st.markdown('<div class="main-header">📊 시험 의뢰 항목 데이터</div>', unsafe_allow_html=True)
    
    # 5.2.1 세션 정보 표시
    st.markdown('<div class="info-box">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        st.write(f"**👤 사용자:** {st.session_state.selected_user}")
    with col2:
        st.write(f"**📋 의뢰 ID:** {st.session_state.selected_request['request_id']}")
    with col3:
        if st.button("🔙 돌아가기"):
            st.session_state.current_page = 'user_selection'
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 5.2.2 의뢰 추출 데이터 박스
    st.markdown('<div class="sub-header">🔍 추출된 시험 항목</div>', unsafe_allow_html=True)
    
    if st.session_state.extracted_data:
        # Expandable tree view로 데이터 표시
        for idx, test_item in enumerate(st.session_state.extracted_data):
            with st.expander(f"🧪 {test_item.get('test_name', f'시험 항목 {idx+1}')}"):
                # 편집 가능한 폼
                test_item['test_name'] = st.text_input(
                    "시험 명칭",
                    value=test_item.get('test_name', ''),
                    key=f"name_{idx}"
                )
                
                col1, col2 = st.columns(2)
                with col1:
                    test_item['category'] = st.text_input(
                        "시험 분류",
                        value=test_item.get('category', ''),
                        key=f"category_{idx}"
                    )
                    test_item['temperature'] = st.text_input(
                        "온도 조건",
                        value=test_item.get('temperature', ''),
                        key=f"temp_{idx}"
                    )
                    test_item['voltage'] = st.text_input(
                        "전압 조건",
                        value=test_item.get('voltage', ''),
                        key=f"voltage_{idx}"
                    )
                
                with col2:
                    test_item['cycles'] = st.number_input(
                        "사이클 수",
                        value=int(test_item.get('cycles', 0)),
                        key=f"cycles_{idx}"
                    )
                    test_item['duration_hours'] = st.number_input(
                        "예상 소요 시간 (시간)",
                        value=float(test_item.get('duration_hours', 0)),
                        key=f"duration_{idx}"
                    )
                    test_item['standard_id'] = st.text_input(
                        "매칭된 표준 ID",
                        value=test_item.get('standard_id', ''),
                        key=f"standard_{idx}",
                        help="마스터 데이터와 매칭된 표준 ID"
                    )
                
                test_item['notes'] = st.text_area(
                    "비고",
                    value=test_item.get('notes', ''),
                    key=f"notes_{idx}"
                )
    
    st.markdown("---")
    
    # 5.2.3 계획서 생성 버튼 & 5.2.4 의뢰 데이터 저장 버튼
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("📝 계획서 생성", use_container_width=True):
            # 데이터 저장
            st.session_state.db.save_request_data(
                st.session_state.selected_request['request_id'],
                st.session_state.extracted_data
            )
            st.session_state.current_page = 'plan_draft'
            st.success("✅ 데이터 저장 완료!")
            st.rerun()
    
    with col2:
        if st.button("💾 의뢰 데이터 저장", use_container_width=True):
            st.session_state.db.save_request_data(
                st.session_state.selected_request['request_id'],
                st.session_state.extracted_data
            )
            st.success("✅ 데이터 저장 완료!")


def plan_draft_page():
    """5.3 계획서 초안 작성 화면"""
    st.markdown('<div class="main-header">📋 계획서 초안 작성</div>', unsafe_allow_html=True)
    
    # 5.3.1 세션 정보 표시
    st.markdown('<div class="info-box">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        st.write(f"**👤 사용자:** {st.session_state.selected_user}")
    with col2:
        st.write(f"**📋 의뢰 ID:** {st.session_state.selected_request['request_id']}")
    with col3:
        if st.button("🔙 돌아가기"):
            st.session_state.current_page = 'test_data'
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 5.3.2 계획서 출력 박스
    st.markdown('<div class="sub-header">📊 계획서 초안</div>', unsafe_allow_html=True)
    
    # 계획서 데이터 준비
    if st.session_state.plan_data is None:
        plan_data = []
        for idx, item in enumerate(st.session_state.extracted_data):
            plan_data.append({
                'include': True,
                'order': idx + 1,
                'test_name': item.get('test_name', ''),
                'category': item.get('category', ''),
                'temperature': item.get('temperature', ''),
                'voltage': item.get('voltage', ''),
                'cycles': item.get('cycles', 0),
                'duration_hours': item.get('duration_hours', 0),
                'notes': item.get('notes', '')
            })
        st.session_state.plan_data = plan_data
    
    # 편집 가능한 테이블
    edited_data = []
    for idx, item in enumerate(st.session_state.plan_data):
        col_check, col_order, col_name, col_cat, col_temp, col_volt, col_cycles, col_hours = st.columns([0.5, 0.5, 2, 1.5, 1, 1, 1, 1])
        
        with col_check:
            include = st.checkbox("", value=item['include'], key=f"include_{idx}", label_visibility="collapsed")
        with col_order:
            order = st.number_input("", value=item['order'], key=f"order_{idx}", label_visibility="collapsed", min_value=1)
        with col_name:
            test_name = st.text_input("", value=item['test_name'], key=f"plan_name_{idx}", label_visibility="collapsed")
        with col_cat:
            category = st.text_input("", value=item['category'], key=f"plan_cat_{idx}", label_visibility="collapsed")
        with col_temp:
            temperature = st.text_input("", value=item['temperature'], key=f"plan_temp_{idx}", label_visibility="collapsed")
        with col_volt:
            voltage = st.text_input("", value=item['voltage'], key=f"plan_volt_{idx}", label_visibility="collapsed")
        with col_cycles:
            cycles = st.number_input("", value=item['cycles'], key=f"plan_cycles_{idx}", label_visibility="collapsed")
        with col_hours:
            duration = st.number_input("", value=item['duration_hours'], key=f"plan_hours_{idx}", label_visibility="collapsed", format="%.1f")
        
        edited_data.append({
            'include': include,
            'order': order,
            'test_name': test_name,
            'category': category,
            'temperature': temperature,
            'voltage': voltage,
            'cycles': cycles,
            'duration_hours': duration,
            'notes': item['notes']
        })
    
    st.session_state.plan_data = edited_data
    
    # 헤더 표시
    st.markdown("**계획서 테이블**")
    col_check, col_order, col_name, col_cat, col_temp, col_volt, col_cycles, col_hours = st.columns([0.5, 0.5, 2, 1.5, 1, 1, 1, 1])
    col_check.write("**포함**")
    col_order.write("**순서**")
    col_name.write("**시험명**")
    col_cat.write("**분류**")
    col_temp.write("**온도**")
    col_volt.write("**전압**")
    col_cycles.write("**사이클**")
    col_hours.write("**시간(h)**")
    
    st.markdown("---")
    
    # 5.3.3 계획서 저장 버튼 & 5.3.4 일정 생성 버튼
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("💾 계획서 저장 (Excel)", use_container_width=True):
            df = pd.DataFrame([item for item in st.session_state.plan_data if item['include']])
            excel_file = export_to_excel(df, st.session_state.selected_request['request_id'])
            st.download_button(
                label="📥 Excel 다운로드",
                data=excel_file,
                file_name=f"plan_{st.session_state.selected_request['request_id']}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            st.success("✅ 계획서 저장 완료!")
    
    with col2:
        if st.button("📅 일정 생성", use_container_width=True):
            st.session_state.current_page = 'schedule'
            st.rerun()


def schedule_page():
    """5.4 시험 일정 관리 화면"""
    st.markdown('<div class="main-header">📅 시험 일정 관리</div>', unsafe_allow_html=True)
    
    # 5.4.1 세션 정보 표시
    st.markdown('<div class="info-box">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        st.write(f"**👤 사용자:** {st.session_state.selected_user}")
    with col2:
        st.write(f"**📋 의뢰 ID:** {st.session_state.selected_request['request_id']}")
    with col3:
        if st.button("🔙 돌아가기"):
            st.session_state.current_page = 'plan_draft'
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 5.4.2 타임라인(d-day) 확인 박스
    st.markdown('<div class="sub-header">📊 Gantt Chart - 시험 타임라인</div>', unsafe_allow_html=True)
    
    # 시작일 선택
    start_date = st.date_input(
        "시험 시작일 선택",
        value=datetime.now(),
        help="Day 0의 날짜를 선택하세요"
    )
    
    # Gantt Chart 데이터 생성
    included_items = [item for item in st.session_state.plan_data if item['include']]
    included_items.sort(key=lambda x: x['order'])
    
    gantt_data = []
    current_start = start_date
    
    for item in included_items:
        duration_days = item['duration_hours'] / 24
        end_date = current_start + timedelta(days=duration_days)
        
        gantt_data.append({
            'Task': item['test_name'],
            'Start': current_start,
            'Finish': end_date,
            'Category': item['category'],
            'Duration (hours)': item['duration_hours']
        })
        
        current_start = end_date
    
    if gantt_data:
        # Plotly Gantt Chart
        fig = create_gantt_chart(gantt_data, title=f"의뢰 {st.session_state.selected_request['request_id']} - 시험 타임라인")
        st.plotly_chart(fig, use_container_width=True)
        
        # 요약 정보
        total_duration = sum([item['duration_hours'] for item in included_items])
        st.markdown(f"""
        <div class="info-box">
        <strong>📊 일정 요약</strong><br>
        • 총 시험 항목: {len(included_items)}개<br>
        • 총 소요 시간: {total_duration:.1f} 시간 ({total_duration/24:.1f} 일)<br>
        • 시작일: {start_date.strftime('%Y-%m-%d')}<br>
        • 종료 예정일: {current_start.strftime('%Y-%m-%d')}
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 5.4.3 타임라인(d-day) 저장 버튼
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("💾 일정 저장", use_container_width=True):
            # DB에 일정 저장
            st.session_state.db.save_schedule(
                st.session_state.selected_user,
                st.session_state.selected_request['request_id'],
                gantt_data
            )
            st.success("✅ 일정 저장 완료!")
            st.balloons()
    
    with col2:
        if st.button("🏠 홈으로 돌아가기", use_container_width=True):
            st.session_state.current_page = 'user_selection'
            st.session_state.plan_data = None
            st.rerun()


# 메인 라우팅
def main():
    if st.session_state.current_page == 'user_selection':
        user_selection_page()
    elif st.session_state.current_page == 'test_data':
        test_data_page()
    elif st.session_state.current_page == 'plan_draft':
        plan_draft_page()
    elif st.session_state.current_page == 'schedule':
        schedule_page()


if __name__ == "__main__":
    main()
