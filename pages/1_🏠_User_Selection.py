import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from modules.data_manager import DataManager
from modules.llm_parser import LLMParser
from modules.standardizer import Standardizer

st.set_page_config(page_title="User Selection", page_icon="🏠", layout="wide")

# 데이터 매니저 초기화
dm = DataManager()

st.title("🏠 사용자 선택 및 의뢰 관리")

# 사용자 선택 섹션
st.header("👤 사용자 선택")

col1, col2 = st.columns([3, 1])

with col1:
    # 사용자 목록 로드
    users_df = dm.load_user_list()
    user_names = users_df['user_name'].tolist()
    
    if user_names:
        selected_user_name = st.selectbox(
            "사용자를 선택하세요",
            user_names,
            key="user_select"
        )
        
        # 선택된 사용자 정보 저장
        selected_user = users_df[users_df['user_name'] == selected_user_name].iloc[0]
        st.session_state.current_user = selected_user.to_dict()
        
        # 마지막 접속 시간 업데이트
        dm.update_last_access(selected_user['id'])
        
        st.success(f"✅ {selected_user_name}님, 환영합니다!")
    else:
        st.warning("등록된 사용자가 없습니다. 새 사용자를 추가해주세요.")

with col2:
    # 사용자 추가
    with st.expander("➕ 사용자 추가", expanded=False):
        new_user_name = st.text_input("새 사용자 이름")
        if st.button("추가", use_container_width=True):
            if new_user_name:
                dm.add_user(new_user_name)
                st.success(f"{new_user_name} 추가 완료!")
                st.rerun()
            else:
                st.error("이름을 입력하세요.")

st.divider()

# 사용자가 선택된 경우에만 나머지 표시
if st.session_state.current_user:
    user_id = st.session_state.current_user['id']
    
    # 일정 확인 섹션
    st.header("📅 일정 확인")
    
    # 사용자의 스케줄 로드
    user_schedules = dm.get_user_schedules(user_id)
    
    if not user_schedules.empty:
        # 월 선택
        col1, col2 = st.columns([1, 3])
        with col1:
            selected_month = st.date_input(
                "월 선택",
                value=datetime.now(),
                key="month_select"
            )
        
        # 선택된 월의 스케줄 필터링
        user_schedules['start_date'] = pd.to_datetime(user_schedules['start_date'])
        user_schedules['end_date'] = pd.to_datetime(user_schedules['end_date'])
        
        month_start = pd.Timestamp(selected_month.year, selected_month.month, 1)
        if selected_month.month == 12:
            month_end = pd.Timestamp(selected_month.year + 1, 1, 1)
        else:
            month_end = pd.Timestamp(selected_month.year, selected_month.month + 1, 1)
        
        filtered_schedules = user_schedules[
            (user_schedules['start_date'] < month_end) & 
            (user_schedules['end_date'] >= month_start)
        ]
        
        if not filtered_schedules.empty:
            # Gantt Chart 생성
            fig = px.timeline(
                filtered_schedules,
                x_start='start_date',
                x_end='end_date',
                y='test_name',
                color='request_id',
                title=f"{selected_month.strftime('%Y년 %m월')} 시험 일정",
                labels={'test_name': '시험 항목', 'request_id': '의뢰 ID'}
            )
            
            fig.update_yaxes(categoryorder='total ascending')
            fig.update_layout(height=400, showlegend=True)
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(f"📌 {selected_month.strftime('%Y년 %m월')}에 예정된 일정이 없습니다.")
    else:
        st.info("📌 아직 등록된 일정이 없습니다.")
    
    st.divider()
    
    # 의뢰 관리 섹션
    st.header("📋 의뢰 관리")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📂 기존 의뢰")
        
        # 사용자의 의뢰 목록 로드
        requests_df = dm.load_request_info()
        user_requests = requests_df[requests_df['user_id'] == user_id]
        
        if not user_requests.empty:
            request_options = [
                f"{row['id']} - {row['client']} ({row['project']})" 
                for _, row in user_requests.iterrows()
            ]
            
            selected_request_str = st.selectbox(
                "의뢰 선택",
                request_options,
                key="request_select"
            )
            
            if selected_request_str:
                request_id = selected_request_str.split(" - ")[0]
                selected_request = user_requests[user_requests['id'] == request_id].iloc[0]
                
                # 의뢰 정보 표시
                st.info(f"""
                **의뢰 ID**: {selected_request['id']}  
                **발주처**: {selected_request['client']}  
                **프로젝트**: {selected_request['project']}  
                **검증 여부**: {'✅ 완료' if selected_request['is_verified'] else '⏳ 진행중'}
                """)
                
                # 해당 의뢰의 일정 표시
                request_schedules = user_schedules[
                    user_schedules['request_id'] == request_id
                ]
                
                if not request_schedules.empty:
                    st.markdown("##### 📅 의뢰 일정")
                    
                    fig = px.timeline(
                        request_schedules,
                        x_start='start_date',
                        x_end='end_date',
                        y='test_name',
                        color='status',
                        title=f"의뢰 {request_id} 일정",
                        color_discrete_map={
                            'planned': '#FFA500',
                            'in_progress': '#4169E1',
                            'completed': '#32CD32',
                            'cancelled': '#DC143C'
                        }
                    )
                    
                    fig.update_yaxes(categoryorder='total ascending')
                    fig.update_layout(height=300)
                    
                    st.plotly_chart(fig, use_container_width=True)
                
                # 의뢰 수정 버튼
                if st.button("✏️ 의뢰 수정", use_container_width=True):
                    st.session_state.current_request = selected_request.to_dict()
                    
                    # 추출 데이터 로드
                    try:
                        import json
                        extracted_data = json.loads(selected_request['extracted_data'])
                        st.session_state.extracted_data = extracted_data
                        st.success("✅ 의뢰 데이터를 불러왔습니다.")
                        st.info("👉 '📝 Edit Extraction' 페이지로 이동하세요.")
                    except:
                        st.error("데이터 로드 중 오류가 발생했습니다.")
        else:
            st.info("등록된 의뢰가 없습니다.")
    
    with col2:
        st.subheader("➕ 새 의뢰")
        
        # API 키 입력
        api_key = st.text_input(
            "Gemini API Key",
            type="password",
            help="Google AI Studio에서 발급받은 API 키를 입력하세요.",
            key="gemini_api_key"
        )
        
        # 파일 업로드
        uploaded_file = st.file_uploader(
            "시험 규격 문서 업로드",
            type=['pdf', 'docx'],
            help="PDF 또는 DOCX 형식의 시험 규격 문서를 업로드하세요."
        )
        
        # 샘플 데이터 로드 버튼
        use_sample = st.checkbox("샘플 데이터 사용 (테스트용)", value=False)
        
        if st.button("🚀 새 의뢰 생성", use_container_width=True, type="primary"):
            if use_sample:
                # 샘플 데이터 사용
                with st.spinner("샘플 데이터 생성 중..."):
                    parser = LLMParser(api_key or "dummy")
                    extracted_data = parser.extract_sample_data()
                    
                    # 표준화 적용
                    standardizer = Standardizer()
                    extracted_data['test_items'] = standardizer.standardize_all_items(
                        extracted_data['test_items']
                    )
                    
                    # 세션에 저장
                    st.session_state.extracted_data = extracted_data
                    
                    # 의뢰 생성
                    request_id = dm.add_request(
                        user_id,
                        extracted_data['request_info']['client'],
                        extracted_data['request_info']['project'],
                        extracted_data
                    )
                    
                    st.session_state.current_request = {
                        'id': request_id,
                        'user_id': user_id,
                        'client': extracted_data['request_info']['client'],
                        'project': extracted_data['request_info']['project']
                    }
                    
                    st.success("✅ 샘플 의뢰가 생성되었습니다!")
                    st.info("👉 '📝 Edit Extraction' 페이지로 이동하세요.")
                    st.rerun()
                    
            elif uploaded_file and api_key:
                # 실제 파일 파싱
                with st.spinner("문서 파싱 중... (최대 1분 소요)"):
                    try:
                        file_bytes = uploaded_file.read()
                        file_type = uploaded_file.name.split('.')[-1].lower()
                        
                        # LLM 파서 초기화 및 파싱
                        parser = LLMParser(api_key)
                        extracted_data = parser.parse_document(file_bytes, file_type)
                        
                        if extracted_data:
                            # 표준화 적용
                            standardizer = Standardizer()
                            extracted_data['test_items'] = standardizer.standardize_all_items(
                                extracted_data['test_items']
                            )
                            
                            # 세션에 저장
                            st.session_state.extracted_data = extracted_data
                            
                            # 의뢰 생성
                            request_id = dm.add_request(
                                user_id,
                                extracted_data['request_info']['client'],
                                extracted_data['request_info']['project'],
                                extracted_data
                            )
                            
                            st.session_state.current_request = {
                                'id': request_id,
                                'user_id': user_id,
                                'client': extracted_data['request_info']['client'],
                                'project': extracted_data['request_info']['project']
                            }
                            
                            st.success("✅ 문서 파싱이 완료되었습니다!")
                            st.info("👉 '📝 Edit Extraction' 페이지로 이동하세요.")
                            st.rerun()
                        else:
                            st.error("❌ 문서 파싱에 실패했습니다.")
                    except Exception as e:
                        st.error(f"❌ 오류 발생: {str(e)}")
            else:
                st.warning("⚠️ API 키와 파일을 모두 입력하거나, 샘플 데이터를 선택하세요.")

else:
    st.warning("⚠️ 먼저 사용자를 선택하세요.")
