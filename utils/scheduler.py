import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

class SchedulerManager:
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    def create_user_gantt_chart(self, user_id):
        """사용자의 전체 시험 일정을 Gantt 차트로 생성"""
        try:
            # 사용자의 모든 의뢰 조회
            requests_df = self.db_manager.get_user_requests(user_id)
            
            if requests_df.empty:
                return None
            
            # 각 의뢰의 시험 항목 수집
            all_items = []
            for _, request in requests_df.iterrows():
                test_items = self.db_manager.get_test_items_by_request(request['id'])
                
                for _, item in test_items.iterrows():
                    all_items.append({
                        'Task': item['test_name'],
                        'Request': request['project'],
                        'Duration': int(item['test_duration']) if item['test_duration'] else 1
                    })
            
            if not all_items:
                return None
            
            # 시작 날짜 계산
            start_date = datetime.now()
            gantt_data = []
            current_date = start_date
            
            for item in all_items:
                end_date = current_date + timedelta(days=item['Duration'])
                gantt_data.append({
                    'Task': item['Task'],
                    'Start': current_date,
                    'Finish': end_date,
                    'Request': item['Request']
                })
                current_date = end_date
            
            df = pd.DataFrame(gantt_data)
            
            # Gantt 차트 생성
            fig = px.timeline(
                df,
                x_start='Start',
                x_end='Finish',
                y='Task',
                color='Request',
                title='전체 시험 일정'
            )
            
            fig.update_yaxes(autorange="reversed")
            fig.update_layout(height=400)
            
            return fig
        
        except Exception as e:
            print(f"Gantt Chart Error: {str(e)}")
            return None
    
    def create_request_gantt_chart(self, request_id):
        """특정 의뢰의 시험 일정을 Gantt 차트로 생성"""
        try:
            test_items = self.db_manager.get_test_items_by_request(request_id)
            
            if test_items.empty:
                return None
            
            start_date = datetime.now()
            gantt_data = []
            current_date = start_date
            
            for _, item in test_items.iterrows():
                duration = int(item['test_duration']) if item['test_duration'] else 1
                end_date = current_date + timedelta(days=duration)
                
                gantt_data.append({
                    'Task': item['test_name'],
                    'Start': current_date,
                    'Finish': end_date,
                    'Category': item['category']
                })
                current_date = end_date
            
            df = pd.DataFrame(gantt_data)
            
            fig = px.timeline(
                df,
                x_start='Start',
                x_end='Finish',
                y='Task',
                color='Category',
                title=f'의뢰 {request_id} 시험 일정'
            )
            
            fig.update_yaxes(autorange="reversed")
            fig.update_layout(height=300)
            
            return fig
        
        except Exception as e:
            print(f"Request Gantt Error: {str(e)}")
            return None
    
    def create_timeline_chart(self, plan_df, request_id):
        """계획서 데이터를 기반으로 D-Day 타임라인 생성"""
        try:
            gantt_data = []
            current_day = 0
            
            for _, row in plan_df.iterrows():
                duration = int(row['시험 기간(일)']) if row['시험 기간(일)'] else 1
                
                gantt_data.append({
                    'Task': row['시험명'],
                    'Start': current_day,
                    'Finish': current_day + duration,
                    'Category': row['분류']
                })
                current_day += duration
            
            df = pd.DataFrame(gantt_data)
            
            # Plotly Figure 생성
            fig = go.Figure()
            
            colors = px.colors.qualitative.Plotly
            categories = df['Category'].unique()
            color_map = {cat: colors[i % len(colors)] for i, cat in enumerate(categories)}
            
            for _, row in df.iterrows():
                fig.add_trace(go.Bar(
                    x=[row['Finish'] - row['Start']],
                    y=[row['Task']],
                    orientation='h',
                    base=row['Start'],
                    name=row['Category'],
                    marker=dict(color=color_map[row['Category']]),
                    text=f"D+{row['Start']} ~ D+{row['Finish']}",
                    textposition='inside',
                    showlegend=True
                ))
            
            fig.update_layout(
                title='시험 타임라인 (D-Day)',
                xaxis_title='Day',
                yaxis_title='시험 항목',
                barmode='overlay',
                height=500,
                yaxis=dict(autorange="reversed")
            )
            
            return fig
        
        except Exception as e:
            print(f"Timeline Error: {str(e)}")
            return None
    
    def save_schedule(self, user_id, request_id, schedule_data):
        """일정 데이터를 데이터베이스에 저장"""
        # 이미 Request와 Test Item에 저장되어 있으므로
        # 추가 작업이 필요하면 여기에 구현
        pass
