import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime

def create_gantt_chart(schedule_data, color_by='request', title='Test Schedule'):
    """Gantt 차트 생성"""
    if len(schedule_data) == 0:
        return None
    
    # 데이터 준비
    df = pd.DataFrame(schedule_data)
    
    # 날짜 형식 변환
    if 'start_date' in df.columns:
        df['Start'] = pd.to_datetime(df['start_date'])
        df['Finish'] = pd.to_datetime(df['end_date'])
    else:
        df['Start'] = df['start_day']
        df['Finish'] = df['end_day']
    
    # Task 이름 설정
    if 'test_name' in df.columns:
        df['Task'] = df['test_name']
    elif 'Test Title' in df.columns:
        df['Task'] = df['Test Title']
    else:
        df['Task'] = df.index.astype(str)
    
    # 색상 설정
    if color_by == 'request' and 'request_id' in df.columns:
        color_col = 'request_id'
    elif 'category' in df.columns:
        color_col = 'category'
    else:
        color_col = None
    
    # Gantt 차트 생성
    if color_col:
        fig = px.timeline(
            df,
            x_start='Start',
            x_end='Finish',
            y='Task',
            color=color_col,
            title=title
        )
    else:
        fig = px.timeline(
            df,
            x_start='Start',
            x_end='Finish',
            y='Task',
            title=title
        )
    
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(
        height=max(400, len(df) * 40),
        xaxis_title="Timeline",
        yaxis_title="Test Items",
        showlegend=True
    )
    
    return fig

def create_calendar_view(schedule_data, month):
    """월별 캘린더 뷰 생성"""
    if len(schedule_data) == 0:
        return None
    
    df = pd.DataFrame(schedule_data)
    df['start_date'] = pd.to_datetime(df['start_date'])
    df['end_date'] = pd.to_datetime(df['end_date'])
    
    # 해당 월의 모든 날짜 생성
    month_start = pd.to_datetime(f"{month}-01")
    if month_start.month == 12:
        month_end = month_start.replace(year=month_start.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        month_end = month_start.replace(month=month_start.month + 1, day=1) - timedelta(days=1)
    
    date_range = pd.date_range(month_start, month_end)
    
    # 날짜별 시험 항목 매핑
    calendar_data = []
    for date in date_range:
        tests_on_date = df[
            (df['start_date'] <= date) & (df['end_date'] >= date)
        ]
        
        calendar_data.append({
            'date': date,
            'day': date.day,
            'weekday': date.strftime('%A'),
            'test_count': len(tests_on_date),
            'tests': ', '.join(tests_on_date['test_name'].tolist() if 'test_name' in tests_on_date.columns else [])
        })
    
    return pd.DataFrame(calendar_data)

from datetime import timedelta
