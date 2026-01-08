from typing import Dict, List
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

class SchedulingManager:
    def __init__(self, database):
        self.db = database
    
    def create_dday_schedule(self, test_items: List[Dict]) -> List[Dict]:
        """D-day 기준 일정 생성"""
        # 소요 시간 기준 정렬 (긴 것부터)
        sorted_items = sorted(test_items, 
                            key=lambda x: int(x.get('test_duration', 1)), 
                            reverse=True)
        
        # 병렬 진행 트랙 (최대 2개)
        tracks = [0, 0]  # 각 트랙의 현재 종료일
        schedule = []
        
        for item in sorted_items:
            duration = int(item.get('test_duration', 1))
            
            # 가장 빨리 끝나는 트랙 선택
            track_idx = 0 if tracks[0] <= tracks[1] else 1
            
            start_day = tracks[track_idx]
            end_day = start_day + duration
            
            schedule.append({
                'test_item_id': item.get('id', ''),
                'test_name': item.get('test_name', ''),
                'start_day': start_day,
                'end_day': end_day,
                'duration': duration,
                'track': track_idx
            })
            
            tracks[track_idx] = end_day
        
        return schedule
    
    def convert_to_date_schedule(self, dday_schedule: List[Dict], 
                                 start_date: datetime) -> List[Dict]:
        """D-day 일정을 실제 날짜로 변환"""
        date_schedule = []
        
        for item in dday_schedule:
            start = start_date + timedelta(days=item['start_day'])
            end = start_date + timedelta(days=item['end_day'])
            
            date_schedule.append({
                'test_item_id': item['test_item_id'],
                'start_date': start.strftime('%Y-%m-%d'),
                'end_date': end.strftime('%Y-%m-%d'),
                'start_day': item['start_day'],
                'end_day': item['end_day'],
                'duration': item['duration'],
                'status': 'planned'
            })
        
        return date_schedule
    
    def create_gantt_chart(self, schedule_data: List[Dict], 
                          date_mode: bool = False,
                          title: str = "Test Schedule") -> go.Figure:
        """Gantt 차트 생성"""
        if not schedule_data:
            fig = go.Figure()
            fig.update_layout(title=title)
            return fig
        
        df = pd.DataFrame(schedule_data)
        
        if date_mode:
            df['Start'] = pd.to_datetime(df['start_date'])
            df['Finish'] = pd.to_datetime(df['end_date'])
        else:
            # D-day 모드
            base_date = datetime.now()
            df['Start'] = df['start_day'].apply(lambda x: base_date + timedelta(days=x))
            df['Finish'] = df['end_day'].apply(lambda x: base_date + timedelta(days=x))
        
        df['Task'] = df.get('test_name', df.get('test_item_id', 'Test'))
        
        # 색상 할당
        unique_tasks = df['Task'].unique()
        colors = px.colors.qualitative.Plotly
        color_map = {task: colors[i % len(colors)] for i, task in enumerate(unique_tasks)}
        df['Color'] = df['Task'].map(color_map)
        
        fig = go.Figure()
        
        for _, row in df.iterrows():
            fig.add_trace(go.Bar(
                x=[row['Finish'] - row['Start']],
                y=[row['Task']],
                base=row['Start'],
                orientation='h',
                marker=dict(color=row['Color']),
                name=row['Task'],
                showlegend=False,
                hovertemplate=f"<b>{row['Task']}</b><br>" +
                             f"Start: {row['Start'].strftime('%Y-%m-%d')}<br>" +
                             f"End: {row['Finish'].strftime('%Y-%m-%d')}<br>" +
                             f"Duration: {row['duration']} days<extra></extra>"
            ))
        
        fig.update_layout(
            title=title,
            xaxis_title="Date" if date_mode else "Day",
            yaxis_title="Test Item",
            height=max(400, len(df) * 30),
            barmode='overlay',
            showlegend=False
        )
        
        return fig
    
    def get_default_start_date(self, user_id: str) -> datetime:
        """사용자의 기본 시작일 계산"""
        last_date = self.db.get_last_schedule_date(user_id)
        
        if last_date:
            return last_date + timedelta(days=1)
        else:
            return datetime.now()
