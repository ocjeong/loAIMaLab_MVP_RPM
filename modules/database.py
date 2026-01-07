import pandas as pd
import os
from datetime import datetime
import json

class DatabaseManager:
    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        
        self.master_test_file = os.path.join(data_dir, "Master_Test.csv")
        self.request_info_file = os.path.join(data_dir, "Request_Info.csv")
        self.test_item_file = os.path.join(data_dir, "Test_Item.csv")
        self.user_list_file = os.path.join(data_dir, "User_List.csv")
        
        self._initialize_files()
    
    def _initialize_files(self):
        """CSV 파일이 없으면 초기화"""
        # Master Test Data
        if not os.path.exists(self.master_test_file):
            master_df = pd.DataFrame(columns=['id', 'std_name', 'std_category', 'aliases', 'ref_standard'])
            master_df.to_csv(self.master_test_file, index=False, encoding='utf-8-sig')
        
        # Request Info Data
        if not os.path.exists(self.request_info_file):
            request_df = pd.DataFrame(columns=['id', 'user_id', 'extracted_data', 'final_data', 
                                              'is_verified', 'client', 'project'])
            request_df.to_csv(self.request_info_file, index=False, encoding='utf-8-sig')
        
        # Test Item Data
        if not os.path.exists(self.test_item_file):
            test_item_df = pd.DataFrame(columns=['test_name', 'test_name_original', 'category', 
                                                'category_original', 'ref_standard', 'sample_assembly',
                                                'test_sample_no', 'sample_count', 'test_duration',
                                                'test_equipment', 'test_master_id', 'custom_specs', 
                                                'request_id'])
            test_item_df.to_csv(self.test_item_file, index=False, encoding='utf-8-sig')
        
        # User List Data
        if not os.path.exists(self.user_list_file):
            user_df = pd.DataFrame(columns=['id', 'user_name', 'created_date', 'last_access'])
            # 기본 사용자 추가
            user_df = pd.DataFrame([{
                'id': 'U001',
                'user_name': '기본사용자',
                'created_date': datetime.now().strftime('%Y-%m-%d'),
                'last_access': datetime.now().strftime('%Y-%m-%d')
            }])
            user_df.to_csv(self.user_list_file, index=False, encoding='utf-8-sig')
    
    # User 관련 메서드
    def load_users(self):
        return pd.read_csv(self.user_list_file, encoding='utf-8-sig')
    
    def add_user(self, user_name):
        users = self.load_users()
        new_id = f"U{str(len(users) + 1).zfill(3)}"
        new_user = pd.DataFrame([{
            'id': new_id,
            'user_name': user_name,
            'created_date': datetime.now().strftime('%Y-%m-%d'),
            'last_access': datetime.now().strftime('%Y-%m-%d')
        }])
        users = pd.concat([users, new_user], ignore_index=True)
        users.to_csv(self.user_list_file, index=False, encoding='utf-8-sig')
        return new_id
    
    def update_user_last_access(self, user_id):
        users = self.load_users()
        users.loc[users['id'] == user_id, 'last_access'] = datetime.now().strftime('%Y-%m-%d')
        users.to_csv(self.user_list_file, index=False, encoding='utf-8-sig')
    
    # Master Test 관련 메서드
    def load_master_tests(self):
        df = pd.read_csv(self.master_test_file, encoding='utf-8-sig')
        # aliases를 리스트로 변환
        if 'aliases' in df.columns:
            df['aliases'] = df['aliases'].apply(lambda x: json.loads(x) if pd.notna(x) and x != '' else [])
        return df
    
    def add_alias_to_master(self, master_id, alias):
        masters = self.load_master_tests()
        idx = masters[masters['id'] == master_id].index
        if len(idx) > 0:
            current_aliases = masters.loc[idx[0], 'aliases']
            if alias not in current_aliases:
                current_aliases.append(alias)
                masters.loc[idx[0], 'aliases'] = json.dumps(current_aliases, ensure_ascii=False)
                masters.to_csv(self.master_test_file, index=False, encoding='utf-8-sig')
    
    # Request 관련 메서드
    def load_requests(self):
        return pd.read_csv(self.request_info_file, encoding='utf-8-sig')
    
    def create_request(self, user_id, client, project, extracted_data):
        requests = self.load_requests()
        new_id = f"R{str(len(requests) + 1).zfill(5)}"
        new_request = pd.DataFrame([{
            'id': new_id,
            'user_id': user_id,
            'extracted_data': json.dumps(extracted_data, ensure_ascii=False),
            'final_data': '',
            'is_verified': False,
            'client': client,
            'project': project
        }])
        requests = pd.concat([requests, new_request], ignore_index=True)
        requests.to_csv(self.request_info_file, index=False, encoding='utf-8-sig')
        return new_id
    
    def update_request_final_data(self, request_id, final_data):
        requests = self.load_requests()
        idx = requests[requests['id'] == request_id].index
        if len(idx) > 0:
            requests.loc[idx[0], 'final_data'] = json.dumps(final_data, ensure_ascii=False)
            requests.to_csv(self.request_info_file, index=False, encoding='utf-8-sig')
    
    def get_user_requests(self, user_id):
        requests = self.load_requests()
        return requests[requests['user_id'] == user_id]
    
    # Test Item 관련 메서드
    def load_test_items(self):
        df = pd.read_csv(self.test_item_file, encoding='utf-8-sig')
        if 'custom_specs' in df.columns:
            df['custom_specs'] = df['custom_specs'].apply(
                lambda x: json.loads(x) if pd.notna(x) and x != '' else {}
            )
        return df
    
    def save_test_items(self, test_items):
        """시험 항목들을 Test_Item.csv에 저장"""
        existing_items = self.load_test_items()
        
        # 새로운 항목들을 DataFrame으로 변환
        new_items = pd.DataFrame(test_items)
        
        # custom_specs를 JSON 문자열로 변환
        if 'custom_specs' in new_items.columns:
            new_items['custom_specs'] = new_items['custom_specs'].apply(
                lambda x: json.dumps(x, ensure_ascii=False) if isinstance(x, dict) else x
            )
        
        # 기존 데이터와 병합
        all_items = pd.concat([existing_items, new_items], ignore_index=True)
        all_items.to_csv(self.test_item_file, index=False, encoding='utf-8-sig')
    
    def get_request_test_items(self, request_id):
        """특정 의뢰의 시험 항목들을 조회"""
        test_items = self.load_test_items()
        return test_items[test_items['request_id'] == request_id]
    
    def get_user_all_test_items(self, user_id):
        """특정 사용자의 모든 시험 항목들을 조회"""
        requests = self.get_user_requests(user_id)
        request_ids = requests['id'].tolist()
        test_items = self.load_test_items()
        return test_items[test_items['request_id'].isin(request_ids)]
