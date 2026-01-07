import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from modules.data_manager import DataManager

st.set_page_config(page_title="View Schedule", page_icon="📊", layout="wide")

dm = DataManager()

st.title("📊 전체 시험 일정 보기")

# 세션 체크
if not st.session_state.current_user:
    st.warning("⚠️ 먼저 사용자를 선택하세요.")
    st.info("👉 '🏠 User Selection' 페이지로 이동하세요.")
    st.stop()

user_id = st.session_state.current_user['id']
user_name = st.session_state.current_user['user_name']

st.subheader(f"👤 {user_name}님의 시험 일정")

# 사용자의 전체 스케줄 로드
user_schedules = dm.get_user_schedules(user_id)

if user_schedules.empty:
    st.info("📌 등록된 시험 일정이 없습니다.")
    st.markdown("""
    ### 시작하기
    
    1. **🏠 User Selection**: 사용자 선택 및 새 의뢰 생성
    2. **📝 Edit Extraction**: 추출된 데이터 검토 및 편집
    3. **📋 Draft Plan**: 시험 계획서 초안 작성
    4. **📅 Schedule**: 시험 일정 생성 및 저장
    5. **📊 View Schedule**: 전체 일정 확인 (현재 페이지)
    """)
    st.stop()

# 날짜 변환
user_schedules['start_date'] = pd.to_datetime(user_schedules['start_date'])
user_schedules['end_date'] = pd.to_datetime(user_schedules['end_date'])

# 통계 정보
st.header("📈 통계")

col1, col2, col3, col4 = st.columns(4)

with col1:
    total_tests = len(user_schedules)
    st.metric("총 시험 항목", total_tests)

with col2:
    total_requests = user_schedules['request_id'].nunique()
    st.metric("총 의뢰 수", total_requests)

with col3:
    planned = len(user_schedules[user_schedules['status'] == 'planned'])
    st.metric("계획된 시험", planned)

with col4:
    in_progress = len(user_schedules[user_schedules['status'] == 'in_progress'])
    st.metric("진행중 시험", in_progress)

st.divider()

# 필터링 옵션
st.header("🔍 필터")

col1, col2, col3 = st.columns(3)

with col1:
    # 월 선택
    min_date = user_schedules['start_date'].min()
    max_date = user_schedules['end_date'].max()
    
    view_mode = st.radio(
        "보기 모드",
        ["전체", "월별"],
        horizontal=True
    )
    
    if view_mode == "월별":
        selected_month = st.date_input(
            "월 선택",
            value=datetime.now(),
            min_value=min_date.to_pydatetime(),
            max_value=max_date.to_pydatetime()
        )

with col2:
    # 의뢰 필터
    requests = user_schedules['request_id'].unique().tolist()
    selected_requests = st.multiselect(
        "의뢰 필터",
        options=requests,
        default=requests,
        help="표시할 의뢰를 선택하세요."
    )

with col3:
    # 상태 필터
    statuses = user_schedules['status'].unique().tolist()
    selected_statuses = st.multiselect(
        "상태 필터",
        options=statuses,
        default=statuses,
        help="표시할 상태를 선택하세요."
    )

# 필터 적용
filtered_schedules = user_schedules[
    (user_schedules['request_id'].isin(selected_requests)) &
    (user_schedules['status'].isin(selected_statuses))
]

# 월별 필터링
if view_mode == "월별":
    month_start = pd.Timestamp(selected_month.year, selected_month.month, 1)
    if selected_month.month == 12:
        month_end = pd.Timestamp(selected_month.year + 1, 1, 1)
    else:
        month_end = pd.Timestamp(selected_month.year, selected_month.month + 1, 1)
    
    filtered_schedules = filtered_schedules[
        (filtered_schedules['start_date'] < month_end) & 
        (filtered_schedules['end_date'] >= month_start)
    ]

st.divider()

# 일정 표시
if filtered_schedules.empty:
    st.warning("⚠️ 선택한 조건에 해당하는 일정이 없습니다.")
else:
    st.header("📅 일정 타임라인")
    
    # 뷰 선택
    view_type = st.radio(
        "차트 유형",
        ["Gantt Chart", "캘린더 뷰"],
        horizontal=True
    )
    
    if view_type == "Gantt Chart":
        # Gantt Chart
        fig = px.timeline(
            filtered_schedules,
            x_start='start_date',
            x_end='end_date',
            y='test_name',
            color='request_id',
            hover_data=['status', 'duration', 'category'],
            title="시험 일정 Gantt Chart",
            labels={
                'test_name': '시험 항목',
                'request_id': '의뢰 ID',
                'status': '상태',
                'duration': '기간 (일)',
                'category': '분류'
            }
        )
        
        fig.update_yaxes(categoryorder='total ascending')
        fig.update_layout(
            height=max(500, len(filtered_schedules) * 30),
            xaxis_title="날짜",
            yaxis_title="시험 항목",
            showlegend=True
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    else:
        # 캘린더 뷰
        st.markdown("### 📆 캘린더 뷰")
        
        # 월별 그룹화
        filtered_schedules['month'] = filtered_schedules['start_date'].dt.to_period('M')
        months = sorted(filtered_schedules['month'].unique())
        
        for month in months:
            month_data = filtered_schedules[filtered_schedules['month'] == month]
            
            with st.expander(f"📅 {month}", expanded=True):
                # 일별 시험 항목 표시
                month_start = pd.Timestamp(month.to_timestamp())
                month_end = month_start + pd.DateOffset(months=1)
                
                date_range = pd.date_range(month_start, month_end - pd.Timedelta(days=1), freq='D')
                
                calendar_data = []
                for date in date_range:
                    day_tests = month_data[
                        (month_data['start_date'] <= date) & 
                        (month_data['end_date'] >= date)
                    ]
                    
                    if not day_tests.empty:
                        calendar_data.append({
                            'Date': date.strftime('%Y-%m-%d'),
                            'Day': date.strftime('%a'),
                            'Tests': ', '.join(day_tests['test_name'].tolist()[:3]) + 
                                    (f" 외 {len(day_tests)-3}건" if len(day_tests) > 3 else ""),
                            'Count': len(day_tests)
                        })
                
                if calendar_data:
                    cal_df = pd.DataFrame(calendar_data)
                    st.dataframe(
                        cal_df,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "Date": st.column_config.DateColumn("날짜", format="YYYY-MM-DD"),
                            "Day": st.column_config.TextColumn("요일", width="small"),
                            "Tests": st.column_config.TextColumn("시험 항목", width="large"),
                            "Count": st.column_config.NumberColumn("항목 수", width="small")
                        }
                    )
                else:
                    st.info("이 달에는 예정된 시험이 없습니다.")
    
    st.divider()
    
    # 상세 테이블
    st.header("📋 상세 일정 테이블")
    
    # 표시할 컬럼 선택
    display_columns = st.multiselect(
        "표시할 컬럼 선택",
        options=['test_name', 'category', 'request_id', 'start_date', 'end_date', 
                'duration', 'status', 'ref_standard', 'sample_assembly'],
        default=['test_name', 'category', 'start_date', 'end_date', 'duration', 'status'],
        help="테이블에 표시할 컬럼을 선택하세요."
    )
    
    # 날짜 포맷 변환
    display_df = filtered_schedules[display_columns].copy()
    if 'start_date' in display_df.columns:
        display_df['start_date'] = display_df['start_date'].dt.strftime('%Y-%m-%d')
    if 'end_date' in display_df.columns:
        display_df['end_date'] = display_df['end_date'].dt.strftime('%Y-%m-%d')
    
    # 컬럼명 한글화
    column_names = {
        'test_name': '시험명',
        'category': '분류',
        'request_id': '의뢰 ID',
        'start_date': '시작일',
        'end_date': '종료일',
        'duration': '기간(일)',
        'status': '상태',
        'ref_standard': '참조 규격',
        'sample_assembly': '시료 구성'
    }
    
    display_df.columns = [column_names.get(col, col) for col in display_df.columns]
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        height=400
    )
    
    # CSV 다운로드
    csv = display_df.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="📥 CSV 다운로드",
        data=csv,
        file_name=f"schedule_{user_name}_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
    )

st.divider()

# 의뢰별 통계
st.header("📊 의뢰별 통계")

request_stats = user_schedules.groupby('request_id').agg({
    'test_item_id': 'count',
    'duration': 'sum',
    'start_date': 'min',
    'end_date': 'max'
}).reset_index()

request_stats.columns = ['의뢰 ID', '시험 항목 수', '총 소요 기간 (일)', '시작일', '종료일']
request_stats['시작일'] = pd.to_datetime(request_stats['시작일']).dt.strftime('%Y-%m-%d')
request_stats['종료일'] = pd.to_datetime(request_stats['종료일']).dt.strftime('%Y-%m-%d')

st.dataframe(
    request_stats,
    use_container_width=True,
    hide_index=True
)

# 상태별 통계 차트
col1, col2 = st.columns(2)

with col1:
    st.subheader("상태별 분포")
    status_counts = user_schedules['status'].value_counts()
    
    fig = px.pie(
        values=status_counts.values,
        names=status_counts.index,
        title="시험 상태 분포",
        color_discrete_map={
            'planned': '#FFA500',
            'in_progress': '#4169E1',
            'completed': '#32CD32',
            'cancelled': '#DC143C'
        }
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("분류별 분포")
    category_counts = user_schedules['category'].value_counts()
    
    fig = px.bar(
        x=category_counts.index,
        y=category_counts.values,
        title="시험 분류별 항목 수",
        labels={'x': '분류', 'y': '항목 수'},
        color=category_counts.values,
        color_continuous_scale='Viridis'
    )
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

# 타임라인 요약
st.divider()
st.header("📅 타임라인 요약")

col1, col2, col3 = st.columns(3)

with col1:
    earliest_start = user_schedules['start_date'].min()
    st.metric("가장 빠른 시작일", earliest_start.strftime('%Y-%m-%d'))

with col2:
    latest_end = user_schedules['end_date'].max()
    st.metric("가장 늦은 종료일", latest_end.strftime('%Y-%m-%d'))

with col3:
    total_span = (latest_end - earliest_start).days + 1
    st.metric("전체 기간", f"{total_span} 일")

# 진행률 계산
today = pd.Timestamp.now()
completed = len(user_schedules[user_schedules['status'] == 'completed'])
total = len(user_schedules)
progress = (completed / total * 100) if total > 0 else 0

st.progress(progress / 100)
st.caption(f"전체 진행률: {progress:.1f}% ({completed}/{total} 완료)")
