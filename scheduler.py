import pandas as pd
from datetime import datetime, timedelta
from config import MAX_PARALLEL_TESTS, DEFAULT_TEST_DURATION

class Scheduler:
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    def create_schedule(self, test_items):
        """시험 일정 생성 (D-day 기준)"""
        # 소요 시간 기준으로 정렬 (긴 것부터)
        sorted_items = sorted(
            test_items,
            key=lambda x: int(x.get('test_duration', DEFAULT_TEST_DURATION)) if str(x.get('test_duration', '')).isdigit() else DEFAULT_TEST_DURATION,
            reverse=True
        )
        
        # 병렬 처리를 위한 트랙
        tracks = [{'end_day': 0, 'items': []} for _ in range(MAX_PARALLEL_TESTS)]
        
        schedule = []
        
        for item in sorted_items:
            # 가장 빨리 끝나는 트랙 찾기
            earliest_track = min(tracks, key=lambda x: x['end_day'])
            
            duration = int(item.get('test_duration', DEFAULT_TEST_DURATION)) if str(item.get('test_duration', '')).isdigit() else DEFAULT_TEST_DURATION
            start_day = earliest_track['end_day']
            end_day = start_day + duration
            
            schedule_item = {
                'test_item': item,
                'start_day': start_day,
                'end_day': end_day,
                'duration': duration
            }
            
            schedule.append(schedule_item)
            earliest_track['end_day'] = end_day
            earliest_track['items'].append(schedule_item)
        
        return schedule
    
    def convert_to_dates(self, schedule, start_date):
        """D-day를 실제 날짜로 변환"""
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        
        dated_schedule = []
        for item in schedule:
            dated_item = item.copy()
            dated_item['start_date'] = (start_date + timedelta(days=item['start_day'])).strftime('%Y-%m-%d')
            dated_item['end_date'] = (start_date + timedelta(days=item['end_day'])).strftime('%Y-%m-%d')
            dated_schedule.append(dated_item)
        
        return dated_schedule
    
    def save_schedule(self, schedule, test_item_ids):
        """일정을 데이터베이스에 저장"""
        schedule_items = []
        
        for idx, item in enumerate(schedule):
            schedule_item = {
                'test_item_id': test_item_ids[idx] if idx < len(test_item_ids) else '',
                'start_date': item['start_date'],
                'end_date': item['end_date'],
                'start_day': item['start_day'],
                'end_day': item['end_day'],
                'duration': item['duration'],
                'status': 'planned'
            }
            schedule_items.append(schedule_item)
        
        self.db_manager.add_schedule_items(schedule_items)
