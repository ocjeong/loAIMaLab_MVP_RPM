import pandas as pd
import json
from pathlib import Path
from datetime import datetime
import streamlit as st

class DataManager:
    def __init__(self):
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        
        self.user_list_path = self.data_dir / "User_List.csv"
        self.master_test_path = self.data_dir / "Master_Test.csv"
        self.request_info_path = self.data_dir / "Request_Info.csv"
        self.test_item_path = self.data_dir / "Test_Item.csv"
        self.schedule_item_path = self.data_dir / "Schedule_Item.csv"
    
    @staticmethod
    def initialize_csv_files():
        """CSV 파일 초기화"""
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        
        # User List 초기화
        user_list_path = data_dir / "User_List.csv"
        if not user_list_path.exists():
            df = pd.DataFrame({
                'id': ['U001'],
                'user_name': ['기본사용자'],
                'created_date': [datetime.now().strftime('%Y-%m-%d')],
                'last_access': [datetime.now().strftime('%Y-%m-%d')]
            })
            df.to_csv(user_list_path, index=False, encoding='utf-8-sig')
        
        # Master Test 초기화 (샘플 데이터)
        master_test_path = data_dir / "Master_Test.csv"
        if not master_test_path.exists():
            df = pd.DataFrame({
                'id': ['M001', 'M002', 'M003', 'M004', 'M005', 'M006', 'M007', 'M008', 'M009'],
                'std_name': [
                    'On & Off Test',
                    'High Temperature Test',
                    'Low Temperature Test',
                    'Noise Test',
                    'Random Vibration Test',
                    'Salt Spray Test',
                    'Dust Protection Test',
                    'Water Protection Test',
                    'Undervoltage and Overvoltage Test'
                ],
                'std_category': [
                    'Endurance Test',
                    'Environmental Test',
                    'Environmental Test',
                    'Performance Test',
                    'Environmental Test',
                    'Environmental Test',
                    'Environmental Test',
                    'Environmental Test',
                    'Electrical Tests'
                ],
                'aliases': [
                    '["작동성 시험", "온오프", "ON/OFF 시험"]',
                    '["고온 시험", "고온 내구", "High Temp"]',
                    '["저온 시험", "저온 내구", "Low Temp"]',
                    '["소음 시험", "소음 측정", "Noise Measurement"]',
                    '["랜덤 진동", "진동 시험", "Vibration"]',
                    '["염수 분무", "내식성", "Corrosion"]',
                    '["분진 보호", "방진", "Dust"]',
                    '["방수", "침수", "Water Ingress"]',
                    '["과저전압", "정지 전압 확인", "Voltage Test"]'
                ],
                'ref_standard': [
                    '',
                    'ISO 16750-3',
                    'ISO 16750-3',
                    '',
                    'ISO 16750-3',
                    'ISO 9227',
                    'ISO 20653',
                    'ISO 20653',
                    'ISO 16750-3'
                ]
            })
            df.to_csv(master_test_path, index=False, encoding='utf-8-sig')
        
        # Request Info 초기화
        request_info_path = data_dir / "Request_Info.csv"
        if not request_info_path.exists():
            df = pd.DataFrame({
                'id': [],
                'user_id': [],
                'extracted_data': [],
                'final_data': [],
                'is_verified': [],
                'client': [],
                'project': []
            })
            df.to_csv(request_info_path, index=False, encoding='utf-8-sig')
        
        # Test Item 초기화
        test_item_path = data_dir / "Test_Item.csv"
        if not test_item_path.exists():
            df = pd.DataFrame({
                'id': [],
                'test_name': [],
                'test_name_original': [],
                'category': [],
                'category_original': [],
                'ref_standard': [],
                'sample_assembly': [],
                'test_sample_no': [],
                'sample_count': [],
                'test_duration': [],
                'test_equipment': [],
                'test_master_id': [],
                'custom_specs': [],
                'request_id': []
            })
            df.to_csv(test_item_path, index=False, encoding='utf-8-sig')
        
        # Schedule Item 초기화
        schedule_item_path = data_dir / "Schedule_Item.csv"
        if not schedule_item_path.exists():
            df = pd.DataFrame({
                'test_item_id': [],
                'start_date': [],
                'end_date': [],
                'start_day': [],
                'end_day': [],
                'duration': [],
                'status': []
            })
            df.to_csv(schedule_item_path, index=False, encoding='utf-8-sig')
    
    def load_user_list(self):
        """사용자 목록 로드"""
        if self.user_list_path.exists():
            return pd.read_csv(self.user_list_path, encoding='utf-8-sig')
        return pd.DataFrame()
    
    def save_user_list(self, df):
        """사용자 목록 저장"""
        df.to_csv(self.user_list_path, index=False, encoding='utf-8-sig')
    
    def add_user(self, user_name):
        """사용자 추가"""
        df = self.load_user_list()
        new_id = f"U{str(len(df) + 1).zfill(3)}"
        new_user = pd.DataFrame({
            'id': [new_id],
            'user_name': [user_name],
            'created_date': [datetime.now().strftime('%Y-%m-%d')],
            'last_access': [datetime.now().strftime('%Y-%m-%d')]
        })
        df = pd.concat([df, new_user], ignore_index=True)
        self.save_user_list(df)
        return new_id
    
    def update_last_access(self, user_id):
        """마지막 접속 시간 업데이트"""
        df = self.load_user_list()
        df.loc[df['id'] == user_id, 'last_access'] = datetime.now().strftime('%Y-%m-%d')
        self.save_user_list(df)
    
    def load_master_test(self):
        """마스터 테스트 데이터 로드"""
        if self.master_test_path.exists():
            return pd.read_csv(self.master_test_path, encoding='utf-8-sig')
        return pd.DataFrame()
    
    def save_master_test(self, df):
        """마스터 테스트 데이터 저장"""
        df.to_csv(self.master_test_path, index=False, encoding='utf-8-sig')
    
    def get_master_by_id(self, master_id):
        """마스터 ID로 마스터 데이터 조회"""
        df = self.load_master_test()
        result = df[df['id'] == master_id]
        if not result.empty:
            return result.iloc[0].to_dict()
        return None
    
    def update_master_aliases(self, master_id, new_alias):
        """마스터 데이터의 유사어 업데이트"""
        df = self.load_master_test()
        idx = df[df['id'] == master_id].index
        if not idx.empty:
            aliases_str = df.loc[idx[0], 'aliases']
            try:
                aliases = json.loads(aliases_str)
            except:
                aliases = []
            
            if new_alias not in aliases:
                aliases.append(new_alias)
                df.loc[idx[0], 'aliases'] = json.dumps(aliases, ensure_ascii=False)
                self.save_master_test(df)
    
    def add_master_test(self, std_name, std_category, ref_standard, aliases):
        """새로운 마스터 테스트 추가"""
        df = self.load_master_test()
        new_id = f"M{str(len(df) + 1).zfill(3)}"
        new_master = pd.DataFrame({
            'id': [new_id],
            'std_name': [std_name],
            'std_category': [std_category],
            'aliases': [json.dumps(aliases, ensure_ascii=False)],
            'ref_standard': [ref_standard]
        })
        df = pd.concat([df, new_master], ignore_index=True)
        self.save_master_test(df)
        return new_id
    
    def load_request_info(self):
        """의뢰 정보 로드"""
        if self.request_info_path.exists():
            return pd.read_csv(self.request_info_path, encoding='utf-8-sig')
        return pd.DataFrame()
    
    def save_request_info(self, df):
        """의뢰 정보 저장"""
        df.to_csv(self.request_info_path, index=False, encoding='utf-8-sig')
    
    def add_request(self, user_id, client, project, extracted_data):
        """새로운 의뢰 추가"""
        df = self.load_request_info()
        new_id = f"R{str(len(df) + 1).zfill(5)}"
        new_request = pd.DataFrame({
            'id': [new_id],
            'user_id': [user_id],
            'extracted_data': [json.dumps(extracted_data, ensure_ascii=False)],
            'final_data': [''],
            'is_verified': [False],
            'client': [client],
            'project': [project]
        })
        df = pd.concat([df, new_request], ignore_index=True)
        self.save_request_info(df)
        return new_id
    
    def update_request_final_data(self, request_id, final_data):
        """의뢰의 최종 데이터 업데이트"""
        df = self.load_request_info()
        df.loc[df['id'] == request_id, 'final_data'] = json.dumps(final_data, ensure_ascii=False)
        self.save_request_info(df)
    
    def load_test_item(self):
        """시험 항목 데이터 로드"""
        if self.test_item_path.exists():
            return pd.read_csv(self.test_item_path, encoding='utf-8-sig')
        return pd.DataFrame()
    
    def save_test_item(self, df):
        """시험 항목 데이터 저장"""
        df.to_csv(self.test_item_path, index=False, encoding='utf-8-sig')
    
    def add_test_items(self, test_items, request_id):
        """시험 항목 추가"""
        df = self.load_test_item()
        start_idx = len(df) + 1
        
        new_items = []
        for i, item in enumerate(test_items):
            new_id = f"TI{str(start_idx + i).zfill(5)}"
            item['id'] = new_id
            item['request_id'] = request_id
            new_items.append(item)
        
        new_df = pd.DataFrame(new_items)
        df = pd.concat([df, new_df], ignore_index=True)
        self.save_test_item(df)
        return new_items
    
    def load_schedule_item(self):
        """스케줄 항목 로드"""
        if self.schedule_item_path.exists():
            return pd.read_csv(self.schedule_item_path, encoding='utf-8-sig')
        return pd.DataFrame()
    
    def save_schedule_item(self, df):
        """스케줄 항목 저장"""
        df.to_csv(self.schedule_item_path, index=False, encoding='utf-8-sig')
    
    def add_schedule_items(self, schedule_items):
        """스케줄 항목 추가"""
        df = self.load_schedule_item()
        new_df = pd.DataFrame(schedule_items)
        df = pd.concat([df, new_df], ignore_index=True)
        self.save_schedule_item(df)
    
    def get_user_schedules(self, user_id):
        """사용자의 모든 스케줄 조회"""
        test_items = self.load_test_item()
        schedules = self.load_schedule_item()
        requests = self.load_request_info()
        
        # 사용자의 의뢰 필터링
        user_requests = requests[requests['user_id'] == user_id]['id'].tolist()
        
        # 사용자의 시험 항목 필터링
        user_test_items = test_items[test_items['request_id'].isin(user_requests)]
        
        # 스케줄 조인
        result = schedules[schedules['test_item_id'].isin(user_test_items['id'])]
        
        return result.merge(user_test_items, left_on='test_item_id', right_on='id', how='left')
