import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from modules.data_manager import DataManager
from modules.scheduler import Scheduler

st.set_page_config(page_title="Schedule", page_icon="📅", layout="wide")

dm = DataManager()
scheduler = Scheduler()

st.title("📅 시험 일정 스케줄링")

# 세션 체크
if not st.session_state.current_user:
    st.warning("⚠️ 먼저 사용자를 선택하세요.")
    st.stop()

if not st.session_state.draft_plan:
    st.warning("⚠️ 계획서 초안이 없습니다.")
    st.info("👉 '📋 Draft Plan' 페이지에서 계획서를 먼저 작성하세요.")
    st.stop()

if not st.session_state.extracted_data:
    st.warning("⚠️ 시험 항목 데이터가 없습니다.")
    st.stop()

# 데이터 로드
user_id = st.session_state.current_user['id']
test_items = st.session_state.extracted_data.get('test_items', [])

# D-day 스케줄 생성
if 'dday_schedule' not in st.session_state:
    dday_schedules = scheduler.create_dday_schedule(test_items)
    st.session_state.dday_schedule = dday_schedules

dday_schedules = st.session_state.dday_schedule

# 타임라인 정보
st.header("⏱️ D-day 기반 타임라인")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("총 시험 항목", len(dday_schedules))
with col2:
    max_day = max([s['end_day'] for s in dday_schedules]) if dday_schedules else 0
    st.metric("총 소요 기간", f"{max_day} 일")
with col3:
    total_duration = sum([s['duration'] for s in dday_schedules])
    st.metric("누적 시험 시간", f"{total_duration} 일")

st.divider()

# D-day 스케줄 표시
st.subheader("📊 D-day 스케줄")

# 데이터프레임 생성
dday_df = pd.DataFrame(dday_schedules)

if not dday_df.empty:
    # Gantt Chart 생성 (D-day 기준)
    fig = go.Figure()
    
    colors = px.colors.qualitative.Set3
    
    for idx, row in dday_df.iterrows():
        fig.add_trace(go.Bar(
            name=row['test_name'],
            x=[row['duration']],
            y=[row['test_name']],
            orientation='h',
            marker=dict(color=colors[idx % len(colors)]),
            text=f"D+{row['start_day']} ~ D+{row['end_day']} ({row['duration']}일)",
            textposition='inside',
            hovertemplate=(
                f"<b>{row['test_name']}</b><br>" +
                f"시작: D+{row['start_day']}<br>" +
                f"종료: D+{row['end_day']}<br>" +
                f"기간: {row['duration']}일<br>" +
                "<extra></extra>"
            ),
            base=row['start_day']
        ))
    
    fig.update_layout(
        title="시험 일정 타임라인 (D-day)",
        xaxis_title="D-day",
        yaxis_title="시험 항목",
        height=max(400, len(dday_schedules) * 40),
        showlegend=False,
        barmode='overlay',
        xaxis=dict(
            tickmode='linear',
            tick0=0,
            dtick=5
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 테이블로도 표시
    with st.expander("📋 상세 일정 테이블", expanded=False):
        display_df = dday_df[['test_name', 'start_day', 'end_day', 'duration', 'status']].copy()
        display_df.columns = ['시험명', '시작 (D-day)', '종료 (D-day)', '소요 기간 (일)', '상태']
        st.dataframe(display_df, use_container_width=True)

st.divider()

# 실제 날짜로 변환
st.header("📆 실제 날짜 스케줄 생성")

col1, col2 = st.columns([2, 1])

with col1:
    # 기본 시작일 계산
    default_start = scheduler.get_default_start_date(user_id)
    
    start_date = st.date_input(
        "시험 시작일",
        value=datetime.strptime(default_start, '%Y-%m-%d'),
        help="시험을 시작할 날짜를 선택하세요. 기본값은 마지막 시험 종료일 다음날입니다."
    )

with col2:
    st.info(f"💡 **추천 시작일**\n\n{default_start}\n\n(마지막 일정 종료 다음날)")

# 날짜 스케줄 생성 버튼
if st.button("🗓️ 날짜 스케줄 생성", use_container_width=True, type="primary"):
    start_date_str = start_date.strftime('%Y-%m-%d')
    
    # 날짜 스케줄 변환
    date_schedules = scheduler.convert_to_date_schedule(dday_schedules, start_date_str)
    st.session_state.date_schedule = date_schedules
    
    st.success("✅ 날짜 스케줄이 생성되었습니다!")

# 날짜 스케줄이 생성된 경우 표시
if 'date_schedule' in st.session_state and st.session_state.date_schedule:
    st.divider()
    st.subheader("📅 날짜 기반 스케줄")
    
    date_schedules = st.session_state.date_schedule
    date_df = pd.DataFrame(date_schedules)
    
    # 날짜 변환
    date_df['start_date'] = pd.to_datetime(date_df['start_date'])
    date_df['end_date'] = pd.to_datetime(date_df['end_date'])
    
    # 통계
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("시작일", date_df['start_date'].min().strftime('%Y-%m-%d'))
    with col2:
        st.metric("종료일", date_df['end_date'].max().strftime('%Y-%m-%d'))
    with col3:
        total_days = (date_df['end_date'].max() - date_df['start_date'].min()).days + 1
        st.metric("총 기간", f"{total_days} 일")
    
    # Gantt Chart (날짜 기준)
    # 시험 항목 이름 추가
    date_df_display = date_df.copy()
    test_items_dict = {item['id']: item for item in test_items}
    date_df_display['test_name'] = date_df_display['test_item_id'].apply(
        lambda x: test_items_dict.get(x, {}).get('test_name', 'Unknown')
    )
    
    fig = px.timeline(
        date_df_display,
        x_start='start_date',
        x_end='end_date',
        y='test_name',
        color='status',
        title="시험 일정 (실제 날짜)",
        labels={'test_name': '시험 항목', 'status': '상태'},
        color_discrete_map={
            'planned': '#FFA500',
            'in_progress': '#4169E1',
            'completed': '#32CD32',
            'cancelled': '#DC143C'
        }
    )
    
    fig.update_yaxes(categoryorder='total ascending')
    fig.update_layout(
        height=max(400, len(date_schedules) * 40),
        xaxis_title="날짜",
        yaxis_title="시험 항목"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 테이블로도 표시
    with st.expander("📋 상세 날짜 테이블", expanded=True):
        display_df = date_df_display[['test_name', 'start_date', 'end_date', 'duration', 'status']].copy()
        display_df['start_date'] = display_df['start_date'].dt.strftime('%Y-%m-%d')
        display_df['end_date'] = display_df['end_date'].dt.strftime('%Y-%m-%d')
        display_df.columns = ['시험명', '시작일', '종료일', '소요 기간 (일)', '상태']
        st.dataframe(display_df, use_container_width=True, height=400)
    
    st.divider()
    
    # 일정 저장
    st.header("💾 일정 저장")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.info("""
        **저장 안내**
        
        - 생성된 일정을 데이터베이스에 저장합니다.
        - 저장 후 '📊 View Schedule' 페이지에서 전체 일정을 확인할 수 있습니다.
        - 저장된 일정은 사용자의 전체 일정에 반영됩니다.
        """)
    
    with col2:
        if st.button("💾 일정 저장", use_container_width=True, type="primary"):
            try:
                # 스케줄 저장
                dm.add_schedule_items(date_schedules)
                
                st.success("✅ 일정이 저장되었습니다!")
                st.balloons()
                st.info("👉 '📊 View Schedule' 페이지에서 전체 일정을 확인하세요.")
                
                # 세션 정리
                if st.button("🏠 처음으로 돌아가기"):
                    st.session_state.draft_plan = None
                    st.session_state.date_schedule = None
                    st.session_state.dday_schedule = None
                    st.rerun()
                    
            except Exception as e:
                st.error(f"❌ 저장 중 오류 발생: {str(e)}")

else:
    st.info("💡 시험 시작일을 선택하고 '날짜 스케줄 생성' 버튼을 클릭하세요.")

# 추가 정보
with st.expander("ℹ️ 스케줄링 정보", expanded=False):
    st.markdown("""
    ### 스케줄링 알고리즘
    
    **우선순위**
    1. 소요 시간이 긴 시험부터 우선 배치
    2. 최대 2개의 시험을 병렬로 진행
    3. 각 트랙에서 더 빨리 끝나는 쪽에 다음 시험 배치
    
    **기본값**
    - 시험 소요 기간이 명시되지 않은 경우: 1일
    - 시작일 미지정 시: 마지막 시험 종료일 다음날 (또는 오늘)
    
    **상태 코드**
    - `planned`: 계획됨
    - `in_progress`: 진행중
    - `completed`: 완료
    - `cancelled`: 취소됨
    """)
