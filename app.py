import streamlit as st
import pandas as pd
from datetime import datetime
import os
import json
from modules.database import Database
from modules.llm_processor import LLMProcessor
from modules.scheduler import Scheduler
from modules.utils import Utils

# 페이지 설정
st.set_page_config(
    page_title="RPM - Reliable Planning Manager",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 세션 상태 초기화
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

# 데이터베이스 초기화
@st.cache_resource
def init_database():
    return Database()

db = init_database()

# 유틸리티 초기화
utils = Utils()

# 헤더
st.title("⚙️ RPM - Reliable Planning Manager")
st.markdown("### Blower Motor Test Support System")
st.divider()

# ============================================================================
# 페이지 1: 사용자 선택 화면
# ============================================================================
def page_user_selection():
    st.header("🔐 사용자 선택")
    
    col1, col2 = st.columns([2, 3])
    
    with col1:
        st.subheader("사용자 관리")
        
        # 사용자 목록 불러오기
        users = db.get_all_users()
        user_names = users['user_name'].tolist() if not users.empty else []
        
        # 사용자 선택
        selected_user_name = st.selectbox(
            "사용자 선택",
            options=user_names,
            key="user_selectbox"
        )
        
        if st.button("사용자 선택 확인", type="primary", use_container_width=True):
            if selected_user_name:
                user_data = users[users['user_name'] == selected_user_name].iloc[0]
                st.session_state.selected_user = {
                    'id': user_data['id'],
                    'name': user_data['user_name']
                }
                # 마지막 접속 시간 업데이트
                db.update_user_last_access(user_data['id'])
                st.success(f"✅ {selected_user_name}님 환영합니다!")
        
        st.divider()
        
        # 새 사용자 추가
        with st.expander("➕ 새 사용자 추가"):
            new_user_name = st.text_input("새 사용자 이름")
            if st.button("사용자 추가", use_container_width=True):
                if new_user_name:
                    success = db.add_user(new_user_name)
                    if success:
                        st.success(f"✅ {new_user_name} 추가 완료!")
                        st.rerun()
                    else:
                        st.error("❌ 사용자 추가 실패")
                else:
                    st.warning("⚠️ 사용자 이름을 입력하세요")
    
    with col2:
        if st.session_state.selected_user:
            st.subheader(f"📅 {st.session_state.selected_user['name']}님의 시험 일정")
            
            # 사용자의 시험 일정 표시
            schedule_data = db.get_user_schedule(st.session_state.selected_user['id'])
            
            if not schedule_data.empty:
                st.dataframe(
                    schedule_data,
                    use_container_width=True,
                    height=300
                )
            else:
                st.info("📋 등록된 시험 일정이 없습니다.")
            
            st.divider()
            
            # 의뢰 선택
            st.subheader("📂 기존 의뢰 선택")
            requests = db.get_user_requests(st.session_state.selected_user['id'])
            
            if not requests.empty:
                request_options = [f"{row['id']} - {row['client']} ({row['project']})" 
                                 for _, row in requests.iterrows()]
                selected_request_str = st.selectbox(
                    "의뢰 선택",
                    options=request_options,
                    key="request_selectbox"
                )
                
                col_a, col_b = st.columns(2)
                
                with col_a:
                    if st.button("의뢰 수정", use_container_width=True):
                        request_id = selected_request_str.split(' - ')[0]
                        st.session_state.selected_request = request_id
                        # 기존 의뢰 데이터 불러오기
                        request_data = db.get_request_data(request_id)
                        st.session_state.extracted_data = request_data
                        st.session_state.current_page = 'test_item_data'
                        st.rerun()
                
                with col_b:
                    if st.button("의뢰 일정 보기", use_container_width=True):
                        request_id = selected_request_str.split(' - ')[0]
                        request_schedule = db.get_request_schedule(request_id)
                        if not request_schedule.empty:
                            st.dataframe(request_schedule, use_container_width=True)
                        else:
                            st.info("해당 의뢰의 일정이 없습니다.")
            else:
                st.info("📋 등록된 의뢰가 없습니다.")
            
            st.divider()
            
            # 새 의뢰 버튼
            st.subheader("📤 새 의뢰 생성")
            uploaded_file = st.file_uploader(
                "테스트 스펙 파일 업로드 (PDF, DOCX)",
                type=['pdf', 'docx'],
                key="spec_file_uploader"
            )
            
            if st.button("새 의뢰 생성", type="primary", use_container_width=True):
                if uploaded_file:
                    with st.spinner("📄 파일 분석 중..."):
                        # LLM 처리
                        llm_processor = LLMProcessor(db)
                        extracted_data = llm_processor.process_document(uploaded_file)
                        
                        if extracted_data:
                            st.session_state.extracted_data = extracted_data
                            st.session_state.selected_request = None  # 새 의뢰
                            st.session_state.current_page = 'test_item_data'
                            st.success("✅ 파일 분석 완료!")
                            st.rerun()
                        else:
                            st.error("❌ 파일 분석 실패")
                else:
                    st.warning("⚠️ 파일을 업로드하세요")
        else:
            st.info("👈 왼쪽에서 사용자를 선택하세요")

# ============================================================================
# 페이지 2: 시험 의뢰 항목 데이터 화면
# ============================================================================
def page_test_item_data():
    st.header("📋 시험 의뢰 항목 데이터")
    
    if st.button("← 사용자 선택으로 돌아가기"):
        st.session_state.current_page = 'user_selection'
        st.rerun()
    
    st.divider()
    
    if st.session_state.extracted_data:
        data = st.session_state.extracted_data
        
        # 의뢰 정보 표시
        st.subheader("📌 의뢰 정보")
        col1, col2 = st.columns(2)
        with col1:
            client = st.text_input("발주처", value=data.get('request_info', {}).get('client', ''))
        with col2:
            project = st.text_input("프로젝트명", value=data.get('request_info', {}).get('project', ''))
        
        st.divider()
        
        # 시험 항목 데이터 표시 (Expandable Tree View)
        st.subheader("🔍 추출된 시험 항목")
        
        test_items = data.get('test_items', [])
        
        if test_items:
            # 편집 가능한 데이터로 변환
            edited_items = []
            
            for idx, item in enumerate(test_items):
                with st.expander(f"**{idx+1}. {item.get('test_name', 'Unknown Test')}**"):
                    col_a, col_b = st.columns(2)
                    
                    with col_a:
                        test_name = st.text_input("시험명", value=item.get('test_name', ''), key=f"test_name_{idx}")
                        category = st.text_input("분류", value=item.get('category', ''), key=f"category_{idx}")
                        ref_standard = st.text_input("참조 규격", value=item.get('ref_standard', ''), key=f"ref_standard_{idx}")
                        sample_assembly = st.text_input("시료 구성", value=item.get('sample_assembly', ''), key=f"sample_assembly_{idx}")
                        test_sample_no = st.text_input("샘플 번호", value=item.get('test_sample_no', ''), key=f"test_sample_no_{idx}")
                    
                    with col_b:
                        sample_count = st.text_input("시료 수", value=item.get('sample_count', ''), key=f"sample_count_{idx}")
                        test_duration = st.text_input("소요 일수", value=item.get('test_duration', ''), key=f"test_duration_{idx}")
                        test_instrument = st.text_input("시험 장비", value=item.get('test_instrument', ''), key=f"test_instrument_{idx}")
                        test_master_id = st.text_input("마스터 ID", value=item.get('test_master_id', ''), key=f"test_master_id_{idx}")
                    
                    st.markdown("**특수 조건 (Custom Specs)**")
                    custom_specs = item.get('custom_specs', {})
                    custom_specs_str = st.text_area(
                        "JSON 형식",
                        value=json.dumps(custom_specs, indent=2, ensure_ascii=False),
                        height=150,
                        key=f"custom_specs_{idx}"
                    )
                    
                    # 편집된 데이터 저장
                    edited_item = {
                        'test_name': test_name,
                        'category': category,
                        'ref_standard': ref_standard,
                        'sample_assembly': sample_assembly,
                        'test_sample_no': test_sample_no,
                        'sample_count': sample_count,
                        'test_duration': test_duration,
                        'test_instrument': test_instrument,
                        'test_master_id': test_master_id,
                        'custom_specs': json.loads(custom_specs_str) if custom_specs_str else {}
                    }
                    edited_items.append(edited_item)
            
            # 업데이트된 데이터 저장
            st.session_state.extracted_data['test_items'] = edited_items
            st.session_state.extracted_data['request_info'] = {
                'client': client,
                'project': project
            }
            
            st.divider()
            
            # 버튼
            col_btn1, col_btn2 = st.columns(2)
            
            with col_btn1:
                if st.button("📝 계획서 생성", type="primary", use_container_width=True):
                    # 데이터 저장
                    request_id = db.save_request_data(
                        st.session_state.selected_user['id'],
                        st.session_state.extracted_data,
                        st.session_state.selected_request
                    )
                    
                    if request_id:
                        st.session_state.selected_request = request_id
                        st.success("✅ 데이터 저장 완료!")
                        st.session_state.current_page = 'plan_draft'
                        st.rerun()
                    else:
                        st.error("❌ 데이터 저장 실패")
            
            with col_btn2:
                if st.button("💾 의뢰 데이터 저장", use_container_width=True):
                    request_id = db.save_request_data(
                        st.session_state.selected_user['id'],
                        st.session_state.extracted_data,
                        st.session_state.selected_request
                    )
                    
                    if request_id:
                        st.session_state.selected_request = request_id
                        st.success("✅ 데이터 저장 완료!")
                    else:
                        st.error("❌ 데이터 저장 실패")
        else:
            st.warning("⚠️ 추출된 시험 항목이 없습니다.")
    else:
        st.error("❌ 데이터가 없습니다. 사용자 선택 화면으로 돌아가세요.")

# ============================================================================
# 페이지 3: 계획서 초안 작성 화면
# ============================================================================
def page_plan_draft():
    st.header("📊 계획서 초안 작성")
    
    if st.button("← 시험 항목 데이터로 돌아가기"):
        st.session_state.current_page = 'test_item_data'
        st.rerun()
    
    st.divider()
    
    if st.session_state.extracted_data:
        test_items = st.session_state.extracted_data.get('test_items', [])
        
        if test_items:
            st.subheader("📋 계획서 초안")
            
            # 계획서 데이터 생성
            plan_data = []
            for idx, item in enumerate(test_items):
                plan_row = {
                    '포함': True,
                    '순번': idx + 1,
                    '시험명': item.get('test_name', ''),
                    '분류': item.get('category', ''),
                    '참조규격': item.get('ref_standard', ''),
                    '시료구성': item.get('sample_assembly', ''),
                    '시료수': item.get('sample_count', ''),
                    '소요일수': item.get('test_duration', ''),
                    '시험장비': item.get('test_instrument', ''),
                    '특수조건': json.dumps(item.get('custom_specs', {}), ensure_ascii=False)
                }
                plan_data.append(plan_row)
            
            # 데이터프레임으로 변환
            df_plan = pd.DataFrame(plan_data)
            
            # 편집 가능한 데이터 에디터
            edited_df = st.data_editor(
                df_plan,
                use_container_width=True,
                num_rows="dynamic",
                column_config={
                    "포함": st.column_config.CheckboxColumn(
                        "포함",
                        help="계획서에 포함할 항목 선택",
                        default=True,
                    ),
                    "순번": st.column_config.NumberColumn(
                        "순번",
                        help="시험 순서",
                        min_value=1,
                        step=1,
                    ),
                },
                hide_index=True,
                key="plan_editor"
            )
            
            st.session_state.plan_data = edited_df
            
            st.divider()
            
            # 버튼
            col_btn1, col_btn2 = st.columns(2)
            
            with col_btn1:
                if st.button("💾 계획서 저장 (Excel)", type="primary", use_container_width=True):
                    # 포함된 항목만 필터링
                    final_plan = edited_df[edited_df['포함'] == True].copy()
                    final_plan = final_plan.drop(columns=['포함'])
                    
                    # Excel 파일로 저장
                    excel_file = utils.save_plan_to_excel(
                        final_plan,
                        st.session_state.extracted_data['request_info']
                    )
                    
                    if excel_file:
                        st.download_button(
                            label="📥 계획서 다운로드",
                            data=excel_file,
                            file_name=f"Test_Plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                        st.success("✅ 계획서 저장 완료!")
                    else:
                        st.error("❌ 계획서 저장 실패")
            
            with col_btn2:
                if st.button("📅 일정 생성", use_container_width=True):
                    st.session_state.current_page = 'schedule_management'
                    st.rerun()
        else:
            st.warning("⚠️ 시험 항목이 없습니다.")
    else:
        st.error("❌ 데이터가 없습니다.")

# ============================================================================
# 페이지 4: 시험 일정 관리 화면
# ============================================================================
def page_schedule_management():
    st.header("📅 시험 일정 관리")
    
    if st.button("← 계획서 초안으로 돌아가기"):
        st.session_state.current_page = 'plan_draft'
        st.rerun()
    
    st.divider()
    
    if st.session_state.plan_data is not None:
        # 포함된 항목만 필터링
        included_items = st.session_state.plan_data[st.session_state.plan_data['포함'] == True].copy()
        
        if not included_items.empty:
            st.subheader("📊 Gantt Chart (타임라인)")
            
            # 스케줄러 초기화
            scheduler = Scheduler()
            
            # 시작일 선택
            start_date = st.date_input(
                "시험 시작일 (Day 0)",
                value=datetime.now().date(),
                key="start_date_input"
            )
            
            # Gantt Chart 생성
            gantt_fig = scheduler.create_gantt_chart(included_items, start_date)
            
            if gantt_fig:
                st.plotly_chart(gantt_fig, use_container_width=True)
            else:
                st.warning("⚠️ Gantt Chart 생성 실패")
            
            st.divider()
            
            # 일정 테이블
            st.subheader("📋 상세 일정")
            schedule_df = scheduler.create_schedule_table(included_items, start_date)
            
            if schedule_df is not None:
                st.dataframe(schedule_df, use_container_width=True)
            
            st.divider()
            
            # 일정 저장 버튼
            if st.button("💾 타임라인 저장", type="primary", use_container_width=True):
                success = db.save_schedule(
                    st.session_state.selected_request,
                    st.session_state.selected_user['id'],
                    schedule_df
                )
                
                if success:
                    st.success("✅ 일정 저장 완료!")
                    st.balloons()
                else:
                    st.error("❌ 일정 저장 실패")
        else:
            st.warning("⚠️ 포함된 시험 항목이 없습니다.")
    else:
        st.error("❌ 계획서 데이터가 없습니다.")

# ============================================================================
# 메인 라우팅
# ============================================================================
def main():
    # 사이드바
    with st.sidebar:
        st.image("https://via.placeholder.com/200x80/FF4B4B/FFFFFF?text=RPM", use_container_width=True)
        st.markdown("---")
        
        if st.session_state.selected_user:
            st.success(f"👤 {st.session_state.selected_user['name']}")
            if st.button("🚪 로그아웃", use_container_width=True):
                st.session_state.selected_user = None
                st.session_state.current_page = 'user_selection'
                st.rerun()
        
        st.markdown("---")
        st.markdown("### 📍 현재 페이지")
        page_names = {
            'user_selection': '🔐 사용자 선택',
            'test_item_data': '📋 시험 항목 데이터',
            'plan_draft': '📊 계획서 초안',
            'schedule_management': '📅 일정 관리'
        }
        st.info(page_names.get(st.session_state.current_page, '알 수 없음'))
        
        st.markdown("---")
        st.markdown("### 📚 통계")
        stats = db.get_statistics()
        st.metric("전체 사용자", stats.get('total_users', 0))
        st.metric("전체 의뢰", stats.get('total_requests', 0))
        st.metric("전체 시험 항목", stats.get('total_test_items', 0))
    
    # 페이지 라우팅
    if st.session_state.current_page == 'user_selection':
        page_user_selection()
    elif st.session_state.current_page == 'test_item_data':
        page_test_item_data()
    elif st.session_state.current_page == 'plan_draft':
        page_plan_draft()
    elif st.session_state.current_page == 'schedule_management':
        page_schedule_management()

if __name__ == "__main__":
    main()
