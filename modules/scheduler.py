import pandas as pd
import plotly.figure_factory as ff
import plotly.graph_objects as go
from datetime import datetime, timedelta
from modules.utils import parse_duration


class SchedulerManager:
    """시험 계획 및 스케줄링 모듈"""
    
    def __init__(self):
        # 시험 우선순위 정의 (낮을수록 우선)
        self.priority_map = {
            "Electrical Tests": 1,
            "Performance Tests": 2,
            "Operational and Environmental tests": 3,
            "Endurance Test": 4,
            "default": 5
        }
    
    def sort_by_priority(self, test_items):
        """시험 항목을 우선순위에 따라 정렬"""
        def get_priority(item):
            category = item.get('category', '')
            return self.priority_map.get(category, self.priority_map['default'])
        
        return sorted(test_items, key=get_priority)
    
    def create_gantt_chart(self, test_items, start_date):
        """Gantt 차트 생성"""
        try:
            # 우선순위에 따라 정렬
            sorted_items = self.sort_by_priority(test_items)
            
            # Gantt 차트 데이터 준비
            gantt_data = []
            current_date = start_date
            
            for idx, item in enumerate(sorted_items):
                test_name = item.get('test_name', f'Test {idx+1}')
                duration = parse_duration(item.get('test_duration', '1'))
                
                end_date = current_date + timedelta(days=duration)
                
                gantt_data.append({
                    'Task': test_name,
                    'Start': current_date,
                    'Finish': end_date,
                    'Resource': item.get('category', 'N/A')
                })
                
                current_date = end_date
            
            # DataFrame 생성
            df = pd.DataFrame(gantt_data)
            
            # Plotly Gantt 차트 생성
            colors = {
                'Electrical Tests': 'rgb(220, 0, 0)',
                'Performance Tests': 'rgb(0, 128, 255)',
                'Operational and Environmental tests': 'rgb(0, 200, 0)',
                'Endurance Test': 'rgb(255, 140, 0)',
                'N/A': 'rgb(128, 128, 128)'
            }
            
            fig = ff.create_gantt(
                df,
                colors=colors,
                index_col='Resource',
                show_colorbar=True,
                group_tasks=True,
                showgrid_x=True,
                showgrid_y=True,
                title='시험 일정 Gantt Chart'
            )
            
            # 레이아웃 업데이트
            fig.update_layout(
                xaxis_title="날짜",
                yaxis_title="시험 항목",
                height=max(400, len(gantt_data) * 40),
                font=dict(size=10)
            )
            
            return fig
        
        except Exception as e:
            print(f"Gantt 차트 생성 실패: {str(e)}")
            return None
    
    def create_schedule_summary(self, test_items, start_date):
        """일정 요약 테이블 생성"""
        try:
            sorted_items = self.sort_by_priority(test_items)
            
            summary_data = []
            current_date = start_date
            day_counter = 0
            
            for idx, item in enumerate(sorted_items):
                test_name = item.get('test_name', f'Test {idx+1}')
                duration = parse_duration(item.get('test_duration', '1'))
                category = item.get('category', 'N/A')
                equipment = item.get('test_equipment', 'N/A')
                sample_count = item.get('sample_count', 'N/A')
                
                end_date = current_date + timedelta(days=duration)
                
                summary_data.append({
                    '순번': idx + 1,
                    '시험명': test_name,
                    '분류': category,
                    '시작일': f'D+{day_counter} ({current_date.strftime("%Y-%m-%d")})',
                    '종료일': f'D+{day_counter + duration} ({end_date.strftime("%Y-%m-%d")})',
                    '소요일수': duration,
                    '시료수': sample_count,
                    '시험장비': equipment
                })
                
                current_date = end_date
                day_counter += duration
            
            return pd.DataFrame(summary_data)
        
        except Exception as e:
            print(f"일정 요약 생성 실패: {str(e)}")
            return pd.DataFrame()
    
    def calculate_total_duration(self, test_items):
        """전체 시험 소요 시간 계산"""
        total_days = 0
        for item in test_items:
            duration = parse_duration(item.get('test_duration', '1'))
            total_days += duration
        
        return total_days
    
    def create_flowchart_data(self, test_items):
        """Flowchart 데이터 생성 (Graphviz용)"""
        try:
            sorted_items = self.sort_by_priority(test_items)
            
            # Graphviz DOT 형식
            dot_string = "digraph TestFlow {\n"
            dot_string += "  rankdir=TB;\n"
            dot_string += "  node [shape=box, style=rounded];\n\n"
            
            # 시작 노드
            dot_string += '  start [label="시작", shape=ellipse, fillcolor=lightgreen, style=filled];\n'
            
            # 시험 노드
            prev_node = "start"
            for idx, item in enumerate(sorted_items):
                node_name = f"test{idx}"
                test_name = item.get('test_name', f'Test {idx+1}')
                duration = item.get('test_duration', 'N/A')
                
                # 노드 생성
                dot_string += f'  {node_name} [label="{test_name}\\n({duration}일)"];\n'
                
                # 엣지 생성
                dot_string += f'  {prev_node} -> {node_name};\n'
                
                prev_node = node_name
            
            # 종료 노드
            dot_string += '  end [label="종료", shape=ellipse, fillcolor=lightcoral, style=filled];\n'
            dot_string += f'  {prev_node} -> end;\n'
            
            dot_string += "}\n"
            
            return dot_string
        
        except Exception as e:
            print(f"Flowchart 데이터 생성 실패: {str(e)}")
            return None
