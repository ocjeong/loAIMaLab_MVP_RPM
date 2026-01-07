import plotly.figure_factory as ff
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd

class SchedulingModule:
    def __init__(self):
        self.priority_order = [
            'Functional Test',
            'Environmental Test',
            'Electrical Tests',
            'Performance Test',
            'Endurance Test'
        ]
    
    def create_schedule(self, plan_data):
        """시험 일정 생성"""
        
        # 우선순위에 따라 정렬
        sorted_items = self._sort_by_priority(plan_data)
        
        # 일정 계산
        schedule = []
        current_day = 0
        
        for item in sorted_items:
            duration = int(item.get('test_duration', 1))
            
            schedule_item = {
                'test_name': item.get('test_name', ''),
                'category': item.get('category', ''),
                'start_day': current_day,
                'end_day': current_day + duration,
                'duration': duration,
                'sample_count': item.get('sample_count', ''),
                'ref_standard': item.get('ref_standard', '')
            }
            
            schedule.append(schedule_item)
            current_day += duration
        
        return schedule
    
    def _sort_by_priority(self, plan_data):
        """우선순위에 따라 정렬"""
        
        def get_priority(item):
            category = item.get('category', '')
            try:
                return self.priority_order.index(category)
            except ValueError:
                return len(self.priority_order)
        
        return sorted(plan_data, key=get_priority)
    
    def create_gantt_chart_from_schedule(self, schedule):
        """일정에서 Gantt Chart 생성"""
        
        if not schedule:
            return go.Figure()
        
        # 데이터 준비
        df_data = []
        for item in schedule:
            df_data.append({
                'Task': item['test_name'],
                'Start': f"Day {item['start_day']}",
                'Finish': f"Day {item['end_day']}",
                'Resource': item['category']
            })
        
        df = pd.DataFrame(df_data)
        
        # Gantt Chart 생성
        fig = ff.create_gantt(
            df,
            index_col='Resource',
            show_colorbar=True,
            group_tasks=True,
            showgrid_x=True,
            showgrid_y=True,
            title='시험 일정 (D-Day 기준)'
        )
        
        fig.update_layout(
            xaxis_title='일정 (Days)',
            yaxis_title='시험 항목',
            height=600,
            font=dict(size=10)
        )
        
        return fig
    
    @staticmethod
    def create_gantt_chart(requests):
        """의뢰 목록에서 Gantt Chart 생성"""
        
        if requests.empty:
            return go.Figure()
        
        # 간단한 Gantt Chart (실제로는 더 복잡한 로직 필요)
        fig = go.Figure()
        
        for idx, request in requests.iterrows():
            fig.add_trace(go.Bar(
                name=request['project'],
                x=[30],  # 임시 기간
                y=[request['project']],
                orientation='h'
            ))
        
        fig.update_layout(
            title='전체 시험 일정',
            xaxis_title='기간 (days)',
            yaxis_title='프로젝트',
            height=400
        )
        
        return fig
    
    @staticmethod
    def create_gantt_chart_from_items(test_items):
        """시험 항목에서 Gantt Chart 생성"""
        
        if test_items.empty:
            return go.Figure()
        
        fig = go.Figure()
        
        current_day = 0
        for idx, item in test_items.iterrows():
            duration = int(item.get('test_duration', 1)) if item.get('test_duration') else 1
            
            fig.add_trace(go.Bar(
                name=item['test_name'],
                x=[duration],
                y=[item['test_name']],
                orientation='h',
                text=f"{duration} days",
                textposition='inside'
            ))
            
            current_day += duration
        
        fig.update_layout(
            title='시험 항목 일정',
            xaxis_title='기간 (days)',
            yaxis_title='시험 항목',
            height=500,
            showlegend=False
        )
        
        return fig
