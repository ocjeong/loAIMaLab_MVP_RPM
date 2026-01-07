import plotly.figure_factory as ff
import pandas as pd
from datetime import datetime, timedelta

class SchedulerManager:
    def __init__(self):
        self.default_duration = 5  # 기본 시험 기간 (days)
    
    def create_gantt_chart(self, test_items_df, start_day=0):
        """Gantt Chart 생성"""
        if test_items_df.empty:
            return None
        
        # 시작 날짜 설정 (D-0)
        start_date = datetime.now()
        
        tasks = []
        current_date = start_date
        
        for idx, row in test_items_df.iterrows():
            test_name = row.get('test_name', f'Test {idx+1}')
            
            # 시험 기간 파싱
            duration = self._parse_duration(row.get('test_duration', ''))
            if duration == 0:
                duration = self.default_duration
            
            end_date = current_date + timedelta(days=duration)
            
            tasks.append(dict(
                Task=test_name,
                Start=current_date.strftime('%Y-%m-%d'),
                Finish=end_date.strftime('%Y-%m-%d'),
                Resource=row.get('category', 'General')
            ))
            
            current_date = end_date
        
        if not tasks:
            return None
        
        # Gantt Chart 생성
        fig = ff.create_gantt(
            tasks,
            index_col='Resource',
            show_colorbar=True,
            group_tasks=True,
            showgrid_x=True,
            showgrid_y=True,
            title='시험 일정 (Gantt Chart)'
        )
        
        fig.update_layout(
            xaxis_title="날짜",
            yaxis_title="시험 항목",
            height=max(400, len(tasks) * 40)
        )
        
        return fig
    
    def _parse_duration(self, duration_str):
        """시험 기간 문자열을 일수로 변환"""
        if not duration_str or duration_str == '':
            return 0
        
        try:
            # 숫자만 추출
            duration = float(''.join(filter(str.isdigit, str(duration_str))))
            return int(duration) if duration > 0 else 0
        except:
            return 0
