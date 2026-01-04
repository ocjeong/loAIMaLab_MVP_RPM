import pandas as pd
import plotly.figure_factory as ff
import plotly.graph_objects as go
from datetime import datetime, timedelta

class Scheduler:
    def create_gantt_chart(self, plan_df, start_date):
        """Gantt Chart 생성"""
        try:
            tasks = []
            current_date = pd.to_datetime(start_date)
            
            for idx, row in plan_df.iterrows():
                # 소요일수 파싱
                try:
                    duration = int(str(row['소요일수']).replace('days', '').strip())
                except:
                    duration = 1
                
                end_date = current_date + timedelta(days=duration)
                
                task = dict(
                    Task=row['시험명'],
                    Start=current_date.strftime('%Y-%m-%d'),
                    Finish=end_date.strftime('%Y-%m-%d'),
                    Resource=row['분류']
                )
                tasks.append(task)
                
                # 다음 시험은 현재 시험 종료 후 시작
                current_date = end_date
            
            if tasks:
                fig = ff.create_gantt(
                    tasks,
                    index_col='Resource',
                    show_colorbar=True,
                    group_tasks=True,
                    showgrid_x=True,
                    showgrid_y=True,
                    title='시험 일정 Gantt Chart'
                )
                
                fig.update_layout(
                    height=400,
                    xaxis_title="날짜",
                    yaxis_title="시험 항목",
                    font=dict(size=10)
                )
                
                return fig
            else:
                return None
        except Exception as e:
            print(f"Error creating Gantt chart: {e}")
            return None
    
    def create_schedule_table(self, plan_df, start_date):
        """일정 테이블 생성"""
        try:
            schedule_data = []
            current_date = pd.to_datetime(start_date)
            day_counter = 0
            
            for idx, row in plan_df.iterrows():
                # 소요일수 파싱
                try:
                    duration = int(str(row['소요일수']).replace('days', '').strip())
                except:
                    duration = 1
                
                end_date = current_date + timedelta(days=duration)
                
                schedule_row = {
                    '순번': row['순번'],
                    '시험명': row['시험명'],
                    '분류': row['분류'],
                    '시작일': current_date.strftime('%Y-%m-%d'),
                    '종료일': end_date.strftime('%Y-%m-%d'),
                    '시작 D-Day': f"D+{day_counter}",
                    '종료 D-Day': f"D+{day_counter + duration}",
                    '소요일수': duration,
                    '시료수': row['시료수'],
                    '시험장비': row['시험장비']
                }
                schedule_data.append(schedule_row)
                
                # 다음 시험은 현재 시험 종료 후 시작
                current_date = end_date
                day_counter += duration
            
            return pd.DataFrame(schedule_data)
        except Exception as e:
            print(f"Error creating schedule table: {e}")
            return None
