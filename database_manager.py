import pandas as pd
import os
import json
from datetime import datetime
from config import *

class DatabaseManager:
    def __init__(self):
        self.ensure_db_directory()
        self.initialize_databases()
    
    def ensure_db_directory(self):
        """데이터베이스 디렉토리 생성"""
        if not os.path.exists(DB_PATH):
            os.makedirs(DB_PATH)
    
    def initialize_databases(self):
        """데이터베이스 파일 초기화"""
        # User List
        if not os.path.exists(USER_LIST_FILE):
            df = pd.DataFrame(columns=['id', 'user_name', 'created_date', 'last_access'])
            df.to_csv(USER_LIST_FILE, index=False, encoding='utf-8-sig')
        
        # Master Test
        if not os.path.exists(MASTER_TEST_FILE):
            df = pd.DataFrame(columns=['id', 'std_name', 'std_category', 'aliases', 'ref_standard'])
            # 초기 마스터 데이터
            initial_data = [
                {
                    'id': 'M001',
                    'std_name': 'High Temperature Test',
                    'std_category': 'Operational and Environmental tests',
                    'aliases': json.dumps(['고온 시험', '고온 내구', 'High Temp'], ensure_ascii=False),
                    'ref_standard': 'ISO 16750-3'
                },
                {
                    'id': 'M002',
                    'std_name': 'Low Temperature Test',
                    'std_category': 'Operational and Environmental tests',
                    'aliases': json.dumps(['저온 시험', '저온 내구', 'Low Temp'], ensure_ascii=False),
                    'ref_standard': 'ISO 16750-3'
                },
                {
                    'id': 'M003',
                    'std_name': 'Noise Test',
                    'std_category': 'Operational and Environmental tests',
                    'aliases': json.dumps(['소음 시험', '소음 측정', 'Noise'], ensure_ascii=False),
                    'ref_standard': ''
                },
                {
                    'id': 'M004',
                    'std_name': 'Random Vibration Test',
                    'std_category': 'Operational and Environmental tests',
                    'aliases': json.dumps(['랜덤 진동', '진동 시험', 'Vibration'], ensure_ascii=False),
                    'ref_standard': 'ISO 16750-3'
                },
                {
                    'id': 'M005',
                    'std_name': 'Dust Protection Test',
                    'std_category': 'Operational and Environmental tests',
                    'aliases': json.dumps(['방진 시험', '분진 보호'], ensure_ascii=False),
                    'ref_standard': 'ISO 20653'
                },
                {
                    'id': 'M006',
                    'std_name': 'Water Protection Test',
                    'std_category': 'Operational and Environmental tests',
                    'aliases': json.dumps(['방수 시험', '침수 시험'], ensure_ascii=False),
                    'ref_standard': 'ISO 20653'
                },
                {
                    'id': 'M007',
                    'std_name': 'Voltage Drop Test',
                    'std_category': 'Electrical Tests',
                    'aliases': json.dumps(['전압 강하', 'Voltage Drop'], ensure_ascii=False),
                    'ref_standard': 'ISO 16750-3'
                },
                {
                    'id': 'M008',
                    'std_name': 'Reverse Polarity Test',
                    'std_category': 'Electrical Tests',
                    'aliases': json.dumps(['역극성', '극성 반전'], ensure_ascii=False),
                    'ref_standard': 'ISO 16750-3'
                },
                {
                    'id': 'M009',
                    'std_name': 'Undervoltage and Overvoltage Test',
                    'std_category': 'Electrical Tests',
                    'aliases': json.dumps(['과저전압', '정지 전압 확인'], ensure_ascii=False),
                    'ref_standard': 'ISO 16750-3'
                },
                {
                    'id': 'M010',
                    'std_name': 'On & Off Test',
                    'std_category': 'Endurance Test',
                    'aliases': json.dumps(['작동성 시험', '온오프'], ensure_ascii=False),
                    'ref_standard': ''
                },
                {
                    'id': 'M011',
                    'std_name': 'Functional Test',
                    'std_category': 'Functional Test',
                    'aliases': json.dumps(['기능 시험', '기능성 테스트'], ensure_ascii=False),
                    'ref_standard': ''
                }
            ]
            df = pd.DataFrame(initial_data)
            df.to_csv(MASTER_TEST_FILE, index=False, encoding='utf-8-sig')
        
        # Request Info
        if not os.path.exists(REQUEST_INFO_FILE):
            df = pd.DataFrame(columns=['id', 'user_id', 'extracted_data', 'final_data', 
                                      'is_verified', 'client', 'project'])
            df.to_csv(REQUEST_INFO_FILE, index=False, encoding='utf-8-sig')
        
        # Test Item
        if not os.path.exists(TEST_ITEM_FILE):
            df = pd.DataFrame(columns=['id', 'test_name', 'test_name_original', 'category', 
                                      'category_original', 'ref_standard', 'sample_assembly',
                                      'test_sample_no', 'sample_count', 'test_duration',
                                      'test_equipment', 'test_master_id', 'custom_specs', 'request_id'])
            df.to_csv(TEST_ITEM_FILE, index=False, encoding='utf-8-sig')
        
        # Schedule Item
        if not os.path.exists(SCHEDULE_ITEM_FILE):
            df = pd.DataFrame(columns=['test_item_id', 'start_date', 'end_date', 
                                      'start_day', 'end_day', 'duration', 'status'])
            df.to_csv(SCHEDULE_ITEM_FILE, index=False, encoding='utf-8-sig')
    
    # User List 관련
    def get_all_users(self):
        """모든 사용자 조회"""
        df = pd.read_csv(USER_LIST_FILE, encoding='utf-8-sig')
        return df
    
    def add_user(self, user_name):
        """사용자 추가"""
        df = pd.read_csv(USER_LIST_FILE, encoding='utf-8-sig')
        new_id = f"U{str(len(df) + 1).zfill(3)}"
        new_user = {
            'id': new_id,
            'user_name': user_name,
            'created_date': datetime.now().strftime('%Y-%m-%d'),
            'last_access': datetime.now().strftime('%Y-%m-%d')
        }
        df = pd.concat([df, pd.DataFrame([new_user])], ignore_index=True)
        df.to_csv(USER_LIST_FILE, index=False, encoding='utf-8-sig')
        return new_id
    
    def update_last_access(self, user_id):
        """마지막 접속 시간 업데이트"""
        df = pd.read_csv(USER_LIST_FILE, encoding='utf-8-sig')
        df.loc[df['id'] == user_id, 'last_access'] = datetime.now().strftime('%Y-%m-%d')
        df.to_csv(USER_LIST_FILE, index=False, encoding='utf-8-sig')
    
    # Master Test 관련
    def get_all_masters(self):
        """모든 마스터 데이터 조회"""
        df = pd.read_csv(MASTER_TEST_FILE, encoding='utf-8-sig')
        return df
    
    def get_master_by_id(self, master_id):
        """ID로 마스터 데이터 조회"""
        df = pd.read_csv(MASTER_TEST_FILE, encoding='utf-8-sig')
        master = df[df['id'] == master_id]
        if len(master) > 0:
            master_dict = master.iloc[0].to_dict()
            # aliases를 리스트로 변환
            if pd.notna(master_dict['aliases']):
                try:
                    master_dict['aliases'] = json.loads(master_dict['aliases'])
                except:
                    master_dict['aliases'] = []
            else:
                master_dict['aliases'] = []
            return master_dict
        return None
    
    def update_master_aliases(self, master_id, new_alias):
        """마스터 데이터의 유사어 업데이트"""
        df = pd.read_csv(MASTER_TEST_FILE, encoding='utf-8-sig')
        idx = df[df['id'] == master_id].index
        if len(idx) > 0:
            current_aliases = df.loc[idx[0], 'aliases']
            try:
                aliases_list = json.loads(current_aliases) if pd.notna(current_aliases) else []
            except:
                aliases_list = []
            
            if new_alias not in aliases_list:
                aliases_list.append(new_alias)
                df.loc[idx[0], 'aliases'] = json.dumps(aliases_list, ensure_ascii=False)
                df.to_csv(MASTER_TEST_FILE, index=False, encoding='utf-8-sig')
    
    def add_master(self, test_item):
        """새로운 마스터 데이터 추가"""
        df = pd.read_csv(MASTER_TEST_FILE, encoding='utf-8-sig')
        new_id = f"M{str(len(df) + 1).zfill(3)}"
        new_master = {
            'id': new_id,
            'std_name': test_item.get('test_name', ''),
            'std_category': test_item.get('category', ''),
            'aliases': json.dumps([test_item.get('test_name', '')], ensure_ascii=False),
            'ref_standard': test_item.get('ref_standard', '')
        }
        df = pd.concat([df, pd.DataFrame([new_master])], ignore_index=True)
        df.to_csv(MASTER_TEST_FILE, index=False, encoding='utf-8-sig')
        return new_id
    
    # Request Info 관련
    def get_all_requests(self, user_id=None):
        """모든 의뢰 조회 (사용자별 필터링 가능)"""
        df = pd.read_csv(REQUEST_INFO_FILE, encoding='utf-8-sig')
        if user_id:
            df = df[df['user_id'] == user_id]
        return df
    
    def add_request(self, user_id, extracted_data, client, project):
        """의뢰 추가"""
        df = pd.read_csv(REQUEST_INFO_FILE, encoding='utf-8-sig')
        new_id = f"R{str(len(df) + 1).zfill(5)}"
        new_request = {
            'id': new_id,
            'user_id': user_id,
            'extracted_data': json.dumps(extracted_data, ensure_ascii=False),
            'final_data': '',
            'is_verified': False,
            'client': client,
            'project': project
        }
        df = pd.concat([df, pd.DataFrame([new_request])], ignore_index=True)
        df.to_csv(REQUEST_INFO_FILE, index=False, encoding='utf-8-sig')
        return new_id
    
    def update_request_final_data(self, request_id, final_data):
        """의뢰의 최종 데이터 업데이트"""
        df = pd.read_csv(REQUEST_INFO_FILE, encoding='utf-8-sig')
        df.loc[df['id'] == request_id, 'final_data'] = json.dumps(final_data, ensure_ascii=False)
        df.loc[df['id'] == request_id, 'is_verified'] = True
        df.to_csv(REQUEST_INFO_FILE, index=False, encoding='utf-8-sig')
    
    def get_request_by_id(self, request_id):
        """ID로 의뢰 조회"""
        df = pd.read_csv(REQUEST_INFO_FILE, encoding='utf-8-sig')
        request = df[df['id'] == request_id]
        if len(request) > 0:
            request_dict = request.iloc[0].to_dict()
            # JSON 파싱
            if pd.notna(request_dict['extracted_data']):
                try:
                    request_dict['extracted_data'] = json.loads(request_dict['extracted_data'])
                except:
                    request_dict['extracted_data'] = []
            else:
                request_dict['extracted_data'] = []
            
            if pd.notna(request_dict['final_data']):
                try:
                    request_dict['final_data'] = json.loads(request_dict['final_data'])
                except:
                    request_dict['final_data'] = []
            else:
                request_dict['final_data'] = []
            
            return request_dict
        return None
    
    # Test Item 관련
    def add_test_items(self, test_items, request_id):
        """시험 항목 추가"""
        df = pd.read_csv(TEST_ITEM_FILE, encoding='utf-8-sig')
        new_items = []
        
        for item in test_items:
            new_id = f"TI{str(len(df) + len(new_items) + 1).zfill(5)}"
            new_item = {
                'id': new_id,
                'test_name': item.get('test_name', ''),
                'test_name_original': item.get('test_name_original', item.get('test_name', '')),
                'category': item.get('category', ''),
                'category_original': item.get('category_original', item.get('category', '')),
                'ref_standard': item.get('ref_standard', ''),
                'sample_assembly': item.get('sample_assembly', ''),
                'test_sample_no': item.get('test_sample_no', ''),
                'sample_count': item.get('sample_count', ''),
                'test_duration': item.get('test_duration', ''),
                'test_equipment': item.get('test_equipment', ''),
                'test_master_id': item.get('test_master_id', ''),
                'custom_specs': json.dumps(item.get('custom_specs', {}), ensure_ascii=False),
                'request_id': request_id
            }
            new_items.append(new_item)
        
        df = pd.concat([df, pd.DataFrame(new_items)], ignore_index=True)
        df.to_csv(TEST_ITEM_FILE, index=False, encoding='utf-8-sig')
        return [item['id'] for item in new_items]
    
    def get_test_items_by_request(self, request_id):
        """의뢰별 시험 항목 조회"""
        df = pd.read_csv(TEST_ITEM_FILE, encoding='utf-8-sig')
        items = df[df['request_id'] == request_id]
        items_list = []
        for _, row in items.iterrows():
            item_dict = row.to_dict()
            # custom_specs 파싱
            if pd.notna(item_dict['custom_specs']):
                try:
                    item_dict['custom_specs'] = json.loads(item_dict['custom_specs'])
                except:
                    item_dict['custom_specs'] = {}
            else:
                item_dict['custom_specs'] = {}
            items_list.append(item_dict)
        return items_list
    
    def get_test_item_by_id(self, test_item_id):
        """ID로 시험 항목 조회"""
        df = pd.read_csv(TEST_ITEM_FILE, encoding='utf-8-sig')
        item = df[df['id'] == test_item_id]
        if len(item) > 0:
            item_dict = item.iloc[0].to_dict()
            if pd.notna(item_dict['custom_specs']):
                try:
                    item_dict['custom_specs'] = json.loads(item_dict['custom_specs'])
                except:
                    item_dict['custom_specs'] = {}
            else:
                item_dict['custom_specs'] = {}
            return item_dict
        return None
    
    # Schedule Item 관련
    def add_schedule_items(self, schedule_items):
        """일정 항목 추가"""
        df = pd.read_csv(SCHEDULE_ITEM_FILE, encoding='utf-8-sig')
        df = pd.concat([df, pd.DataFrame(schedule_items)], ignore_index=True)
        df.to_csv(SCHEDULE_ITEM_FILE, index=False, encoding='utf-8-sig')
    
    def get_schedule_by_user(self, user_id, month=None):
        """사용자별 일정 조회"""
        # 사용자의 모든 의뢰 가져오기
        requests = self.get_all_requests(user_id)
        if len(requests) == 0:
            return pd.DataFrame()
        
        request_ids = requests['id'].tolist()
        
        # 의뢰에 속한 시험 항목 가져오기
        test_items_df = pd.read_csv(TEST_ITEM_FILE, encoding='utf-8-sig')
        test_items = test_items_df[test_items_df['request_id'].isin(request_ids)]
        
        if len(test_items) == 0:
            return pd.DataFrame()
        
        test_item_ids = test_items['id'].tolist()
        
        # 일정 가져오기
        schedule_df = pd.read_csv(SCHEDULE_ITEM_FILE, encoding='utf-8-sig')
        schedule = schedule_df[schedule_df['test_item_id'].isin(test_item_ids)]
        
        if month and len(schedule) > 0:
            schedule['start_date'] = pd.to_datetime(schedule['start_date'])
            schedule = schedule[schedule['start_date'].dt.strftime('%Y-%m') == month]
        
        return schedule
    
    def get_last_end_date(self, user_id):
        """사용자의 마지막 일정 종료일 조회"""
        schedule = self.get_schedule_by_user(user_id)
        if len(schedule) == 0:
            return None
        schedule['end_date'] = pd.to_datetime(schedule['end_date'])
        return schedule['end_date'].max()
    
    # CSV Export
    def export_csv(self, table_name):
        """CSV 파일 내보내기"""
        file_map = {
            'User List': USER_LIST_FILE,
            'Master Test': MASTER_TEST_FILE,
            'Request Info': REQUEST_INFO_FILE,
            'Test Item': TEST_ITEM_FILE,
            'Schedule Item': SCHEDULE_ITEM_FILE
        }
        
        if table_name in file_map:
            df = pd.read_csv(file_map[table_name], encoding='utf-8-sig')
            return df
        return None
