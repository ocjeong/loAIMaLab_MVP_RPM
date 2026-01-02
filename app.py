import streamlit as st
import json
from datetime import datetime
from modules.document_parser import DocumentParser
from modules.database import Database
from modules.scheduler import Scheduler
from modules.utils import initialize_session_state, display_session_info

# 페이지 설정
st.set_page_config(
    page_title="RPM - Reliable Planning Manager",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 세션 상태 초기화
initialize_session_state()

# 데이터베이스 초기화
@st.cache_resource
def get_database():
    return Database()

db = get_database()

# 문서 파서 초기화
@st.cache_resource
def get_parser():
    return DocumentParser()

parser = get_parser()

# 스케줄러 초기화
scheduler = Scheduler(db)

# 사이드바 - 네비게이션
with st.sidebar:
    st.title("🔧 RPM")
    st.markdown("**Reliable Planning Manager**")
    st.markdown("---")
    
    page = st.radio(
        "메뉴",
        ["사용자 선택", "시험 의뢰 항목 데이터", "계획서 초안 작성", "시험 일정 관리"],
        key="navigation"
    )
    
    st.markdown("---")
    st.markdown("### 시스템 정보")
    st.info("Blower Motor Test Support System")

# ============================================
# 페이지 1: 사용자 선택 화면
# ============================================
if page == "사용자 선택":
    st.title("👤 사용자 선택")
    
    # 5.1.1. 사용자 선택 메뉴
    users = db.get_all_users()
    if not users:
        st.warning("등록된 사용자가 없습니다. 새 사용자를 추가하세요.")
        with st.expander("➕ 새 사용자 추가"):
            new_user_name = st.text_input("사용자 이름")
            new_user_email = st.text_input("이메일")
            if st.button("사용자 추가"):
                if new_user_name and new_user_email:
                    db.add_user(new_user_name, new_user_email)
                    st.success(f"사용자 '{new_user_name}'이(가) 추가되었습니다.")
                    st.rerun()
                else:
                    st.error("모든 필드를 입력해주세요.")
    else:
        col1, col2 = st.columns([3, 1])
        with col1:
            selected_user = st.selectbox(
                "사용자 선택",
                options=users,
                format_func=lambda x: f"{x['name']} ({x['email']})",
                key="selected_user_dropdown"
            )
        
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("➕ 사용자 추가"):
                st.session_state.show_add_user = True
        
        if selected_user:
            st.session_state.current_user = selected_user
            
            # 사용자 추가 폼
            if st.session_state.get('show_add_user', False):
                with st.expander("➕ 새 사용자 추가", expanded=True):
                    new_user_name = st.text_input("사용자 이름")
                    new_user_email = st.text_input("이메일")
                    col_a, col_b = st.columns(2)
                    with col_a:
                        if st.button("추가"):
                            if new_user_name and new_user_email:
                                db.add_user(new_user_name, new_user_email)
                                st.success(f"사용자 '{new_user_name}'이(가) 추가되었습니다.")
                                st.session_state.show_add_user = False
                                st.rerun()
                            else:
                                st.error("모든 필드를 입력해주세요.")
                    with col_b:
                        if st.button("취소"):
                            st.session_state.show_add_user = False
                            st.rerun()
            
            st.markdown("---")
            
            # 5.1.2. 일정 확인 박스
            st.subheader("📅 시험 일정")
            
            # 월 선택
            selected_month = st.date_input(
                "조회 월 선택",
                value=datetime.now(),
                key="schedule_month"
            )
            
            # 해당 월의 전체 시험 일정 표시
            schedule_data = db.get_user_schedule(
                selected_user['id'], 
                selected_month.year, 
                selected_month.month
            )
            
            if schedule_data:
                st.plotly_chart(
                    scheduler.create_monthly_gantt(schedule_data),
                    use_container_width=True
                )
            else:
                st.info("이번 달에 예정된 시험이 없습니다.")
            
            st.markdown("---")
            
            # 5.1.3. 의뢰 선택 메뉴
            col1, col2 = st.columns([3, 1])
            with col1:
                requests = db.get_user_requests(selected_user['id'])
                if requests:
                    selected_request = st.selectbox(
                        "기존 의뢰 선택",
                        options=[None] + requests,
                        format_func=lambda x: "선택하세요..." if x is None else f"{x['client']} - {x['project']}",
                        key="selected_request_dropdown"
                    )
                    
                    if selected_request:
                        st.session_state.current_request = selected_request
                        
                        # 선택된 의뢰의 일정 표시
                        request_schedule = db.get_request_schedule(selected_request['id'])
                        if request_schedule:
                            st.plotly_chart(
                                scheduler.create_request_gantt(request_schedule),
                                use_container_width=True
                            )
                else:
                    st.info("등록된 의뢰가 없습니다.")
            
            # 5.1.5. 의뢰 수정 버튼
            with col2:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("✏️ 의뢰 수정", disabled=not st.session_state.get('current_request')):
                    st.session_state.navigation = "시험 의뢰 항목 데이터"
                    st.session_state.edit_mode = True
                    st.rerun()
            
            st.markdown("---")
            
            # 5.1.4. 새 의뢰 버튼
            st.subheader("📄 새 의뢰 생성")
            uploaded_file = st.file_uploader(
                "테스트 스펙 파일 업로드",
                type=['pdf', 'docx'],
                help="PDF 또는 DOCX 형식의 테스트 스펙 문서를 업로드하세요."
            )
            
            if uploaded_file:
                if st.button("🚀 새 의뢰 생성", type="primary"):
                    with st.spinner("문서를 분석하고 있습니다..."):
                        try:
                            # 문서 파싱 및 데이터 추출
                            extracted_data = parser.parse_document(uploaded_file, db.get_master_data())
                            
                            # 새 의뢰 생성
                            request_id = db.create_request(
                                user_id=selected_user['id'],
                                extracted_data=extracted_data
                            )
                            
                            st.session_state.current_request = db.get_request_by_id(request_id)
                            st.session_state.extracted_data = extracted_data
                            st.session_state.edit_mode = False
                            st.session_state.navigation = "시험 의뢰 항목 데이터"
                            
                            st.success("문서 분석이 완료되었습니다!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"문서 처리 중 오류가 발생했습니다: {str(e)}")

# ============================================
# 페이지 2: 시험 의뢰 항목 데이터 화면
# ============================================
elif page == "시험 의뢰 항목 데이터":
    if not st.session_state.get('current_user') or not st.session_state.get('current_request'):
        st.warning("먼저 사용자와 의뢰를 선택해주세요.")
        if st.button("사용자 선택으로 이동"):
            st.session_state.navigation = "사용자 선택"
            st.rerun()
    else:
        # 5.2.1. 세션 정보 표시
        display_session_info(st.session_state.current_user, st.session_state.current_request)
        
        st.title("📋 시험 의뢰 항목 데이터")
        
        # 5.2.2. 의뢰 추출 데이터 박스
        st.subheader("추출된 데이터")
        
        # 데이터 로드
        if st.session_state.get('extracted_data'):
            data = st.session_state.extracted_data
        else:
            request = st.session_state.current_request
            data = json.loads(request.get('final_data', request.get('extracted_data', '{}')))
        
        # 의뢰 정보
        with st.expander("📌 의뢰 정보", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                client = st.text_input("발주처", value=data.get('request_info', {}).get('client', ''))
            with col2:
                project = st.text_input("프로젝트명", value=data.get('request_info', {}).get('project', ''))
            
            data['request_info'] = {'client': client, 'project': project}
        
        # 시험 항목 데이터 (Expandable Tree View)
        st.markdown("### 시험 항목")
        test_items = data.get('test_items', [])
        
        for idx, item in enumerate(test_items):
            with st.expander(f"🔬 {item.get('test_name', f'시험 항목 {idx+1}')}"):
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
                    item['test_sample_no'] = st.number_input(
                        "샘플 번호", 
                        value=item.get('test_sample_no', 0),
                        key=f"sample_no_{idx}"
                    )
                    item['sample_count'] = st.number_input(
                        "시료 수", 
                        value=item.get('sample_count', 1),
                        min_value=1,
                        key=f"sample_count_{idx}"
                    )
                    item['test_duration'] = st.number_input(
                        "소요 일수", 
                        value=float(item.get('test_duration', 1.0)),
                        min_value=0.1,
                        key=f"duration_{idx}"
                    )
                    item['test_instrument'] = st.text_input(
                        "시험 기기", 
                        value=item.get('test_instrument', ''),
                        key=f"instrument_{idx}"
                    )
                
                # 마스터 데이터 매칭
                master_id = item.get('test_master_id', '')
                master_data = db.get_master_by_id(master_id) if master_id else None
                
                if master_data:
                    st.success(f"✅ 매칭됨: {master_data['std_name']} ({master_data['std_category']})")
                else:
                    st.warning("⚠️ 마스터 데이터 미매칭")
                
                # Custom Specs
                st.markdown("**특수 요구사항**")
                custom_specs = item.get('custom_specs', {})
                
                custom_specs_str = st.text_area(
                    "Custom Specs (JSON)",
                    value=json.dumps(custom_specs, indent=2, ensure_ascii=False),
                    height=150,
                    key=f"custom_specs_{idx}"
                )
                
                try:
                    item['custom_specs'] = json.loads(custom_specs_str)
                except:
                    st.error("올바른 JSON 형식이 아닙니다.")
                
                # 삭제 버튼
                if st.button(f"🗑️ 이 항목 삭제", key=f"delete_{idx}"):
                    test_items.pop(idx)
                    st.rerun()
        
        # 새 항목 추가
        if st.button("➕ 새 시험 항목 추가"):
            test_items.append({
                "test_name": "",
                "category": "",
                "ref_standard": "",
                "sample_assembly": "",
                "test_sample_no": 0,
                "sample_count": 1,
                "test_duration": 1.0,
                "test_instrument": "",
                "test_master_id": "",
                "custom_specs": {}
            })
            st.rerun()
        
        data['test_items'] = test_items
        st.session_state.extracted_data = data
        
        st.markdown("---")
        
        # 5.2.3. 계획서 생성 버튼 & 5.2.4. 의뢰 데이터 저장 버튼
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            if st.button("📊 계획서 생성", type="primary"):
                # 데이터 저장
                db.update_request_data(
                    st.session_state.current_request['id'],
                    data
                )
                st.success("✅ 데이터가 저장되었습니다.")
                
                # 마스터 데이터 업데이트 (Learning Loop)
                db.update_master_from_request(data)
                
                st.session_state.navigation = "계획서 초안 작성"
                st.rerun()
        
        with col2:
            if st.button("💾 데이터 저장"):
                db.update_request_data(
                    st.session_state.current_request['id'],
                    data
                )
                st.success("✅ 데이터가 저장되었습니다.")

# ============================================
# 페이지 3: 계획서 초안 작성 화면
# ============================================
elif page == "계획서 초안 작성":
    if not st.session_state.get('current_user') or not st.session_state.get('current_request'):
        st.warning("먼저 사용자와 의뢰를 선택해주세요.")
        if st.button("사용자 선택으로 이동"):
            st.session_state.navigation = "사용자 선택"
            st.rerun()
    else:
        # 5.3.1. 세션 정보 표시
        display_session_info(st.session_state.current_user, st.session_state.current_request)
        
        st.title("📝 계획서 초안 작성")
        
        # 5.3.2. 계획서 출력 박스
        request = st.session_state.current_request
        data = json.loads(request.get('final_data', request.get('extracted_data', '{}')))
        
        test_items = data.get('test_items', [])
        
        if not test_items:
            st.warning("시험 항목이 없습니다.")
        else:
            # 계획서 테이블 생성
            st.subheader("계획서 초안")
            
            # 우선순위 정렬 (카테고리별)
            sorted_items = scheduler.sort_by_priority(test_items)
            
            # 데이터프레임으로 표시
            import pandas as pd
            
            plan_data = []
            for idx, item in enumerate(sorted_items):
                master = db.get_master_by_id(item.get('test_master_id', ''))
                
                plan_data.append({
                    '포함': True,
                    '순서': idx + 1,
                    '시험명': item.get('test_name', ''),
                    '표준명': master['std_name'] if master else '-',
                    '분류': item.get('category', ''),
                    '표준분류': master['std_category'] if master else '-',
                    '참조규격': item.get('ref_standard', ''),
                    '시료구성': item.get('sample_assembly', ''),
                    '시료수': item.get('sample_count', 1),
                    '소요일수': item.get('test_duration', 1.0),
                    '시험기기': item.get('test_instrument', ''),
                })
            
            df = pd.DataFrame(plan_data)
            
            # 편집 가능한 데이터 에디터
            edited_df = st.data_editor(
                df,
                use_container_width=True,
                num_rows="dynamic",
                column_config={
                    "포함": st.column_config.CheckboxColumn(
                        "포함",
                        help="계획서에 포함할지 선택",
                        default=True,
                    ),
                    "순서": st.column_config.NumberColumn(
                        "순서",
                        help="시험 순서",
                        min_value=1,
                        step=1,
                    ),
                    "소요일수": st.column_config.NumberColumn(
                        "소요일수",
                        help="예상 소요 일수",
                        min_value=0.1,
                        format="%.1f",
                    ),
                },
                hide_index=True,
            )
            
            st.session_state.plan_dataframe = edited_df
            
            # 통계 정보
            st.markdown("---")
            col1, col2, col3 = st.columns(3)
            
            included_items = edited_df[edited_df['포함'] == True]
            
            with col1:
                st.metric("총 시험 항목", len(included_items))
            with col2:
                st.metric("총 예상 소요일", f"{included_items['소요일수'].sum():.1f}일")
            with col3:
                st.metric("총 시료 수", included_items['시료수'].sum())
        
        st.markdown("---")
        
        # 5.3.3. 계획서 저장 버튼 & 5.3.4. 일정 생성 버튼
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            if st.button("💾 Excel 저장", type="secondary"):
                try:
                    # Excel 파일 생성
                    excel_file = scheduler.create_excel_plan(
                        edited_df,
                        st.session_state.current_request
                    )
                    
                    st.download_button(
                        label="📥 계획서 다운로드",
                        data=excel_file,
                        file_name=f"test_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                    st.success("✅ 계획서가 생성되었습니다.")
                except Exception as e:
                    st.error(f"Excel 생성 중 오류: {str(e)}")
        
        with col2:
            if st.button("📅 일정 생성", type="primary"):
                st.session_state.navigation = "시험 일정 관리"
                st.rerun()

# ============================================
# 페이지 4: 시험 일정 관리 화면
# ============================================
elif page == "시험 일정 관리":
    if not st.session_state.get('current_user') or not st.session_state.get('current_request'):
        st.warning("먼저 사용자와 의뢰를 선택해주세요.")
        if st.button("사용자 선택으로 이동"):
            st.session_state.navigation = "사용자 선택"
            st.rerun()
    else:
        # 5.4.1. 세션 정보 표시
        display_session_info(st.session_state.current_user, st.session_state.current_request)
        
        st.title("📅 시험 일정 관리")
        
        # 5.4.2. 타임라인(d-day) 확인 박스
        st.subheader("Gantt Chart (D-Day 기준)")
        
        # 계획서 데이터 가져오기
        if st.session_state.get('plan_dataframe') is not None:
            df = st.session_state.plan_dataframe
            included_items = df[df['포함'] == True].copy()
            
            if len(included_items) > 0:
                # 시작일 설정
                col1, col2 = st.columns([1, 3])
                with col1:
                    start_date = st.date_input(
                        "시험 시작일",
                        value=datetime.now(),
                        key="test_start_date"
                    )
                
                # Gantt Chart 생성
                gantt_fig = scheduler.create_dday_gantt(included_items, start_date)
                st.plotly_chart(gantt_fig, use_container_width=True)
                
                # 일정 요약
                st.markdown("---")
                st.subheader("📊 일정 요약")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("시작일", start_date.strftime("%Y-%m-%d"))
                with col2:
                    total_days = included_items['소요일수'].sum()
                    st.metric("총 소요일", f"{total_days:.1f}일")
                with col3:
                    from datetime import timedelta
                    end_date = start_date + timedelta(days=total_days)
                    st.metric("종료 예정일", end_date.strftime("%Y-%m-%d"))
                with col4:
                    st.metric("시험 항목 수", len(included_items))
                
                # 5.4.3. 타임라인(d-day) 저장 버튼
                st.markdown("---")
                
                col1, col2, col3 = st.columns([1, 1, 2])
                
                with col1:
                    if st.button("💾 일정 저장", type="primary"):
                        try:
                            # 일정 데이터 저장
                            schedule_data = scheduler.prepare_schedule_data(
                                included_items,
                                start_date,
                                st.session_state.current_request['id']
                            )
                            
                            db.save_schedule(
                                st.session_state.current_user['id'],
                                st.session_state.current_request['id'],
                                schedule_data
                            )
                            
                            st.success("✅ 일정이 저장되었습니다!")
                            
                            # 검증 완료 표시
                            db.mark_request_verified(st.session_state.current_request['id'])
                            
                        except Exception as e:
                            st.error(f"일정 저장 중 오류: {str(e)}")
                
                with col2:
                    if st.button("🏠 처음으로"):
                        st.session_state.navigation = "사용자 선택"
                        st.session_state.current_request = None
                        st.session_state.extracted_data = None
                        st.session_state.plan_dataframe = None
                        st.rerun()
            else:
                st.warning("포함된 시험 항목이 없습니다.")
        else:
            st.warning("계획서를 먼저 작성해주세요.")
            if st.button("계획서 작성으로 이동"):
                st.session_state.navigation = "계획서 초안 작성"
                st.rerun()

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray;'>
    <p>RPM - Reliable Planning Manager v1.0 | Blower Motor Test Support System</p>
    </div>
    """,
    unsafe_allow_html=True
)
