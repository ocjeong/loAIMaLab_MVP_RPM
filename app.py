import streamlit as st
import pandas as pd
from datetime import datetime
import os
from modules.database import DatabaseManager
from modules.llm_handler import LLMHandler
from modules.standardization import standardize_test_item, get_master_by_id
from modules.scheduler import SchedulerManager
from utils.helpers import init_session_state, save_to_excel

# 페이지 설정
st.set_page_config(
    page_title="RPM - Reliable Planning Manager",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 세션 상태 초기화
init_session_state()

# 데이터베이스 매니저 초기화
@st.cache_resource
def get_db_manager():
    return DatabaseManager()

db = get_db_manager()

# LLM 핸들러 초기화
@st.cache_resource
def get_llm_handler():
    return LLMHandler()

llm = get_llm_handler()

# 스케줄러 매니저 초기화
scheduler = SchedulerManager()

# 사이드바 구성
def render_sidebar():
    with st.sidebar:
        st.title("🔧 RPM System")
        st.markdown("---")
        
        # 현재 세션 정보
        st.subheader("📊 현재 세션 정보")
        if st.session_state.current_user:
            st.info(f"**사용자:** {st.session_state.current_user['user_name']}")
        if st.session_state.current_request:
            st.info(f"**의뢰 ID:** {st.session_state.current_request.get('id', 'N/A')}")
            st.info(f"**발주처:** {st.session_state.current_request.get('client', 'N/A')}")
        
        st.markdown("---")
        
        # Database Export 기능
        st.subheader("💾 Database Export")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📥 Master Test", use_container_width=True):
                master_data = db.load_master_tests()
                csv = master_data.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="다운로드",
                    data=csv,
                    file_name=f"Master_Test_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
            
            if st.button("📥 Request Info", use_container_width=True):
                request_data = db.load_requests()
                csv = request_data.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="다운로드",
                    data=csv,
                    file_name=f"Request_Info_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
        
        with col2:
            if st.button("📥 Test Item", use_container_width=True):
                test_item_data = db.load_test_items()
                csv = test_item_data.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="다운로드",
                    data=csv,
                    file_name=f"Test_Item_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
            
            if st.button("📥 User List", use_container_width=True):
                user_data = db.load_users()
                csv = user_data.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="다운로드",
                    data=csv,
                    file_name=f"User_List_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )

# 화면 1: 사용자 선택 화면
def render_user_selection():
    st.title("👤 사용자 선택 및 의뢰 관리")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("사용자 선택")
        
        # 사용자 목록 로드
        users = db.load_users()
        user_names = users['user_name'].tolist()
        
        selected_user = st.selectbox(
            "사용자를 선택하세요",
            options=user_names,
            key="user_selector"
        )
        
        # 새 사용자 추가
        with st.expander("➕ 새 사용자 추가"):
            new_user_name = st.text_input("사용자 이름")
            if st.button("사용자 추가"):
                if new_user_name:
                    user_id = db.add_user(new_user_name)
                    st.success(f"사용자 '{new_user_name}' 추가 완료! (ID: {user_id})")
                    st.rerun()
                else:
                    st.error("사용자 이름을 입력해주세요.")
        
        # 사용자 선택 시 세션 상태 업데이트
        if selected_user:
            user_data = users[users['user_name'] == selected_user].iloc[0]
            st.session_state.current_user = user_data.to_dict()
            db.update_user_last_access(user_data['id'])
        
        st.markdown("---")
        
        # 의뢰 선택
        st.subheader("기존 의뢰 선택")
        if st.session_state.current_user:
            user_requests = db.get_user_requests(st.session_state.current_user['id'])
            
            if not user_requests.empty:
                request_options = [f"{row['id']} - {row['client']} ({row['project']})" 
                                 for _, row in user_requests.iterrows()]
                
                selected_request = st.selectbox(
                    "의뢰를 선택하세요",
                    options=["선택 안 함"] + request_options,
                    key="request_selector"
                )
                
                if selected_request != "선택 안 함":
                    request_id = selected_request.split(" - ")[0]
                    request_data = user_requests[user_requests['id'] == request_id].iloc[0]
                    st.session_state.current_request = request_data.to_dict()
                    
                    if st.button("📝 의뢰 수정", use_container_width=True):
                        st.session_state.page = "edit_request"
                        st.rerun()
            else:
                st.info("저장된 의뢰가 없습니다.")
    
    with col2:
        st.subheader("📅 일정 확인")
        
        if st.session_state.current_user:
            # 선택된 의뢰가 있으면 해당 의뢰의 일정만, 없으면 전체 일정 표시
            if st.session_state.current_request:
                test_items = db.get_request_test_items(st.session_state.current_request['id'])
                st.info(f"**{st.session_state.current_request['client']}** 의뢰 일정")
            else:
                test_items = db.get_user_all_test_items(st.session_state.current_user['id'])
                st.info("전체 시험 일정")
            
            if not test_items.empty and 'test_duration' in test_items.columns:
                fig = scheduler.create_gantt_chart(test_items)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("표시할 일정이 없습니다.")
        else:
            st.warning("사용자를 선택해주세요.")
    
    # 새 의뢰 버튼
    st.markdown("---")
    if st.button("📤 새 의뢰 시작", type="primary", use_container_width=False):
        if st.session_state.current_user:
            st.session_state.page = "new_request"
            st.rerun()
        else:
            st.error("먼저 사용자를 선택해주세요.")

# 화면 2: 새 의뢰 생성
def render_new_request():
    st.title("📤 새 의뢰 생성")
    
    st.info(f"**사용자:** {st.session_state.current_user['user_name']}")
    
    uploaded_file = st.file_uploader(
        "시험 규격 문서를 업로드하세요",
        type=['pdf', 'docx'],
        help="PDF 또는 DOCX 형식의 파일만 업로드 가능합니다."
    )
    
    if uploaded_file:
        st.success(f"파일 업로드 완료: {uploaded_file.name}")
        
        if st.button("📊 문서 분석 시작", type="primary"):
            with st.spinner("문서를 분석하고 있습니다... (최대 1분 소요)"):
                try:
                    # LLM을 통한 문서 파싱 및 추출
                    extracted_data = llm.extract_test_specifications(uploaded_file)
                    
                    if extracted_data:
                        # 표준화 적용
                        master_data = db.load_master_tests()
                        standardized_items = []
                        
                        for item in extracted_data['test_items']:
                            standardized_item = standardize_test_item(item, master_data)
                            standardized_items.append(standardized_item)
                        
                        # 의뢰 정보 저장
                        request_id = db.create_request(
                            user_id=st.session_state.current_user['id'],
                            client=extracted_data['request_info'].get('client', ''),
                            project=extracted_data['request_info'].get('project', ''),
                            extracted_data=standardized_items
                        )
                        
                        st.session_state.current_request = {
                            'id': request_id,
                            'client': extracted_data['request_info'].get('client', ''),
                            'project': extracted_data['request_info'].get('project', ''),
                            'extracted_data': standardized_items
                        }
                        
                        st.success("✅ 문서 분석 완료!")
                        st.session_state.page = "edit_request"
                        st.rerun()
                    else:
                        st.error("문서에서 데이터를 추출할 수 없습니다.")
                
                except Exception as e:
                    st.error(f"오류 발생: {str(e)}")
    
    if st.button("⬅️ 뒤로 가기"):
        st.session_state.page = "user_selection"
        st.rerun()

# 화면 3: 추출 시험 규격 편집
def render_edit_request():
    st.title("📝 추출 시험 규격 편집")
    
    if not st.session_state.current_request:
        st.error("선택된 의뢰가 없습니다.")
        if st.button("⬅️ 뒤로 가기"):
            st.session_state.page = "user_selection"
            st.rerun()
        return
    
    st.info(f"**의뢰:** {st.session_state.current_request.get('client', 'N/A')} - {st.session_state.current_request.get('project', 'N/A')}")
    
    # 추출된 데이터 로드
    if 'extracted_data' in st.session_state.current_request:
        test_items = st.session_state.current_request['extracted_data']
    else:
        # DB에서 로드
        test_items_df = db.get_request_test_items(st.session_state.current_request['id'])
        test_items = test_items_df.to_dict('records') if not test_items_df.empty else []
    
    st.subheader("📋 의뢰 추출 데이터")
    
    master_data = db.load_master_tests()
    
    # 각 시험 항목을 Expandable Tree View로 표시
    for idx, item in enumerate(test_items):
        # 매칭 상태 아이콘
        if item.get('test_master_id'):
            icon = "✅"
            status = f"[마스터: {item['test_master_id']}]"
            status_color = "green"
        else:
            icon = "⚠️"
            status = "[미매칭]"
            status_color = "orange"
        
        with st.expander(f"{icon} {item.get('test_name', '시험명 없음')} {status}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**원본 추출 데이터**")
                st.text_input("원본 시험명", value=item.get('test_name_original', ''), 
                            key=f"orig_name_{idx}", disabled=True)
                st.text_input("원본 분류", value=item.get('category_original', ''), 
                            key=f"orig_cat_{idx}", disabled=True)
            
            with col2:
                st.markdown("**표준화된 데이터**")
                item['test_name'] = st.text_input("표준 시험명", value=item.get('test_name', ''), 
                                                  key=f"std_name_{idx}")
                item['category'] = st.text_input("표준 분류", value=item.get('category', ''), 
                                                key=f"std_cat_{idx}")
            
            # 마스터 정보 표시
            if item.get('test_master_id'):
                master = get_master_by_id(item['test_master_id'], master_data)
                if master is not None:
                    st.json({
                        "마스터 ID": master['id'],
                        "표준명": master['std_name'],
                        "표준 분류": master['std_category'],
                        "참조 규격": master.get('ref_standard', ''),
                        "유사어": master.get('aliases', [])
                    })
            
            # 편집 가능한 필드들
            st.markdown("---")
            item['ref_standard'] = st.text_input("참조 규격", value=item.get('ref_standard', ''), 
                                                key=f"ref_{idx}")
            item['sample_assembly'] = st.text_input("시료 구성", value=item.get('sample_assembly', ''), 
                                                   key=f"assembly_{idx}")
            item['test_sample_no'] = st.text_input("샘플 번호", value=item.get('test_sample_no', ''), 
                                                  key=f"sample_no_{idx}")
            item['sample_count'] = st.text_input("시료 수", value=item.get('sample_count', ''), 
                                                key=f"count_{idx}")
            item['test_duration'] = st.text_input("시험 기간 (days)", value=item.get('test_duration', ''), 
                                                 key=f"duration_{idx}")
            item['test_equipment'] = st.text_input("시험 장비", value=item.get('test_equipment', ''), 
                                                  key=f"equipment_{idx}")
            
            # test_master_id는 읽기 전용
            st.text_input("마스터 ID (읽기 전용)", value=item.get('test_master_id', ''), 
                         key=f"master_id_{idx}", disabled=True)
            
            # Custom Specs
            if item.get('custom_specs'):
                st.markdown("**특수 조건**")
                st.json(item['custom_specs'])
    
    # 버튼 영역
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("⬅️ 뒤로 가기", use_container_width=True):
            st.session_state.page = "user_selection"
            st.rerun()
    
    with col2:
        if st.button("💾 의뢰 데이터 저장", use_container_width=True):
            # 최종 데이터 저장
            db.update_request_final_data(
                st.session_state.current_request['id'],
                test_items
            )
            
            # 마스터 데이터 업데이트 (유사어 추가)
            for item in test_items:
                if item.get('test_master_id') and item.get('test_name_original'):
                    db.add_alias_to_master(
                        item['test_master_id'],
                        item['test_name_original']
                    )
            
            st.success("✅ 데이터 저장 완료!")
    
    with col3:
        if st.button("📄 계획서 생성", type="primary", use_container_width=True):
            # 최종 데이터 저장
            db.update_request_final_data(
                st.session_state.current_request['id'],
                test_items
            )
            
            st.session_state.current_test_items = test_items
            st.session_state.page = "create_plan"
            st.success("✅ 데이터 저장 완료!")
            st.rerun()

# 화면 4: 계획서 초안 작성
def render_create_plan():
    st.title("📄 계획서 초안 작성")
    
    if not st.session_state.current_test_items:
        st.error("시험 항목 데이터가 없습니다.")
        if st.button("⬅️ 뒤로 가기"):
            st.session_state.page = "edit_request"
            st.rerun()
        return
    
    st.subheader("📊 시험 계획서 출력")
    
    # 시험 항목을 DataFrame으로 변환
    df = pd.DataFrame(st.session_state.current_test_items)
    
    # 그룹별로 섹션 나누기
    categories = df['category'].unique() if 'category' in df.columns else []
    
    edited_items = []
    
    for category in categories:
        st.markdown(f"### {category}")
        category_items = df[df['category'] == category]
        
        # 데이터 편집기
        edited_df = st.data_editor(
            category_items[['test_name', 'ref_standard', 'sample_assembly', 
                          'sample_count', 'test_duration']],
            use_container_width=True,
            num_rows="dynamic",
            key=f"editor_{category}"
        )
        
        edited_items.append(edited_df)
    
    # 샘플 데이터 로드 버튼
    if st.button("🔄 샘플 데이터 로드"):
        st.info("샘플 데이터가 로드되었습니다.")
    
    # 버튼 영역
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("⬅️ 뒤로 가기", use_container_width=True):
            st.session_state.page = "edit_request"
            st.rerun()
    
    with col2:
        if st.button("💾 계획서 저장", use_container_width=True):
            try:
                # 엑셀 파일로 저장
                filename = f"TestPlan_{st.session_state.current_user['user_name']}_{datetime.now().strftime('%Y%m%d')}.xlsx"
                excel_data = save_to_excel(pd.concat(edited_items), 
                                          st.session_state.current_request)
                
                st.download_button(
                    label="📥 엑셀 다운로드",
                    data=excel_data,
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                st.success("✅ 계획서 저장 완료!")
            except Exception as e:
                st.error(f"저장 중 오류 발생: {str(e)}")
    
    with col3:
        if st.button("📅 일정 생성", type="primary", use_container_width=True):
            st.session_state.page = "schedule"
            st.rerun()

# 화면 5: 시험 일정 관리
def render_schedule():
    st.title("📅 시험 일정 관리")
    
    if not st.session_state.current_test_items:
        st.error("시험 항목 데이터가 없습니다.")
        if st.button("⬅️ 뒤로 가기"):
            st.session_state.page = "create_plan"
            st.rerun()
        return
    
    st.subheader("📊 타임라인 (D-day)")
    
    # Gantt Chart 생성
    df = pd.DataFrame(st.session_state.current_test_items)
    
    if 'test_duration' in df.columns:
        fig = scheduler.create_gantt_chart(df, start_day=0)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("시험 기간 정보가 없어 일정을 생성할 수 없습니다.")
    
    # 버튼 영역
    st.markdown("---")
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button("⬅️ 뒤로 가기", use_container_width=True):
            st.session_state.page = "create_plan"
            st.rerun()
    
    with col2:
        if st.button("💾 타임라인 저장", type="primary", use_container_width=True):
            try:
                # 일정을 DB에 저장
                for item in st.session_state.current_test_items:
                    item['request_id'] = st.session_state.current_request['id']
                
                db.save_test_items(st.session_state.current_test_items)
                
                st.success("✅ 일정이 저장되었습니다!")
                
                # 메인 화면으로 이동
                if st.button("🏠 메인으로 돌아가기"):
                    st.session_state.page = "user_selection"
                    st.session_state.current_request = None
                    st.session_state.current_test_items = []
                    st.rerun()
            except Exception as e:
                st.error(f"저장 중 오류 발생: {str(e)}")

# 메인 앱 라우팅
def main():
    render_sidebar()
    
    # 페이지 라우팅
    if st.session_state.page == "user_selection":
        render_user_selection()
    elif st.session_state.page == "new_request":
        render_new_request()
    elif st.session_state.page == "edit_request":
        render_edit_request()
    elif st.session_state.page == "create_plan":
        render_create_plan()
    elif st.session_state.page == "schedule":
        render_schedule()

if __name__ == "__main__":
    main()
