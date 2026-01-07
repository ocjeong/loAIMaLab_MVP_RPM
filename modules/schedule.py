import plotly.figure_factory as ff
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import List, Dict, Any
import pandas as pd


class ScheduleManager:
    """일정 관리 클래스"""
    
    def __init__(self):
        # 시험 우선순위 정의
        self.priority_order = [
            'Functional Test',
            'Environmental Test',
            'Mechanical Test',
            'Electrical Tests',
            'Performance Test',
            'Endurance Test'
        ]
    
    def generate_schedule(self, test_items: List[Dict[str, Any]], request_id: str) -> List[Dict[str, Any]]:
        """
        시험 항목 리스트에서 일정 생성
        
        Args:
            test_items: 시험 항목 리스트
            request_id: 의뢰 ID
            
        Returns:
            일정 리스트
        """
        schedules = []
        current_day = 0
        
        # 우선순위에 따라 정렬
        sorted_items = self._sort_by_priority(test_items)
        
        for item in sorted_items:
            # 시험 기간 가져오기 (기본값: 3일)
            duration = self._parse_duration(item.get('test_duration', '3'))
            
            schedule = {
                'test_name': item.get('test_name', 'Unknown Test'),
                'category': item.get('category', 'Other'),
                'start_day': current_day,
                'end_day': current_day + duration,
                'duration': duration,
                'request_id': request_id,
                'test_sample_no': item.get('test_sample_no', ''),
                'sample_count': item.get('sample_count', ''),
                'test_equipment': item.get('test_equipment', '')
            }
            
            schedules.append(schedule)
            current_day += duration
        
        return schedules
    
    def _sort_by_priority(self, test_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """우선순위에 따라 시험 항목 정렬"""
        def get_priority(item):
            category = item.get('category', 'Other')
            try:
                return self.priority_order.index(category)
            except ValueError:
                return len(self.priority_order)
        
        return sorted(test_items, key=get_priority)
    
    def _parse_duration(self, duration_str: str) -> int:
        """시험 기간 문자열을 일수로 변환"""
        try:
            # 숫자만 추출
            duration = int(''.join(filter(str.isdigit, str(duration_str))))
            return max(duration, 1)  # 최소 1일
        except:
            return 3  # 기본값
    
    def create_gantt_chart(self, schedules: List[Dict[str, Any]], use_dday: bool = False):
        """
        Gantt Chart 생성
        
        Args:
            schedules: 일정 리스트
            use_dday: D-day 형식 사용 여부
            
        Returns:
            Plotly Figure 객체
        """
        if not schedules:
            # 빈 차트 반환
            fig = go.Figure()
            fig.update_layout(
                title="일정이 없습니다",
                xaxis_title="날짜",
                yaxis_title="시험 항목"
            )
            return fig
        
        # 데이터 준비
        df_data = []
        
        if use_dday:
            # D-day 형식
            base_date = datetime.now()
            
            for schedule in schedules:
                start_date = base_date + timedelta(days=schedule['start_day'])
                end_date = base_date + timedelta(days=schedule['end_day'])
                
                df_data.append({
                    'Task': f"{schedule['test_name']} (D+{schedule['start_day']}~D+{schedule['end_day']})",
                    'Start': start_date,
                    'Finish': end_date,
                    'Resource': schedule.get('category', 'Other')
                })
        else:
            # 날짜 형식
            for schedule in schedules:
                if 'start_date' in schedule and 'end_date' in schedule:
                    df_data.append({
                        'Task': schedule['test_name'],
                        'Start': schedule['start_date'],
                        'Finish': schedule['end_date'],
                        'Resource': schedule.get('category', 'Other')
                    })
        
        if not df_data:
            fig = go.Figure()
            fig.update_layout(
                title="일정 데이터가 올바르지 않습니다",
                xaxis_title="날짜",
                yaxis_title="시험 항목"
            )
            return fig
        
        df = pd.DataFrame(df_data)
        
        # 색상 매핑
        colors = {
            'Functional Test': 'rgb(220, 0, 0)',
            'Environmental Test': 'rgb(0, 150, 200)',
            'Mechanical Test': 'rgb(100, 200, 100)',
            'Electrical Tests': 'rgb(255, 140, 0)',
            'Performance Test': 'rgb(150, 100, 200)',
            'Endurance Test': 'rgb(200, 150, 100)',
            'Other': 'rgb(128, 128, 128)'
        }
        
        # Gantt Chart 생성
        fig = ff.create_gantt(
            df,
            colors=colors,
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
            height=max(400, len(schedules) * 40),
            font=dict(size=10)
        )
        
        return fig
    
    def calculate_total_duration(self, schedules: List[Dict[str, Any]]) -> int:
        """전체 시험 기간 계산"""
        if not schedules:
            return 0
        
        return max(schedule['end_day'] for schedule in schedules)
    
    def get_schedule_summary(self, schedules: List[Dict[str, Any]]) -> Dict[str, Any]:
        """일정 요약 정보"""
        if not schedules:
            return {
                'total_tests': 0,
                'total_duration': 0,
                'categories': {}
            }
        
        categories = {}
        for schedule in schedules:
            category = schedule.get('category', 'Other')
            if category not in categories:
                categories[category] = 0
            categories[category] += 1
        
        return {
            'total_tests': len(schedules),
            'total_duration': self.calculate_total_duration(schedules),
            'categories': categories
        }
