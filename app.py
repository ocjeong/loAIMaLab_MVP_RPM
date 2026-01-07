import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
import plotly.figure_factory as ff
from modules.database import Database
from modules.llm_processor import LLMProcessor
from modules.standardization import standardize_test_item, get_master_by_id
from modules.scheduler import generate_gantt_chart, create_test_plan
from utils.helpers import export_to_excel
import json
import os

# 페이지 설정
st.set_page_config(
    page_title="RPM - Reliable Planning Manager",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 세션 상태 초기화
if 'current_user' not in st.session_state:
    st.session_state.current_user = None
if 'current_request' not in st.session_state:
    st.session_state.current_request = None
if 'page' not in st.session_state:
    st.session_state.page = 'user_selection'
if 'extracted_data' not in st.session_state:
    st.session_state.extracted_data = None
if 'test_plan' not in st.session_state:
    st.session_state.test_plan = None

# 데이터베이스 초기화
db = Database()

# 사이드바
with st.sidebar:
    st.title("🔧 RPM System")
    st.markdown("---")
    
    # 현재 세션 정보
    st.subheader("📊 현재 세션 정보")
    if st.session_state.current_user:
        st.info(f"**사용자:** {st.session_state.current_user['user_name']}")
    else:
        st.warning("사용자를 선택해주세요")
    
    if st.session_state.current_request:
        st.info(f"**의뢰 ID:** {st.session_state.current_request}")
    
    st.markdown("---")
    
    # Database Export 기능
    st.subheader("💾 Database Export")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Master Test", use_container_width=True):
            csv = db.master_test_df.to_csv(index=False)
            st.download_button(
                label="📥 Download",
                data=csv,
                file_name="Master_Test.csv",
                mime="text/csv"
            )
    
    with col2:
        if st.button("User List", use_container_width=True):
            csv = db.user_list_df.to_csv(index=False)
            st.download_button(
                label="📥 Download",
                data=csv,
                file_name="User_List.csv",
                mime="text/csv"
            )
    
    col3, col4 = st.columns(2)
    with col3:
        if st.button("Request Info", use_container_width=True):
            csv = db.request_info_df.to_csv(index=False)
            st.download_button(
                label="📥 Download",
                data=csv,
                file_name="Request_Info.csv",
                mime="text/csv"
            )
    
    with col4:
        if st.button("Test Item", use_container_width=True):
            csv = db.test_item_df.to_csv(index=False)
            st.download_button(
                label="📥 Download",
                data=csv,
                file_name="Test_Item.csv",
                mime="text/csv"
            )
    
    st.markdown("---")
    if st.button("🏠 홈으로", use_container_width=True):
        st.session_state.page = 'user_selection'
        st.rerun()



# ========== 헬퍼 함수 추가 (user_selection_page 함수 위에 추가) ==========

def get_sample_pdf_files():
    """sample 폴더에서 PDF 파일 목록을 가져오는 함수"""
    sample_dir = 'sample'
    
    # sample 폴더가 없으면 생성
    if not os.path.exists(sample_dir):
        os.makedirs(sample_dir)
        return []
    
    # PDF 파일만 필터링
    pdf_files = []
    try:
        for file in os.listdir(sample_dir):
            if file.lower().endswith('.pdf'):
                full_path = os.path.join(sample_dir, file)
                pdf_files.append(full_path)
    except Exception as e:
        print(f"Error reading sample directory: {e}")
        return []
    
    # 파일명 기준으로 정렬
    pdf_files.sort()
    
    return pdf_files

# ========== 페이지 1: 사용자 선택 화면 ==========
def user_selection_page():
    st.title("🔧 RPM - Reliable Planning Manager")
    st.subheader("Blower Motor Test Support System")
    
    st.markdown("---")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("👤 사용자 선택")
        
        # 사용자 목록 불러오기
        user_list = db.get_user_list()
        user_names = user_list['user_name'].tolist()
        
        selected_user_name = st.selectbox(
            "사용자를 선택하세요",
            options=user_names,
            key="user_select"
        )
        
        # 새 사용자 추가
        with st.expander("➕ 새 사용자 추가"):
            new_user_name = st.text_input("사용자 이름")
            if st.button("추가"):
                if new_user_name:
                    db.add_user(new_user_name)
                    st.success(f"'{new_user_name}' 사용자가 추가되었습니다!")
                    st.rerun()
                else:
                    st.error("사용자 이름을 입력해주세요.")
        
        # 사용자 선택 확인
        if st.button("사용자 선택 확인", type="primary", use_container_width=True):
            user_data = user_list[user_list['user_name'] == selected_user_name].iloc[0]
            st.session_state.current_user = user_data.to_dict()
            db.update_last_access(user_data['id'])
            st.success(f"'{selected_user_name}' 선택 완료!")
            st.rerun()
        
        st.markdown("---")
        
        # 의뢰 선택 메뉴
        if st.session_state.current_user:
            st.subheader("📋 기존 의뢰 선택")
            
            user_requests = db.get_user_requests(st.session_state.current_user['id'])
            
            if not user_requests.empty:
                request_options = [f"{row['id']} - {row['client']} ({row['project']})" 
                                   for _, row in user_requests.iterrows()]
                
                selected_request = st.selectbox(
                    "의뢰를 선택하세요",
                    options=request_options,
                    key="request_select"
                )
                
                if st.button("의뢰 수정", use_container_width=True):
                    request_id = selected_request.split(" - ")[0]
                    st.session_state.current_request = request_id
                    
                    # 기존 의뢰 데이터 불러오기 (수정됨)
                    request_data = db.get_request_by_id(request_id)
                    final_data = json.loads(request_data['final_data'])
                    
                    # 데이터 구조 정규화
                    if isinstance(final_data, list):
                        # 리스트인 경우 딕셔너리로 변환
                        st.session_state.extracted_data = {
                            'request_info': {
                                'client': request_data['client'],
                                'project': request_data['project']
                            },
                            'test_items': final_data
                        }
                    else:
                        # 이미 딕셔너리인 경우 그대로 사용
                        st.session_state.extracted_data = final_data
                    
                    st.session_state.page = 'data_edit'
                    st.rerun()
            else:
                st.info("저장된 의뢰가 없습니다.")
        
        st.markdown("---")
        
        # 새 의뢰 버튼
        st.subheader("📄 새 의뢰 생성")
        
        # 탭으로 파일 업로드와 샘플 선택 구분
        tab1, tab2 = st.tabs(["📤 파일 업로드", "📋 샘플 사용"])
        
        with tab1:
            uploaded_file = st.file_uploader(
                "시험 규격 파일 업로드",
                type=['pdf', 'docx'],
                help="PDF 또는 DOCX 형식의 시험 규격 문서를 업로드하세요",
                key="file_uploader"
            )
            
            if uploaded_file:
                if st.button("새 의뢰 생성", type="primary", use_container_width=True, key="upload_btn"):
                    if not st.session_state.current_user:
                        st.error("먼저 사용자를 선택해주세요!")
                    else:
                        with st.spinner("문서 분석 중... 잠시만 기다려주세요."):
                            # LLM 처리
                            llm_processor = LLMProcessor(db)
                            extracted_data = llm_processor.process_document(uploaded_file)
                            
                            if extracted_data:
                                st.session_state.extracted_data = extracted_data
                                st.session_state.page = 'data_edit'
                                st.success("문서 분석 완료!")
                                st.rerun()
                            else:
                                st.error("문서 분석에 실패했습니다.")
        
        with tab2:
            # 샘플 PDF 파일 목록 가져오기
            sample_files = get_sample_pdf_files()
            
            if sample_files:
                st.info(f"📁 {len(sample_files)}개의 샘플 파일이 있습니다.")
                
                # 샘플 파일 선택
                selected_sample = st.selectbox(
                    "샘플 파일 선택",
                    options=sample_files,
                    format_func=lambda x: os.path.basename(x),
                    key="sample_selector"
                )
                
                # 선택된 샘플 파일 정보 표시
                if selected_sample:
                    file_size = os.path.getsize(selected_sample)
                    st.caption(f"📄 파일명: {os.path.basename(selected_sample)}")
                    st.caption(f"💾 크기: {file_size / 1024:.1f} KB")
                
                # 샘플로 의뢰 생성 버튼
                if st.button("샘플로 의뢰 생성", type="primary", use_container_width=True, key="sample_btn"):
                    if not st.session_state.current_user:
                        st.error("먼저 사용자를 선택해주세요!")
                    elif not selected_sample:
                        st.error("샘플 파일을 선택해주세요!")
                    else:
                        with st.spinner("샘플 문서 분석 중... 잠시만 기다려주세요."):
                            # 샘플 파일 읽기
                            with open(selected_sample, 'rb') as f:
                                # BytesIO 객체로 변환하여 업로드 파일처럼 처리
                                from io import BytesIO
                                sample_file_obj = BytesIO(f.read())
                                sample_file_obj.name = os.path.basename(selected_sample)
                                sample_file_obj.type = 'application/pdf'
                                
                                # LLM 처리
                                llm_processor = LLMProcessor(db)
                                extracted_data = llm_processor.process_document_from_bytes(
                                    sample_file_obj.getvalue(), 
                                    'application/pdf'
                                )
                                
                                if extracted_data:
                                    st.session_state.extracted_data = extracted_data
                                    st.session_state.page = 'data_edit'
                                    st.success("샘플 문서 분석 완료!")
                                    st.rerun()
                                else:
                                    st.error("샘플 문서 분석에 실패했습니다.")
            else:
                st.warning("⚠️ 샘플 폴더에 PDF 파일이 없습니다.")
                st.caption("'sample/' 폴더에 PDF 파일을 추가해주세요.")
    
    with col2:
        st.subheader("📅 일정 확인")
        
        if st.session_state.current_user:
            # 사용자의 전체 시험 일정 표시
            user_schedule = db.get_user_schedule(st.session_state.current_user['id'])
            
            if not user_schedule.empty:
                fig = generate_gantt_chart(user_schedule)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("등록된 시험 일정이 없습니다.")
        else:
            st.warning("사용자를 선택하면 일정을 확인할 수 있습니다.")


# ========== 페이지 2: 추출 시험 규격 편집 화면 ==========
def data_edit_page():
    st.title("📝 시험 규격 데이터 편집")
    
    if not st.session_state.extracted_data:
        st.error("추출된 데이터가 없습니다.")
        if st.button("🏠 홈으로 돌아가기"):
            st.session_state.page = 'user_selection'
            st.rerun()
        return
    
    data = st.session_state.extracted_data
    
    # 데이터 구조 검증 및 정규화 (추가됨)
    if isinstance(data, list):
        # 리스트만 있는 경우 (하위 호환성)
        data = {
            'request_info': {'client': '', 'project': ''},
            'test_items': data
        }
        st.session_state.extracted_data = data
    
    # 의뢰 정보 표시
    st.subheader("📋 의뢰 정보")
    col1, col2 = st.columns(2)
    with col1:
        client = st.text_input(
            "발주처", 
            value=data.get('request_info', {}).get('client', ''),
            key="edit_client"
        )
    with col2:
        project = st.text_input(
            "프로젝트", 
            value=data.get('request_info', {}).get('project', ''),
            key="edit_project"
        )
    
    st.markdown("---")
    
    # 시험 항목 표시
    st.subheader("🔬 시험 항목 데이터")
    
    test_items = data.get('test_items', [])
    
    if not test_items:
        st.warning("시험 항목이 없습니다.")
        if st.button("🏠 홈으로 돌아가기"):
            st.session_state.page = 'user_selection'
            st.rerun()
        return
    
    # 표준화 적용
    standardized_items = []
    for item in test_items:
        standardized_item = standardize_test_item(item, db)
        standardized_items.append(standardized_item)
    
    # Expandable tree view
    for idx, item in enumerate(standardized_items):
        # 매칭 상태 표시
        if item.get('test_master_id'):
            master = get_master_by_id(item['test_master_id'], db)
            icon = "✅"
            status = f"[마스터: {item['test_master_id']}]"
            status_color = "green"
        else:
            icon = "⚠️"
            status = "[미매칭]"
            status_color = "orange"
        
        with st.expander(f"{icon} {item.get('test_name', 'Unknown Test')} {status}"):
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
                master = get_master_by_id(item['test_master_id'], db)
                if master:
                    with st.container():
                        st.markdown("**📌 매칭된 마스터 정보**")
                        master_info = {
                            "Master ID": master['id'],
                            "표준명": master['std_name'],
                            "표준 분류": master['std_category'],
                            "참조 규격": master['ref_standard'],
                            "유사어": ", ".join(eval(master['aliases']) if isinstance(master['aliases'], str) else master['aliases'])
                        }
                        st.json(master_info)
            
            st.markdown("---")
            
            # 나머지 필드 편집
            col3, col4 = st.columns(2)
            with col3:
                item['ref_standard'] = st.text_input("참조 규격", value=item.get('ref_standard', ''), 
                                                     key=f"ref_{idx}")
                item['sample_assembly'] = st.text_input("시료 구성", value=item.get('sample_assembly', ''), 
                                                        key=f"assembly_{idx}")
                item['test_sample_no'] = st.text_input("샘플 번호", value=item.get('test_sample_no', ''), 
                                                       key=f"sample_no_{idx}")
                item['sample_count'] = st.text_input("시료 수", value=item.get('sample_count', ''), 
                                                     key=f"count_{idx}")
            
            with col4:
                item['test_duration'] = st.text_input("시험 기간 (days)", value=item.get('test_duration', ''), 
                                                      key=f"duration_{idx}")
                item['test_equipment'] = st.text_input("시험 기기", value=item.get('test_equipment', ''), 
                                                       key=f"equipment_{idx}")
                
                # test_master_id는 읽기 전용
                st.text_input("마스터 ID (읽기 전용)", value=item.get('test_master_id', ''), 
                             key=f"master_id_{idx}", disabled=True)
            
            # custom_specs 편집
            st.markdown("**🔧 특수 조건 (Custom Specs)**")
            custom_specs = item.get('custom_specs', {})
            if not isinstance(custom_specs, dict):
                custom_specs = {}
            
            custom_specs_json = st.text_area(
                "JSON 형식으로 입력",
                value=json.dumps(custom_specs, indent=2, ensure_ascii=False),
                height=150,
                key=f"custom_{idx}"
            )
            try:
                item['custom_specs'] = json.loads(custom_specs_json)
            except:
                st.error("JSON 형식이 올바르지 않습니다.")
    
    st.markdown("---")
    
    # 버튼
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📄 계획서 생성", type="primary", use_container_width=True):
            # 데이터 저장
            request_id = db.save_request(
                user_id=st.session_state.current_user['id'],
                client=client,
                project=project,
                extracted_data=test_items,
                final_data=standardized_items
            )
            st.session_state.current_request = request_id
            
            # 마스터 업데이트
            for item in standardized_items:
                if item.get('test_master_id') and item.get('test_name_original'):
                    db.update_master_aliases(item['test_master_id'], item['test_name_original'])
                elif not item.get('test_master_id'):
                    db.add_new_master(item)
            
            st.session_state.page = 'test_plan'
            st.success("✅ 데이터가 저장되었습니다!")
            st.rerun()
    
    with col2:
        if st.button("💾 의뢰 데이터 저장", use_container_width=True):
            # 데이터 저장
            request_id = db.save_request(
                user_id=st.session_state.current_user['id'],
                client=client,
                project=project,
                extracted_data=test_items,
                final_data=standardized_items
            )
            st.session_state.current_request = request_id
            
            # 마스터 업데이트
            for item in standardized_items:
                if item.get('test_master_id') and item.get('test_name_original'):
                    db.update_master_aliases(item['test_master_id'], item['test_name_original'])
                elif not item.get('test_master_id'):
                    db.add_new_master(item)
            
            st.success("✅ 데이터가 저장되었습니다!")

# ========== 페이지 3: 계획서 초안 작성 화면 ==========
def test_plan_page():
    st.title("📋 시험 계획서 초안")
    
    if not st.session_state.current_request:
        st.error("의뢰 정보가 없습니다.")
        return
    
    # 저장된 데이터 불러오기
    request_data = db.get_request_by_id(st.session_state.current_request)
    test_items = json.loads(request_data['final_data'])
    
    # 계획서 생성
    plan_df = create_test_plan(test_items)
    
    st.subheader("📊 시험 계획서")
    
    # 편집 가능한 데이터프레임
    edited_df = st.data_editor(
        plan_df,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "포함": st.column_config.CheckboxColumn("포함", default=True),
            "시험명": st.column_config.TextColumn("시험명", width="medium"),
            "분류": st.column_config.TextColumn("분류", width="medium"),
            "참조규격": st.column_config.TextColumn("참조규격", width="small"),
            "시료구성": st.column_config.TextColumn("시료구성", width="small"),
            "시료수": st.column_config.TextColumn("시료수", width="small"),
            "시험기간": st.column_config.TextColumn("시험기간(days)", width="small"),
            "시험기기": st.column_config.TextColumn("시험기기", width="medium"),
        }
    )
    
    st.session_state.test_plan = edited_df
    
    st.markdown("---")
    
    # 버튼
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("💾 계획서 저장 (Excel)", type="primary", use_container_width=True):
            excel_data = export_to_excel(edited_df, request_data)
            st.download_button(
                label="📥 Excel 다운로드",
                data=excel_data,
                file_name=f"Test_Plan_{st.session_state.current_request}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            st.success("✅ 계획서가 생성되었습니다!")
    
    with col2:
        if st.button("📅 일정 생성", use_container_width=True):
            st.session_state.page = 'schedule'
            st.rerun()


# ========== 페이지 4: 시험 일정 관리 화면 ==========
def schedule_page():
    st.title("📅 시험 일정 관리")
    
    if st.session_state.test_plan is None:
        st.error("계획서 데이터가 없습니다.")
        return
    
    # 포함된 항목만 필터링
    included_items = st.session_state.test_plan[st.session_state.test_plan['포함'] == True]
    
    st.subheader("📊 타임라인 (D-Day)")
    
    # 시작일 설정
    start_date = st.date_input("시험 시작일", value=datetime.now())
    
    # Gantt 차트 생성
    schedule_data = []
    current_day = 0
    
    for idx, row in included_items.iterrows():
        try:
            duration = int(row['시험기간']) if row['시험기간'] else 1
        except:
            duration = 1
        
        schedule_data.append({
            'Task': row['시험명'],
            'Start': current_day,
            'Finish': current_day + duration,
            'Duration': duration
        })
        current_day += duration
    
    if schedule_data:
        # Plotly Gantt 차트
        df_schedule = pd.DataFrame(schedule_data)
        
        fig = px.timeline(
            df_schedule,
            x_start='Start',
            x_end='Finish',
            y='Task',
            title='시험 일정 타임라인',
            labels={'Start': 'Day', 'Task': '시험 항목'}
        )
        
        fig.update_yaxes(categoryorder='total ascending')
        fig.update_layout(height=max(400, len(schedule_data) * 40))
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 일정 요약
        st.subheader("📋 일정 요약")
        st.info(f"**총 시험 기간:** {current_day} days")
        
        st.dataframe(df_schedule, use_container_width=True)
    
    st.markdown("---")
    
    # 저장 버튼
    if st.button("💾 타임라인 저장", type="primary", use_container_width=True):
        # 일정 데이터를 DB에 저장
        for item in schedule_data:
            db.save_schedule(
                user_id=st.session_state.current_user['id'],
                request_id=st.session_state.current_request,
                test_name=item['Task'],
                start_day=item['Start'],
                duration=item['Duration'],
                start_date=start_date
            )
        
        st.success("✅ 일정이 저장되었습니다!")
        
        if st.button("🏠 홈으로 돌아가기"):
            st.session_state.page = 'user_selection'
            st.rerun()


# ========== 메인 라우팅 ==========
def main():
    if st.session_state.page == 'user_selection':
        user_selection_page()
    elif st.session_state.page == 'data_edit':
        data_edit_page()
    elif st.session_state.page == 'test_plan':
        test_plan_page()
    elif st.session_state.page == 'schedule':
        schedule_page()


if __name__ == "__main__":
    main()



