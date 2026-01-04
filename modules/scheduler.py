import plotly.figure_factory as ff
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta

class Scheduler:
    """스케줄링 클래스"""
    
    def __init__(self, data_manager):
        self.data_manager = data_manager
    
    def create_gantt_chart(self, user_id, request_id=None):
        """Gantt Chart 생성"""
        try:
            # 시험 항목 데이터 로드
            test_items_df = self.data_manager.load_test_item_data()
            requests_df = self.data_manager.load_request_info_data()
            
            # 사용자의 의뢰 필터링
            user_requests = requests_df[requests_df['user_id'] == user_id]
            
            if request_id:
                # 특정 의뢰의 항목만
                test_items = test_items_df[test_items_df['request_id'] == request_id]
            else:
                # 사용자의 모든 의뢰 항목
                test_items = test_items_df[test_items_df['request_id'].isin(user_requests['id'])]
            
            if test_items.empty:
                return None
            
            # Gantt Chart 데이터 준비
            tasks = []
            start_date = datetime.now()
            current_date = start_date
            
            for idx, row in test_items.iterrows():
                try:
                    duration = int(row.get('test_duration', 1))
                except:
                    duration = 1
                
                end_date = current_date + timedelta(days=duration)
                
                tasks.append(dict(
                    Task=row.get('test_name', 'Unknown'),
                    Start=current_date.strftime('%Y-%m-%d'),
                    Finish=end_date.strftime('%Y-%m-%d'),
                    Resource=row.get('category', 'N/A')
                ))
                
                current_date = end_date
            
            # Gantt Chart 생성
            fig = ff.create_gantt(
                tasks,
                index_col='Resource',
                show_colorbar=True,
                group_tasks=True,
                showgrid_x=True,
                showgrid_y=True
            )
            
            fig.update_layout(
                title="시험 일정",
                xaxis_title="날짜",
                yaxis_title="시험 항목",
                height=400
            )
            
            return fig
            
        except Exception as e:
            print(f"Error creating Gantt chart: {e}")
            return None
    
    def create_timeline_chart(self, test_items_df):
        """타임라인 Chart 생성 (D-Day 기준)"""
        try:
            if test_items_df.empty:
                return None
            
            # D-Day 기반 타임라인
            tasks = []
            current_day = 0
            
            for idx, row in test_items_df.iterrows():
                try:
                    duration = int(row.get('test_duration', 1))
                except:
                    duration = 1
                
                tasks.append(dict(
                    Task=row.get('test_name', 'Unknown'),
                    Start=f"Day {current_day}",
                    Finish=f"Day {current_day + duration}",
                    Resource=row.get('category', 'N/A'),
                    Duration=duration
                ))
                
                current_day += duration
            
            # 간단한 바 차트로 표현
            fig = go.Figure()
            
            y_pos = 0
            colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8']
            
            for i, task in enumerate(tasks):
                start = int(task['Start'].split()[1])
                duration = task['Duration']
                
                fig.add_trace(go.Bar(
                    name=task['Task'],
                    x=[duration],
                    y=[task['Task']],
                    orientation='h',
                    marker=dict(color=colors[i % len(colors)]),
                    text=f"D+{start} ~ D+{start+duration} ({duration}일)",
                    textposition='auto',
                    base=start
                ))
            
            fig.update_layout(
                title="시험 타임라인 (D-Day)",
                xaxis_title="Day",
                yaxis_title="시험 항목",
                barmode='overlay',
                height=400,
                showlegend=False
            )
            
            return fig
            
        except Exception as e:
            print(f"Error creating timeline chart: {e}")
            return None
    
    def save_schedule(self, user_id, request_id, test_items_df):
        """일정 저장"""
        try:
            # 이미 Request Info와 Test Item에 저장되어 있으므로
            # 추가 저장 로직이 필요하면 여기에 구현
            return True
        except Exception as e:
            print(f"Error saving schedule: {e}")
            return False
