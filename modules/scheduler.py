import pandas as pd
import plotly.figure_factory as ff
from datetime import datetime, timedelta
import plotly.graph_objects as go

class SchedulerManager:
    def __init__(self):
        self.default_duration = 5  # 기본 시험 기간 (days)
    
    def calculate_schedule(self, test_items_df):
        """시험 일정 계산"""
        
        schedule = []
        current_day = 0
        
        for idx, item in test_items_df.iterrows():
            # 시험 기간 추출
            duration_str = str(item.get('시험 기간', ''))
            
            try:
                # 숫자만 추출
                duration = int(''.join(filter(str.isdigit, duration_str))) if duration_str else self.default_duration
                if duration == 0:
                    duration = self.default_duration
            except:
                duration = self.default_duration
            
            start_day = current_day
            end_day = current_day + duration
            
            schedule.append({
                '시험명': item.get('시험명', ''),
                '분류': item.get('분류', ''),
                '시작일 (D+)': f"D+{start_day}",
                '종료일 (D+)': f"D+{end_day}",
                '소요일수': duration,
                '시작 날짜': (datetime.now() + timedelta(days=start_day)).strftime('%Y-%m-%d'),
                '종료 날짜': (datetime.now() + timedelta(days=end_day)).strftime('%Y-%m-%d')
            })
            
            current_day = end_day
        
        return pd.DataFrame(schedule)
    
    def create_gantt_chart(self, test_items_df):
        """Gantt 차트 생성"""
        
        schedule_df = self.calculate_schedule(test_items_df)
        
        # Plotly Gantt Chart용 데이터 변환
        gantt_data = []
        
        for idx, row in schedule_df.iterrows():
            gantt_data.append(dict(
                Task=row['시험명'],
                Start=row['시작 날짜'],
                Finish=row['종료 날짜'],
                Resource=row['분류']
            ))
        
        # 색상 매핑
        colors = {
            'Environmental Tests': 'rgb(46, 137, 205)',
            'Mechanical Tests': 'rgb(114, 44, 121)',
            'Electrical Tests': 'rgb(198, 47, 105)',
            'Performance Tests': 'rgb(58, 149, 136)',
            'Operational and Environmental tests': 'rgb(107, 127, 135)'
        }
        
        # Gantt 차트 생성
        fig = ff.create_gantt(
            gantt_data,
            colors=colors,
            index_col='Resource',
            show_colorbar=True,
            group_tasks=True,
            showgrid_x=True,
            showgrid_y=True,
            title='시험 일정 Gantt Chart'
        )
        
        fig.update_layout(
            xaxis_title="날짜",
            yaxis_title="시험 항목",
            height=max(400, len(gantt_data) * 40),
            font=dict(size=12)
        )
        
        return fig
