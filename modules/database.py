import streamlit as st
import pandas as pd
import os
from datetime import datetime
import json

class Database:
    def __init__(self):
        self.data_dir = 'data'
        os.makedirs(self.data_dir, exist_ok=True)
        
        # CSV 파일 경로
        self.user_list_path = os.path.join(self.data_dir, 'User_List.csv')
        self.master_test_path = os.path.join(self.data_dir, 'Master_Test.csv')
        self.request_info_path = os.path.join(self.data_dir, 'Request_Info.csv')
        self.test_item_path = os.path.join(self.data_dir, 'Test_Item.csv')
        
        # 데이터프레임 초기화
        self.user_list_df = self._load_or_create_user_list()
        self.master_test_df = self._load_or_create_master_test()
        self.request_info_df = self._load_or_create_request_info()
        self.test_item_df = self._load_or_create_test_item()
    
    def _load_or_create_user_list(self):
        if os.path.exists(self.user_list_path):
            return pd.read_csv(self.user_list_path)
        else:
            df = pd.DataFrame(columns=['id', 'user_name', 'created_date', 'last_access'])
            # 기본 사용자 추가
            df = pd.concat([df, pd.DataFrame([{
                'id': 'U001',
                'user_name': '기본사용자',
                'created_date': datetime.now().strftime('%Y-%m-%d'),
                'last_access': datetime.now().strftime('%Y-%m-%d')
            }])], ignore_index=True)
            df.to_csv(self.user_list_path, index=False)
            return df
    
    def _load_or_create_master_test(self):
        if os.path.exists(self.master_test_path):
            return pd.read_csv(self.master_test_path)
        else:
            # 초기 마스터 데이터
            df = pd.DataFrame([
                {
                    'id': 'M001',
                    'std_name': 'On & Off Test',
                    'std_category': 'Endurance Test',
                    'aliases': '["작동성 시험", "온오프", "On/Off Test"]',
                    'ref_standard': 'ISO 16750-3'
                },
                {
                    'id': 'M002',
                    'std_name': 'High Temperature Test',
                    'std_category': 'Environmental Test',
                    'aliases': '["고온 시험", "고온 내구", "High Temp"]',
                    'ref_standard': 'ISO 16750-4'
                },
                {
                    'id': 'M003',
                    'std_name': 'Low Temperature Test',
                    'std_category': 'Environmental Test',
                    'aliases': '["저온 시험", "저온 내구", "Low Temp"]',
                    'ref_standard': 'ISO 16750-4'
                },
                {
                    'id': 'M004',
                    'std_name': 'Vibration Test',
                    'std_category': 'Mechanical Test',
                    'aliases': '["진동 시험", "Random Vibration", "Sine Vibration"]',
                    'ref_standard': 'ISO 16750-3'
                },
                {
                    'id': 'M005',
                    'std_name': 'Noise Test',
                    'std_category': 'Acoustic Test',
                    'aliases': '["소음 시험", "소음 측정", "Acoustic Test"]',
                    'ref_standard': ''
                },
                {
                    'id': 'M006',
                    'std_name': 'Dust Protection Test',
                    'std_category': 'Environmental Test',
                    'aliases': '["방진 시험", "분진 시험", "IP Test"]',
                    'ref_standard': 'ISO 20653'
                },
                {
                    'id': 'M007',
                    'std_name': 'Water Protection Test',
                    'std_category': 'Environmental Test',
                    'aliases': '["방수 시험", "침수 시험", "IPX Test"]',
                    'ref_standard': 'ISO 20653'
                },
                {
                    'id': 'M008',
                    'std_name': 'Salt Spray Test',
                    'std_category': 'Corrosion Test',
                    'aliases': '["염수 분무", "부식 시험", "Corrosion Test"]',
                    'ref_standard': 'ISO 9227'
                },
                {
                    'id': 'M009',
                    'std_name': 'Undervoltage and Overvoltage Test',
                    'std_category': 'Electrical Test',
                    'aliases': '["과저전압", "정지 전압 확인", "Voltage Test"]',
                    'ref_standard': 'ISO 16750-3'
                },
                {
                    'id': 'M010',
                    'std_name': 'EMC Test',
                    'std_category': 'Electrical Test',
                    'aliases': '["전자파 적합성", "EMI/EMS", "Electromagnetic Compatibility"]',
                    'ref_standard': 'ISO 11452'
                }
            ])
            df.to_csv(self.master_test_path, index=False)
            return df
    
    def _load_or_create_request_info(self):
        if os.path.exists(self.request_info_path):
            return pd.read_csv(self.request_info_path)
        else:
            df = pd.DataFrame(columns=['id', 'user_id', 'extracted_data', 'final_data', 
                                       'is_verified', 'client', 'project', 'created_date'])
            df.to_csv(self.request_info_path, index=False)
            return df
    
    def _load_or_create_test_item(self):
        if os.path.exists(self.test_item_path):
            return pd.read_csv(self.test_item_path)
        else:
            df = pd.DataFrame(columns=['test_name', 'test_name_original', 'category', 
                                       'category_original', 'ref_standard', 'sample_assembly',
                                       'test_sample_no', 'sample_count', 'test_duration',
                                       'test_equipment', 'test_master_id', 'custom_specs', 
                                       'request_id'])
            df.to_csv(self.test_item_path, index=False)
            return df
    
    def get_user_list(self):
        return self.user_list_df
    
    def add_user(self, user_name):
        new_id = f"U{str(len(self.user_list_df) + 1).zfill(3)}"
        new_user = pd.DataFrame([{
            'id': new_id,
            'user_name': user_name,
            'created_date': datetime.now().strftime('%Y-%m-%d'),
            'last_access': datetime.now().strftime('%Y-%m-%d')
        }])
        self.user_list_df = pd.concat([self.user_list_df, new_user], ignore_index=True)
        self.user_list_df.to_csv(self.user_list_path, index=False)
    
    def update_last_access(self, user_id):
        self.user_list_df.loc[self.user_list_df['id'] == user_id, 'last_access'] = \
            datetime.now().strftime('%Y-%m-%d')
        self.user_list_df.to_csv(self.user_list_path, index=False)
    
    def get_user_requests(self, user_id):
        return self.request_info_df[self.request_info_df['user_id'] == user_id]
    
    def get_request_by_id(self, request_id):
        result = self.request_info_df[self.request_info_df['id'] == request_id]
        if not result.empty:
            return result.iloc[0]
        return None
    
    def save_request(self, user_id, client, project, extracted_data, final_data):
        # 기존 request_id 확인 (수정 모드인 경우)
        if st.session_state.current_request:
            # 기존 의뢰 업데이트
            idx = self.request_info_df[self.request_info_df['id'] == st.session_state.current_request].index
            if not idx.empty:
                self.request_info_df.loc[idx[0], 'final_data'] = json.dumps(final_data, ensure_ascii=False)
                self.request_info_df.loc[idx[0], 'client'] = client
                self.request_info_df.loc[idx[0], 'project'] = project
                self.request_info_df.to_csv(self.request_info_path, index=False)
                
                # 기존 Test Item 삭제 후 재저장
                self.test_item_df = self.test_item_df[
                    self.test_item_df['request_id'] != st.session_state.current_request
                ]
                for item in final_data:
                    self.save_test_item(item, st.session_state.current_request)
                
                return st.session_state.current_request
        
        # 새 의뢰 생성
        new_id = f"R{str(len(self.request_info_df) + 1).zfill(5)}"
        
        new_request = pd.DataFrame([{
            'id': new_id,
            'user_id': user_id,
            'extracted_data': json.dumps(extracted_data, ensure_ascii=False),
            'final_data': json.dumps(final_data, ensure_ascii=False),
            'is_verified': False,
            'client': client,
            'project': project,
            'created_date': datetime.now().strftime('%Y-%m-%d')
        }])
        
        self.request_info_df = pd.concat([self.request_info_df, new_request], ignore_index=True)
        self.request_info_df.to_csv(self.request_info_path, index=False)
        
        # Test Item 저장
        for item in final_data:
            self.save_test_item(item, new_id)
        
        return new_id
    
    def save_test_item(self, item, request_id):
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
        
        self.test_item_df = pd.concat([self.test_item_df, new_item], ignore_index=True)
        self.test_item_df.to_csv(self.test_item_path, index=False)
    
    def update_master_aliases(self, master_id, new_alias):
        idx = self.master_test_df[self.master_test_df['id'] == master_id].index
        if not idx.empty:
            current_aliases = eval(self.master_test_df.loc[idx[0], 'aliases'])
            if new_alias not in current_aliases:
                current_aliases.append(new_alias)
                self.master_test_df.loc[idx[0], 'aliases'] = json.dumps(current_aliases, ensure_ascii=False)
                self.master_test_df.to_csv(self.master_test_path, index=False)
    
    def add_new_master(self, item):
        new_id = f"M{str(len(self.master_test_df) + 1).zfill(3)}"
        
        new_master = pd.DataFrame([{
            'id': new_id,
            'std_name': item.get('test_name', ''),
            'std_category': item.get('category', ''),
            'aliases': json.dumps([item.get('test_name_original', '')], ensure_ascii=False),
            'ref_standard': item.get('ref_standard', '')
        }])
        
        self.master_test_df = pd.concat([self.master_test_df, new_master], ignore_index=True)
        self.master_test_df.to_csv(self.master_test_path, index=False)
        
        return new_id
    
    def get_user_schedule(self, user_id):
        # 사용자의 모든 요청에 대한 일정 반환
        user_requests = self.get_user_requests(user_id)
        schedule_data = []
        
        for _, request in user_requests.iterrows():
            test_items = json.loads(request['final_data'])
            for item in test_items:
                schedule_data.append({
                    'Task': item.get('test_name', ''),
                    'Request': request['id'],
                    'Duration': item.get('test_duration', '1')
                })
        
        return pd.DataFrame(schedule_data)
    
    def save_schedule(self, user_id, request_id, test_name, start_day, duration, start_date):
        # 실제 구현에서는 별도의 Schedule 테이블에 저장
        pass
