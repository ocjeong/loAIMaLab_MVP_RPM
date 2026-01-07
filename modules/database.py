import pandas as pd
import os
from datetime import datetime
import json

class DatabaseManager:
    def __init__(self, data_dir='data'):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        
        # CSV 파일 경로
        self.master_file = os.path.join(data_dir, 'Master_Test.csv')
        self.request_file = os.path.join(data_dir, 'Request_Info.csv')
        self.test_item_file = os.path.join(data_dir, 'Test_Item.csv')
        self.user_file = os.path.join(data_dir, 'User_List.csv')
        
        # 초기화
        self._initialize_databases()
    
    def _initialize_databases(self):
        """데이터베이스 파일 초기화"""
        # Master Test Data
        if not os.path.exists(self.master_file):
            master_data = {
                'id': ['M001', 'M002', 'M003', 'M004', 'M005', 'M006', 'M007', 'M008', 'M009'],
                'std_name': [
                    'On & Off Test',
                    'High Temperature Test',
                    'Low Temperature Test',
                    'Noise Test',
                    'Random Vibration Test',
                    'Dust Protection Test',
                    'Water Protection Test',
                    'Functional Test',
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
                    'Functional Test',
                    'Electrical Tests'
                ],
                'aliases': [
                    '["작동성 시험", "온오프", "On/Off"]',
                    '["고온 시험", "고온 내구", "High Temp"]',
                    '["저온 시험", "저온 내구", "Low Temp"]',
                    '["소음 시험", "소음 측정", "Noise Measurement"]',
                    '["진동 시험", "랜덤 진동"]',
                    '["분진 시험", "방진"]',
                    '["방수 시험", "침수"]',
                    '["기능 시험", "성능 확인"]',
                    '["과저전압", "정지 전압 확인", "Under/Over Voltage"]'
                ],
                'ref_standard': [
                    '',
                    'ISO 16750-4',
                    'ISO 16750-4',
                    '',
                    'ISO 16750-3',
                    'ISO 20653',
                    'ISO 20653',
                    '',
                    'ISO 16750-3'
                ]
            }
            pd.DataFrame(master_data).to_csv(self.master_file, index=False, encoding='utf-8-sig')
        
        # User List Data
        if not os.path.exists(self.user_file):
            user_data = {
                'id': ['U001'],
                'user_name': ['기본사용자'],
                'created_date': [datetime.now().strftime('%Y-%m-%d')],
                'last_access': [datetime.now().strftime('%Y-%m-%d')]
            }
            pd.DataFrame(user_data).to_csv(self.user_file, index=False, encoding='utf-8-sig')
        
        # Request Info Data
        if not os.path.exists(self.request_file):
            request_data = {
                'id': [],
                'user_id': [],
                'extracted_data': [],
                'final_data': [],
                'is_verified': [],
                'client': [],
                'project': []
            }
            pd.DataFrame(request_data).to_csv(self.request_file, index=False, encoding='utf-8-sig')
        
        # Test Item Data
        if not os.path.exists(self.test_item_file):
            test_item_data = {
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
            }
            pd.DataFrame(test_item_data).to_csv(self.test_item_file, index=False, encoding='utf-8-sig')
    
    def load_users(self):
        """사용자 목록 로드"""
        return pd.read_csv(self.user_file, encoding='utf-8-sig')
    
    def add_user(self, user_id, user_name):
        """사용자 추가"""
        users = self.load_users()
        new_user = {
            'id': user_id,
            'user_name': user_name,
            'created_date': datetime.now().strftime('%Y-%m-%d'),
            'last_access': datetime.now().strftime('%Y-%m-%d')
        }
        users = pd.concat([users, pd.DataFrame([new_user])], ignore_index=True)
        users.to_csv(self.user_file, index=False, encoding='utf-8-sig')
    
    def update_user_access(self, user_id):
        """사용자 마지막 접속 시간 업데이트"""
        users = self.load_users()
        users.loc[users['id'] == user_id, 'last_access'] = datetime.now().strftime('%Y-%m-%d')
        users.to_csv(self.user_file, index=False, encoding='utf-8-sig')
    
    def load_master_data(self):
        """마스터 데이터 로드"""
        df = pd.read_csv(self.master_file, encoding='utf-8-sig')
        # aliases를 리스트로 변환
        df['aliases'] = df['aliases'].apply(lambda x: json.loads(x) if pd.notna(x) else [])
        return df
    
    def get_master_by_id(self, master_id):
        """ID로 마스터 데이터 조회"""
        masters = self.load_master_data()
        result = masters[masters['id'] == master_id]
        if not result.empty:
            return result.iloc[0].to_dict()
        return None
    
    def update_master_aliases(self, test_items):
        """마스터 데이터의 유사어 업데이트"""
        masters = self.load_master_data()
        
        for item in test_items:
            master_id = item.get('test_master_id')
            if master_id:
                original_name = item.get('test_name_original', item.get('test_name'))
                
                # 해당 마스터의 aliases에 추가
                idx = masters[masters['id'] == master_id].index
                if not idx.empty:
                    current_aliases = masters.loc[idx[0], 'aliases']
                    if original_name and original_name not in current_aliases:
                        current_aliases.append(original_name)
                        masters.loc[idx[0], 'aliases'] = current_aliases
        
        # aliases를 JSON 문자열로 변환하여 저장
        masters['aliases'] = masters['aliases'].apply(json.dumps)
        masters.to_csv(self.master_file, index=False, encoding='utf-8-sig')
    
    def add_master(self, test_item):
        """새로운 마스터 데이터 추가"""
        masters = self.load_master_data()
        new_id = f"M{str(len(masters) + 1).zfill(3)}"
        
        new_master = {
            'id': new_id,
            'std_name': test_item.get('test_name', ''),
            'std_category': test_item.get('category', ''),
            'aliases': json.dumps([test_item.get('test_name', '')]),
            'ref_standard': test_item.get('ref_standard', '')
        }
        
        masters = pd.concat([masters, pd.DataFrame([new_master])], ignore_index=True)
        masters['aliases'] = masters['aliases'].apply(json.dumps)
        masters.to_csv(self.master_file, index=False, encoding='utf-8-sig')
        
        return new_id
    
    def load_requests(self):
        """전체 의뢰 데이터 로드"""
        return pd.read_csv(self.request_file, encoding='utf-8-sig')
    
    def load_requests_by_user(self, user_id):
        """특정 사용자의 의뢰 데이터 로드"""
        requests = self.load_requests()
        return requests[requests['user_id'] == user_id]
    
    def save_request(self, request_id, user_id, extracted_data, final_data, client, project):
        """의뢰 데이터 저장"""
        requests = self.load_requests()
        
        # 기존 의뢰 확인
        existing = requests[requests['id'] == request_id]
        
        request_data = {
            'id': request_id,
            'user_id': user_id,
            'extracted_data': json.dumps(extracted_data, ensure_ascii=False),
            'final_data': json.dumps(final_data, ensure_ascii=False),
            'is_verified': True,
            'client': client,
            'project': project
        }
        
        if not existing.empty:
            # 업데이트
            for key, value in request_data.items():
                requests.loc[requests['id'] == request_id, key] = value
        else:
            # 새로 추가
            requests = pd.concat([requests, pd.DataFrame([request_data])], ignore_index=True)
        
        requests.to_csv(self.request_file, index=False, encoding='utf-8-sig')
        
        # Test Item 데이터 저장
        self._save_test_items(request_id, final_data.get('test_items', []))
    
    def _save_test_items(self, request_id, test_items):
        """시험 항목 데이터 저장"""
        items_df = pd.read_csv(self.test_item_file, encoding='utf-8-sig')
        
        # 기존 항목 삭제
        items_df = items_df[items_df['request_id'] != request_id]
        
        # 새 항목 추가
        for item in test_items:
            item_data = {
                'test_name': item.get('test_name', ''),
                'test_name_original': item.get('test_name_original', ''),
                'category': item.get('category', ''),
                'category_original': item.get('category_original', ''),
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
            items_df = pd.concat([items_df, pd.DataFrame([item_data])], ignore_index=True)
        
        items_df.to_csv(self.test_item_file, index=False, encoding='utf-8-sig')
    
    def load_test_items_by_request(self, request_id):
        """특정 의뢰의 시험 항목 로드"""
        items = pd.read_csv(self.test_item_file, encoding='utf-8-sig')
        return items[items['request_id'] == request_id]
    
    def save_schedule(self, request_id, user_id, schedule):
        """일정 저장 (Request에 포함)"""
        # 실제로는 별도 Schedule 테이블이 필요할 수 있음
        # 여기서는 간단히 Request의 final_data에 포함
        pass
    
    def export_to_csv(self, data_type):
        """CSV 파일 내보내기"""
        file_map = {
            'master': self.master_file,
            'request': self.request_file,
            'test_item': self.test_item_file,
            'user': self.user_file
        }
        
        file_path = file_map.get(data_type)
        if file_path and os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                return f.read()
        return ""
