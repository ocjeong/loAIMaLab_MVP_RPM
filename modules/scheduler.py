import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta


def create_test_plan(test_items):
    """시험 항목으로부터 계획서 생성"""
    plan_data = []
    
    # 우선순위 정의 (분류별)
    priority_order = {
        'Electrical Test': 1,
        'Environmental Test': 2,
        'Mechanical Test': 3,
        'Endurance Test': 4,
        'Acoustic Test': 5,
        'Corrosion Test': 6
    }
    
    for item in test_items:
        plan_data.append({
            '포함': True,
            '시험명': item.get('test_name', ''),
            '분류': item.get('category', ''),
            '참조규격': item.get('ref_standard', ''),
            '시료구성': item.get('sample_assembly', ''),
            '시료수': item.get('sample_count', ''),
            '시험기간': item.get('test_duration', ''),
            '시험기기': item.get('test_equipment', ''),
            '우선순위': priority_order.get(item.get('category', ''), 99)
        })
    
    df = pd.DataFrame(plan_data)
    
    # 우선순위로 정렬
    df = df.sort_values('우선순위').reset_index(drop=True)
    df = df.drop('우선순위', axis=1)
    
    return df


def generate_gantt_chart(schedule_data):
    """Gantt 차트 생성"""
    if schedule_data.empty:
        # 빈 차트 반환
        fig = go.Figure()
        fig.update_layout(
            title="등록된 일정이 없습니다",
            xaxis_title="일수 (Days)",
            yaxis_title="시험 항목"
        )
        return fig
    
    # 간단한 Gantt 차트 생성
    tasks = schedule_data['Task'].tolist()
    
    fig = go.Figure()
    
    for idx, task in enumerate(tasks):
        fig.add_trace(go.Bar(
            y=[task],
            x=[1],
            orientation='h',
            name=task,
            showlegend=False
        ))
    
    fig.update_layout(
        title="시험 일정",
        xaxis_title="기간",
        yaxis_title="시험 항목",
        height=max(400, len(tasks) * 40),
        barmode='stack'
    )
    
    return fig
