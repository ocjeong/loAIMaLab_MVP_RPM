import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from modules.database import get_user_requests, get_test_items

def create_gantt_chart(test_items: List[Dict], start_date: datetime = None) -> go.Figure:
    """Gantt 차트 생성"""
    
    if start_date is None:
        start_date = datetime.now()
    
    # 데이터 준비
    chart_data = []
    current_date = start_date
    
    for item in test_items:
        if item.get('is_included', True):
            duration = item.get('test_duration', 1.0)
            end_date = current_date + timedelta(days=duration)
            
            chart_data.append({
                'Task': item.get('test_name', 'Unknown'),
                'Start': current_date,
                'Finish': end_date,
                'Category': item.get('category', 'Other'),
                'Duration': f"{duration}일"
            })
            
            current_date = end_date
    
    if not chart_data:
        return None
    
    df = pd.DataFrame(chart_data)
    
    # Plotly 타임라인 차트
    fig = px.timeline(
        df,
        x_start='Start',
        x_end='Finish',
        y='Task',
        color='Category',
        title='시험 일정 타임라인',
        hover_data=['Duration']
    )
    
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(
        height=max(400, len(chart_data) * 40),
        xaxis_title="날짜",
        yaxis_title="시험 항목",
        showlegend=True
    )
    
    return fig

def create_monthly_schedule(user_id: str) -> Optional[go.Figure]:
    """사용자의 월간 일정 생성"""
    
    # 사용자의 모든 의뢰 조회
    requests = get_user_requests(user_id)
    
    if not requests:
        return None
    
    # 모든 의뢰의 시험 항목 수집
    all_items = []
    
    for request in requests:
        request_id = request[0]
        test_items = get_test_items(request_id)
        
        for item in test_items:
            if item.get('start_date') and item.get('end_date'):
                all_items.append({
                    'Task': f"{item['test_name']} ({request_id})",
                    'Start': datetime.strptime(item['start_date'], '%Y-%m-%d'),
                    'Finish': datetime.strptime(item['end_date'], '%Y-%m-%d'),
                    'Category': item.get('category', 'Other'),
                    'Request': request_id
                })
    
    if not all_items:
        return None
    
    df = pd.DataFrame(all_items)
    
    # Gantt 차트
    fig = px.timeline(
        df,
        x_start='Start',
        x_end='Finish',
        y='Task',
        color='Request',
        title=f'이번 달 시험 일정 ({datetime.now().strftime("%Y년 %m월")})'
    )
    
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(height=max(300, len(all_items) * 30))
    
    return fig

def create_category_distribution_chart(test_items: List[Dict]) -> go.Figure:
    """시험 분류별 분포 차트"""
    
    categories = {}
    for item in test_items:
        category = item.get('category', 'Other')
        categories[category] = categories.get(category, 0) + 1
    
    fig = go.Figure(data=[
        go.Pie(
            labels=list(categories.keys()),
            values=list(categories.values()),
            hole=0.3
        )
    ])
    
    fig.update_layout(
        title='시험 분류별 분포',
        height=400
    )
    
    return fig
