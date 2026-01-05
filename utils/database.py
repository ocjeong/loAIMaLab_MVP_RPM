import pandas as pd
import os
from datetime import datetime
import json

class DatabaseManager:
    def __init__(self, data_dir='data'):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        
        self.master_file = os.path.join(data_dir, 'Master_Test.csv')
        self.request_file = os.path.join(data_dir, 'Request_Info.csv')
        self.test_item_file = os.path.join(data_dir, 'Test_Item.csv')
        self.user_file = os.path.join(data_dir, 'User_List.csv')
        
        self._initialize_files()
    
    def _initialize_files(self):
        """CSV 파일 초기화"""
        # Master Test Data
        if not os.path.exists(self.master_file):
            master_df = pd.DataFrame(columns=['id', 'std_name', 'std_category', 'aliases', 'ref_standard'])
            # 초기 마스터 데이터 추가
            initial_masters = [
                {
                    'id': 'M001',
                    'std_name': 'On & Off Test',
                    'std_category': 'Endurance Test',
                    'aliases': '["작동성 시험", "온오프", "ON/OFF 시험"]',
                    'ref_standard': ''
                },
                {
                    'id': 'M002',
                    'std_name': 'High Temperature Test',
                    'std_category': 'Environmental Test',
                    'aliases': '["고온 시험", "고온 내구", "열 시험"]',
                    'ref_standard': 'ISO 16750-4'
                },
                {
                    'id': 'M003',
                    'std_name': 'Low Temperature Test',
                    'std_category': 'Environmental Test',
                    'aliases': '["저온 시험", "저온 내구", "냉각 시험"]',
                    'ref_standard': 'ISO 16750-4'
                },
                {
                    'id': 'M004',
                    'std_name': 'Noise Test',
                    'std_category': 'Performance Test',
                    'aliases': '["소음 시험", "소음 측정", "음향 시험"]',
                    'ref_standard': ''
                },
                {
                    'id': 'M005',
                    'std_name': 'Random Vibration Test',
                    'std_category': 'Environmental Test',
                    'aliases': '["진동 시험", "랜덤 진동", "진동 내구"]',
                    'ref_standard': 'ISO 16750-3'
                },
                {
                    'id': 'M006',
                    'std_name': 'Dust Protection Test',
                    'std_category': 'Environmental Test',
                    'aliases': '["방진 시험", "분진 시험", "먼지 보호"]',
                    'ref_standard': 'ISO 20653'
                },
                {
                    'id': 'M007',
                    'std_name': 'Water Protection Test',
                    'std_category': 'Environmental Test',
                    'aliases': '["방수 시험", "침수 시험", "물 보호"]',
                    'ref_standard': 'ISO 20653'
                },
                {
                    'id': 'M008',
                    'std_name': 'Voltage Drop Test',
                    'std_category': 'Electrical Tests',
                    'aliases': '["전압 강하", "전압 드롭", "전압 저하 시험"]',
                    'ref_standard': 'ISO 16750-3'
                },
                {
                    'id': 'M009',
                    'std_name': 'Undervoltage and Overvoltage Test',
                    'std_category': 'Electrical Tests',
                    'aliases': '["과저전압", "정지 전압 확인", "전압 범위 시험"]',
                    'ref_standard': 'ISO 16750-3'
                },
            ]
            master_df = pd.DataFrame(initial_masters)
            master_df.to_csv(self.master_file, index=False, encoding='utf-8-sig')
        
        # Request Info Data
        if not os.path.exists(self.request_file):
            request_df = pd.DataFrame(columns=['id', 'user_id', 'extracted_data', 'final_data', 
                                              'is_verified', 'client', 'project', 'created_date'])
            request_df.to_csv(self.request_file, index=False, encoding='utf-8-sig')
        
        # Test Item Data
        if not os.path.exists(self.test_item_file):
            test_item_df = pd.DataFrame(columns=['test_name', 'test_name_original', 'category', 
                                                 'category_original', 'ref_standard', 'sample_assembly',
                                                 'test_sample_no', 'sample_count', 'test_duration',
                                                 'test_equipment', 'test_master_id', 'custom_specs', 
                                                 'request_id'])
            test_item_df.to_csv(self.test_item_file, index=False, encoding='utf-8-sig')
        
        # User List Data
        if not os.path.exists(self.user_file):
            user_df = pd.DataFrame(columns=['id', 'user_name', 'created_date', 'last_access'])
            # 기본 사용자 추가
            user_df = pd.DataFrame([{
                'id': 'U001',
                'user_name': '기본사용자',
                'created_date': datetime.now().strftime('%Y-%m-%d'),
                'last_access': datetime.now().strftime('%Y-%m-%d')
            }])
            user_df.to_csv(self.user_file, index=False, encoding='utf-8-sig')
    
    # User 관련 메서드
    def load_user_data(self):
        return pd.read_csv(self.user_file, encoding='utf-8-sig')
    
    def add_user(self, user_name):
        users_df = self.load_user_data()
        new_id = f"U{str(len(users_df) + 1).zfill(3)}"
        new_user = pd.DataFrame([{
            'id': new_id,
            'user_name': user_name,
            'created_date': datetime.now().strftime('%Y-%m-%d'),
            'last_access': datetime.now().strftime('%Y-%m-%d')
        }])
        users_df = pd.concat([users_df, new_user], ignore_index=True)
        users_df.to_csv(self.user_file, index=False, encoding='utf-8-sig')
        return new_id
    
    def update_user_last_access(self, user_id):
        users_df = self.load_user_data()
        users_df.loc[users_df['id'] == user_id, 'last_access'] = datetime.now().strftime('%Y-%m-%d')
        users_df.to_csv(self.user_file, index=False, encoding='utf-8-sig')
    
    # Master 관련 메서드
    def load_master_data(self):
        return pd.read_csv(self.master_file, encoding='utf-8-sig')
    
    def get_master_by_id(self, master_id):
        if not master_id:
            return None
        master_df = self.load_master_data()
        result = master_df[master_df['id'] == master_id]
        if result.empty:
            return None
        return result.iloc[0].to_dict()
    
    def update_master_aliases(self, master_id, new_alias):
        """마스터 데이터의 유사어 업데이트"""
        master_df = self.load_master_data()
        idx = master_df[master_df['id'] == master_id].index
        
        if not idx.empty:
            current_aliases = json.loads(master_df.loc[idx[0], 'aliases'])
            if new_alias not in current_aliases:
                current_aliases.append(new_alias)
                master_df.loc[idx[0], 'aliases'] = json.dumps(current_aliases, ensure_ascii=False)
                master_df.to_csv(self.master_file, index=False, encoding='utf-8-sig')
    
    def add_new_master(self, test_item):
        """새로운 마스터 데이터 추가"""
        master_df = self.load_master_data()
        new_id = f"M{str(len(master_df) + 1).zfill(3)}"
        
        new_master = pd.DataFrame([{
            'id': new_id,
            'std_name': test_item.get('test_name', ''),
            'std_category': test_item.get('category', ''),
            'aliases': json.dumps([test_item.get('test_name_original', '')], ensure_ascii=False),
            'ref_standard': test_item.get('ref_standard', '')
        }])
        
        master_df = pd.concat([master_df, new_master], ignore_index=True)
        master_df.to_csv(self.master_file, index=False, encoding='utf-8-sig')
        return new_id
    
    def update_master_from_extraction(self, test_items):
        """추출된 데이터로 마스터 데이터 업데이트"""
        for item in test_items:
            master_id = item.get('test_master_id')
            original_name = item.get('test_name_original')
            
            if master_id and original_name:
                # 매칭된 마스터의 유사어 업데이트
                self.update_master_aliases(master_id, original_name)
            elif not master_id:
                # 미매칭 항목은 새 마스터로 추가
                new_master_id = self.add_new_master(item)
                item['test_master_id'] = new_master_id
    
    def standardize_test_item(self, test_item):
        """시험 항목을 마스터 데이터 기준으로 표준화"""
        master_id = test_item.get('test_master_id')
        
        if master_id:
            master_data = self.get_master_by_id(master_id)
            
            if master_data:
                # 원본 데이터 보존
                if 'test_name_original' not in test_item:
                    test_item['test_name_original'] = test_item.get('test_name', '')
                if 'category_original' not in test_item:
                    test_item['category_original'] = test_item.get('category', '')
                
                # 표준화 적용
                test_item['test_name'] = master_data['std_name']
                test_item['category'] = master_data['std_category']
                
                # ref_standard가 없으면 마스터에서 가져오기
                if not test_item.get('ref_standard'):
                    test_item['ref_standard'] = master_data.get('ref_standard', '')
        
        return test_item
    
    # Request 관련 메서드
    def load_request_data(self):
        return pd.read_csv(self.request_file, encoding='utf-8-sig')
    
    def get_user_requests(self, user_id):
        requests_df = self.load_request_data()
        return requests_df[requests_df['user_id'] == user_id]
    
    def get_request_by_id(self, request_id):
        requests_df = self.load_request_data()
        result = requests_df[requests_df['id'] == request_id]
        if result.empty:
            return None
        return result.iloc[0].to_dict()
    
    def create_request(self, user_id, extracted_data, client, project):
        """새 의뢰 생성"""
        requests_df = self.load_request_data()
        new_id = f"R{str(len(requests_df) + 1).zfill(5)}"
        
        new_request = pd.DataFrame([{
            'id': new_id,
            'user_id': user_id,
            'extracted_data': json.dumps(extracted_data, ensure_ascii=False),
            'final_data': json.dumps(extracted_data, ensure_ascii=False),
            'is_verified': False,
            'client': client,
            'project': project,
            'created_date': datetime.now().strftime('%Y-%m-%d')
        }])
        
        requests_df = pd.concat([requests_df, new_request], ignore_index=True)
        requests_df.to_csv(self.request_file, index=False, encoding='utf-8-sig')
        
        # Test Item 데이터 저장
        self._save_test_items(new_id, extracted_data.get('test_items', []))
        
        return new_id
    
    def update_request(self, request_id, data):
        """기존 의뢰 업데이트"""
        requests_df = self.load_request_data()
        idx = requests_df[requests_df['id'] == request_id].index
        
        if not idx.empty:
            requests_df.loc[idx[0], 'final_data'] = json.dumps(data, ensure_ascii=False)
            requests_df.loc[idx[0], 'client'] = data['request_info'].get('client', '')
            requests_df.loc[idx[0], 'project'] = data['request_info'].get('project', '')
            requests_df.to_csv(self.request_file, index=False, encoding='utf-8-sig')
            
            # Test Item 데이터 업데이트
            self._update_test_items(request_id, data.get('test_items', []))
    
    # Test Item 관련 메서드
    def load_test_item_data(self):
        return pd.read_csv(self.test_item_file, encoding='utf-8-sig')
    
    def _save_test_items(self, request_id, test_items):
        """시험 항목 데이터 저장"""
        test_item_df = self.load_test_item_data()
        
        for item in test_items:
            new_item = pd.DataFrame([{
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
            }])
            test_item_df = pd.concat([test_item_df, new_item], ignore_index=True)
        
        test_item_df.to_csv(self.test_item_file, index=False, encoding='utf-8-sig')
    
    def _update_test_items(self, request_id, test_items):
        """시험 항목 데이터 업데이트"""
        test_item_df = self.load_test_item_data()
        
        # 기존 항목 삭제
        test_item_df = test_item_df[test_item_df['request_id'] != request_id]
        
        # 새 항목 추가
        for item in test_items:
            new_item = pd.DataFrame([{
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
            }])
            test_item_df = pd.concat([test_item_df, new_item], ignore_index=True)
        
        test_item_df.to_csv(self.test_item_file, index=False, encoding='utf-8-sig')
    
    def get_test_items_by_request(self, request_id):
        """특정 의뢰의 시험 항목 조회"""
        test_item_df = self.load_test_item_data()
        return test_item_df[test_item_df['request_id'] == request_id]
