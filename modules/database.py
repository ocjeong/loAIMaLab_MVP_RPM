import pandas as pd
import os
from datetime import datetime
import json

class Database:
    def __init__(self):
        self.data_dir = 'data'
        self.ensure_data_directory()
        self.initialize_csv_files()
    
    def ensure_data_directory(self):
        """데이터 디렉토리 생성"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def initialize_csv_files(self):
        """CSV 파일 초기화"""
        # User List
        user_list_path = os.path.join(self.data_dir, 'User_List.csv')
        if not os.path.exists(user_list_path):
            df_users = pd.DataFrame(columns=['id', 'user_name', 'created_date', 'last_access'])
            # 기본 사용자 추가
            df_users.loc[0] = ['U001', '기본사용자', datetime.now().strftime('%Y-%m-%d'), datetime.now().strftime('%Y-%m-%d')]
            df_users.to_csv(user_list_path, index=False, encoding='utf-8-sig')
        
        # Master Test
        master_test_path = os.path.join(self.data_dir, 'Master_Test.csv')
        if not os.path.exists(master_test_path):
            df_master = pd.DataFrame(columns=['id', 'std_name', 'std_category', 'aliases', 'ref_standard'])
            # 샘플 마스터 데이터
            sample_data = [
                ['M001', 'High Temperature Test', 'Environmental Tests', '["고온시험", "고온"]', 'ISO 16750-4'],
                ['M002', 'Low Temperature Test', 'Environmental Tests', '["저온시험", "저온"]', 'ISO 16750-4'],
                ['M003', 'Vibration Test', 'Mechanical Tests', '["진동시험", "진동"]', 'ISO 16750-3'],
                ['M004', 'Shock Test', 'Mechanical Tests', '["충격시험", "충격"]', 'ISO 16750-3'],
                ['M005', 'Dust Protection Test', 'Environmental Tests', '["방진시험", "분진"]', 'ISO 20653'],
                ['M006', 'Water Protection Test', 'Environmental Tests', '["방수시험", "침수"]', 'ISO 20653'],
                ['M007', 'Overvoltage Test', 'Electrical Tests', '["과전압", "고전압"]', 'ISO 16750-2'],
                ['M008', 'Undervoltage Test', 'Electrical Tests', '["저전압", "저전압시험"]', 'ISO 16750-2'],
                ['M009', 'Undervoltage and Overvoltage Test', 'Electrical Tests', '["과저전압", "정지 전압 확인"]', 'ISO 16750-3'],
                ['M010', 'Noise Test', 'Acoustic Tests', '["소음시험", "소음측정"]', ''],
            ]
            df_master = pd.DataFrame(sample_data, columns=['id', 'std_name', 'std_category', 'aliases', 'ref_standard'])
            df_master.to_csv(master_test_path, index=False, encoding='utf-8-sig')
        
        # Request Info
        request_info_path = os.path.join(self.data_dir, 'Request_Info.csv')
        if not os.path.exists(request_info_path):
            df_requests = pd.DataFrame(columns=['id', 'user_id', 'extracted_data', 'final_data', 'is_verified', 'client', 'project'])
            df_requests.to_csv(request_info_path, index=False, encoding='utf-8-sig')
        
        # Test Item
        test_item_path = os.path.join(self.data_dir, 'Test_Item.csv')
        if not os.path.exists(test_item_path):
            df_test_items = pd.DataFrame(columns=[
                'test_name', 'category', 'ref_standard', 'sample_assembly', 
                'test_sample_no', 'sample_count', 'test_duration', 'test_equipment',
                'test_master_id', 'custom_specs', 'request_id'
            ])
            df_test_items.to_csv(test_item_path, index=False, encoding='utf-8-sig')
    
    def get_all_users(self):
        """모든 사용자 조회"""
        user_list_path = os.path.join(self.data_dir, 'User_List.csv')
        return pd.read_csv(user_list_path, encoding='utf-8-sig')
    
    def add_user(self, user_name):
        """새 사용자 추가"""
        try:
            df_users = self.get_all_users()
            new_id = f"U{str(len(df_users) + 1).zfill(3)}"
            new_user = {
                'id': new_id,
                'user_name': user_name,
                'created_date': datetime.now().strftime('%Y-%m-%d'),
                'last_access': datetime.now().strftime('%Y-%m-%d')
            }
            df_users = pd.concat([df_users, pd.DataFrame([new_user])], ignore_index=True)
            user_list_path = os.path.join(self.data_dir, 'User_List.csv')
            df_users.to_csv(user_list_path, index=False, encoding='utf-8-sig')
            return True
        except Exception as e:
            print(f"Error adding user: {e}")
            return False
    
    def update_user_last_access(self, user_id):
        """사용자 마지막 접속 시간 업데이트"""
        try:
            user_list_path = os.path.join(self.data_dir, 'User_List.csv')
            df_users = pd.read_csv(user_list_path, encoding='utf-8-sig')
            df_users.loc[df_users['id'] == user_id, 'last_access'] = datetime.now().strftime('%Y-%m-%d')
            df_users.to_csv(user_list_path, index=False, encoding='utf-8-sig')
            return True
        except Exception as e:
            print(f"Error updating last access: {e}")
            return False
    
    def get_user_requests(self, user_id):
        """사용자의 모든 의뢰 조회"""
        request_info_path = os.path.join(self.data_dir, 'Request_Info.csv')
        df_requests = pd.read_csv(request_info_path, encoding='utf-8-sig')
        return df_requests[df_requests['user_id'] == user_id]
    
    def get_user_schedule(self, user_id):
        """사용자의 전체 시험 일정 조회"""
        # 실제 구현에서는 별도의 Schedule 테이블이 필요할 수 있음
        # 여기서는 간단히 Request와 Test Item을 조인하여 표시
        request_info_path = os.path.join(self.data_dir, 'Request_Info.csv')
        test_item_path = os.path.join(self.data_dir, 'Test_Item.csv')
        
        df_requests = pd.read_csv(request_info_path, encoding='utf-8-sig')
        df_test_items = pd.read_csv(test_item_path, encoding='utf-8-sig')
        
        user_requests = df_requests[df_requests['user_id'] == user_id]
        if user_requests.empty:
            return pd.DataFrame()
        
        request_ids = user_requests['id'].tolist()
        schedule = df_test_items[df_test_items['request_id'].isin(request_ids)]
        
        return schedule[['request_id', 'test_name', 'test_duration', 'sample_count']]
    
    def get_request_schedule(self, request_id):
        """특정 의뢰의 일정 조회"""
        test_item_path = os.path.join(self.data_dir, 'Test_Item.csv')
        df_test_items = pd.read_csv(test_item_path, encoding='utf-8-sig')
        
        schedule = df_test_items[df_test_items['request_id'] == request_id]
        return schedule[['test_name', 'test_duration', 'sample_count', 'test_equipment']]
    
    def save_request_data(self, user_id, data, request_id=None):
        """의뢰 데이터 저장"""
        try:
            request_info_path = os.path.join(self.data_dir, 'Request_Info.csv')
            test_item_path = os.path.join(self.data_dir, 'Test_Item.csv')
            
            df_requests = pd.read_csv(request_info_path, encoding='utf-8-sig')
            df_test_items = pd.read_csv(test_item_path, encoding='utf-8-sig')
            
            # 새 의뢰인 경우
            if request_id is None:
                request_id = f"R{str(len(df_requests) + 1).zfill(5)}"
                new_request = {
                    'id': request_id,
                    'user_id': user_id,
                    'extracted_data': json.dumps(data, ensure_ascii=False),
                    'final_data': json.dumps(data, ensure_ascii=False),
                    'is_verified': False,
                    'client': data.get('request_info', {}).get('client', ''),
                    'project': data.get('request_info', {}).get('project', '')
                }
                df_requests = pd.concat([df_requests, pd.DataFrame([new_request])], ignore_index=True)
            else:
                # 기존 의뢰 업데이트
                df_requests.loc[df_requests['id'] == request_id, 'final_data'] = json.dumps(data, ensure_ascii=False)
                df_requests.loc[df_requests['id'] == request_id, 'client'] = data.get('request_info', {}).get('client', '')
                df_requests.loc[df_requests['id'] == request_id, 'project'] = data.get('request_info', {}).get('project', '')
                
                # 기존 테스트 항목 삭제
                df_test_items = df_test_items[df_test_items['request_id'] != request_id]
            
            # 테스트 항목 저장
            for item in data.get('test_items', []):
                new_item = {
                    'test_name': item.get('test_name', ''),
                    'category': item.get('category', ''),
                    'ref_standard': item.get('ref_standard', ''),
                    'sample_assembly': item.get('sample_assembly', ''),
                    'test_sample_no': item.get('test_sample_no', ''),
                    'sample_count': item.get('sample_count', ''),
                    'test_duration': item.get('test_duration', ''),
                    'test_equipment': item.get('test_instrument', ''),
                    'test_master_id': item.get('test_master_id', ''),
                    'custom_specs': json.dumps(item.get('custom_specs', {}), ensure_ascii=False),
                    'request_id': request_id
                }
                df_test_items = pd.concat([df_test_items, pd.DataFrame([new_item])], ignore_index=True)
            
            # 저장
            df_requests.to_csv(request_info_path, index=False, encoding='utf-8-sig')
            df_test_items.to_csv(test_item_path, index=False, encoding='utf-8-sig')
            
            return request_id
        except Exception as e:
            print(f"Error saving request data: {e}")
            return None
    
    def get_request_data(self, request_id):
        """의뢰 데이터 조회"""
        try:
            request_info_path = os.path.join(self.data_dir, 'Request_Info.csv')
            df_requests = pd.read_csv(request_info_path, encoding='utf-8-sig')
            
            request = df_requests[df_requests['id'] == request_id]
            if request.empty:
                return None
            
            final_data = request.iloc[0]['final_data']
            return json.loads(final_data)
        except Exception as e:
            print(f"Error getting request data: {e}")
            return None
    
    def get_master_tests(self):
        """마스터 테스트 데이터 조회"""
        master_test_path = os.path.join(self.data_dir, 'Master_Test.csv')
        return pd.read_csv(master_test_path, encoding='utf-8-sig')
    
    def save_schedule(self, request_id, user_id, schedule_df):
        """일정 저장 (Test Item에 일정 정보 업데이트)"""
        try:
            # 실제 구현에서는 별도의 Schedule 테이블을 만들 수 있음
            # 여기서는 간단히 성공 반환
            return True
        except Exception as e:
            print(f"Error saving schedule: {e}")
            return False
    
    def get_statistics(self):
        """통계 정보 조회"""
        try:
            df_users = self.get_all_users()
            request_info_path = os.path.join(self.data_dir, 'Request_Info.csv')
            test_item_path = os.path.join(self.data_dir, 'Test_Item.csv')
            
            df_requests = pd.read_csv(request_info_path, encoding='utf-8-sig')
            df_test_items = pd.read_csv(test_item_path, encoding='utf-8-sig')
            
            return {
                'total_users': len(df_users),
                'total_requests': len(df_requests),
                'total_test_items': len(df_test_items)
            }
        except Exception as e:
            print(f"Error getting statistics: {e}")
            return {'total_users': 0, 'total_requests': 0, 'total_test_items': 0}
