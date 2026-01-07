from datetime import datetime, timedelta
import pandas as pd
from modules.data_manager import DataManager

class Scheduler:
    def __init__(self):
        self.dm = DataManager()
    
    def calculate_duration(self, test_item):
        """시험 소요 기간 계산"""
        duration_str = test_item.get('test_duration', '1')
        
        try:
            # 숫자만 추출
            duration = int(''.join(filter(str.isdigit, str(duration_str))))
            if duration == 0:
                duration = 1
        except:
            duration = 1
        
        return duration
    
    def create_dday_schedule(self, test_items):
        """D-day 기반 스케줄 생성"""
        # 시험 항목을 소요 시간 기준으로 정렬 (오래 걸리는 것부터)
        sorted_items = sorted(
            test_items,
            key=lambda x: self.calculate_duration(x),
            reverse=True
        )
        
        # 병렬 처리를 위한 트랙 (최대 2개)
        track1 = []
        track2 = []
        track1_end = 0
        track2_end = 0
        
        schedules = []
        
        for item in sorted_items:
            duration = self.calculate_duration(item)
            
            # 더 빨리 끝나는 트랙에 배치
            if track1_end <= track2_end:
                start_day = track1_end
                end_day = start_day + duration
                track1.append(item)
                track1_end = end_day
            else:
                start_day = track2_end
                end_day = start_day + duration
                track2.append(item)
                track2_end = end_day
            
            schedules.append({
                'test_item_id': item.get('id', ''),
                'test_name': item.get('test_name', ''),
                'start_day': start_day,
                'end_day': end_day,
                'duration': duration,
                'status': 'planned'
            })
        
        return schedules
    
    def convert_to_date_schedule(self, dday_schedules, start_date):
        """D-day 스케줄을 실제 날짜로 변환"""
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        
        date_schedules = []
        for schedule in dday_schedules:
            start_day = schedule['start_day']
            end_day = schedule['end_day']
            
            actual_start = start_dt + timedelta(days=start_day)
            actual_end = start_dt + timedelta(days=end_day - 1)  # 종료일은 포함
            
            date_schedules.append({
                'test_item_id': schedule['test_item_id'],
                'start_date': actual_start.strftime('%Y-%m-%d'),
                'end_date': actual_end.strftime('%Y-%m-%d'),
                'start_day': start_day,
                'end_day': end_day,
                'duration': schedule['duration'],
                'status': schedule['status']
            })
        
        return date_schedules
    
    def get_default_start_date(self, user_id):
        """사용자의 기본 시작일 계산"""
        schedules = self.dm.get_user_schedules(user_id)
        
        if schedules.empty:
            return datetime.now().strftime('%Y-%m-%d')
        
        # 가장 늦은 종료일 찾기
        max_end_date = schedules['end_date'].max()
        
        try:
            end_dt = datetime.strptime(max_end_date, '%Y-%m-%d')
            next_start = end_dt + timedelta(days=1)
            return next_start.strftime('%Y-%m-%d')
        except:
            return datetime.now().strftime('%Y-%m-%d')
