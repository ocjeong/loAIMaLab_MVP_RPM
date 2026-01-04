import pandas as pd
import os
from datetime import datetime
import json

class DataManager:
    """데이터 관리 클래스"""
    
    def __init__(self):
        self.data_dir = "data"
        self.ensure_data_directory()
        self.initialize_csv_files()
    
    def ensure_data_directory(self):
        """데이터 디렉토리 생성"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def initialize_csv_files(self):
        """CSV 파일 초기화"""
        # User List
        user_file = os.path.join(self.data_dir, "User_List.csv")
        if not os.path.exists(user_file):
            df = pd.DataFrame(columns=['id', 'user_name', 'created_date', 'last_access'])
            # 기본 사용자 추가
            df.loc[0] = ['U001', '기본사용자', datetime.now().strftime('%Y-%m-%d'), datetime.now().strftime('%Y-%m-%d')]
            df.to_csv(user_file, index=False, encoding='utf-8-sig')
        
        # Master Test
        master_file = os.path.join(self.data_dir, "Master_Test.csv")
        if not os.path.exists(master_file):
            df = pd.DataFrame(columns=['id', 'std_name', 'std_category', 'aliases', 'ref_standard'])
            # 샘플 데이터
            df.loc[0] = ['M001', 'On & Off Test', 'Endurance Test', '["작동성 시험", "온오프"]', 'ISO 16750-3']
            df.loc[1] = ['M002', 'High Temperature Test', 'Environmental Test', '["고온 시험", "내열"]', 'ISO 16750-4']
            df.loc[2] = ['M003', 'Low Temperature Test', 'Environmental Test', '["저온 시험", "내한"]', 'ISO 16750-4']
            df.loc[3] = ['M004', 'Vibration Test', 'Mechanical Test', '["진동 시험", "내진동"]', 'ISO 16750-3']
            df.loc[4] = ['M005', 'Noise Test', 'Performance Test', '["소음 시험", "음향"]', '']
            df.loc[5] = ['M006', 'Undervoltage and Overvoltage Test', 'Electrical Tests', '["과저전압", "정지 전압 확인"]', 'ISO 16750-3']
            df.to_csv(master_file, index=False, encoding='utf-8-sig')
        
        # Request Info
        request_file = os.path.join(self.data_dir, "Request_Info.csv")
        if not os.path.exists(request_file):
            df = pd.DataFrame(columns=['id', 'user_id', 'extracted_data', 'final_data', 'is_verified', 'client', 'project'])
            df.to_csv(request_file, index=False, encoding='utf-8-sig')
        
        # Test Item
        test_file = os.path.join(self.data_dir, "Test_Item.csv")
        if not os.path.exists(test_file):
            df = pd.DataFrame(columns=[
                'test_name', 'category', 'ref_standard', 'sample_assembly',
                'test_sample_no', 'sample_count', 'test_duration', 'test_equipment',
                'test_master_id', 'custom_specs', 'request_id'
            ])
            df.to_csv(test_file, index=False, encoding='utf-8-sig')
    
    def load_user_list_data(self):
        """사용자 목록 로드"""
        file_path = os.path.join(self.data_dir, "User_List.csv")
        return pd.read_csv(file_path, encoding='utf-8-sig')
    
    def load_master_test_data(self):
        """마스터 테스트 데이터 로드"""
        file_path = os.path.join(self.data_dir, "Master_Test.csv")
        return pd.read_csv(file_path, encoding='utf-8-sig')
    
    def load_request_info_data(self):
        """의뢰 정보 데이터 로드"""
        file_path = os.path.join(self.data_dir, "Request_Info.csv")
        return pd.read_csv(file_path, encoding='utf-8-sig')
    
    def load_test_item_data(self):
        """시험 항목 데이터 로드"""
        file_path = os.path.join(self.data_dir, "Test_Item.csv")
        return pd.read_csv(file_path, encoding='utf-8-sig')
    
    def add_user(self, user_name):
        """사용자 추가"""
        try:
            df = self.load_user_list_data()
            
            # 중복 확인
            if user_name in df['user_name'].values:
                return False
            
            # 새 ID 생성
            if df.empty:
                new_id = "U001"
            else:
                last_id = df['id'].iloc[-1]
                num = int(last_id[1:]) + 1
                new_id = f"U{num:03d}"
            
            # 새 사용자 추가
            new_row = {
                'id': new_id,
                'user_name': user_name,
                'created_date': datetime.now().strftime('%Y-%m-%d'),
                'last_access': datetime.now().strftime('%Y-%m-%d')
            }
            
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            df.to_csv(os.path.join(self.data_dir, "User_List.csv"), index=False, encoding='utf-8-sig')
            
            return True
        except Exception as e:
            print(f"Error adding user: {e}")
            return False
    
    def update_last_access(self, user_id):
        """마지막 접속 시간 업데이트"""
        try:
            df = self.load_user_list_data()
            df.loc[df['id'] == user_id, 'last_access'] = datetime.now().strftime('%Y-%m-%d')
            df.to_csv(os.path.join(self.data_dir, "User_List.csv"), index=False, encoding='utf-8-sig')
        except Exception as e:
            print(f"Error updating last access: {e}")
    
    def save_request_data(self, user_id, request_info, test_items):
        """의뢰 데이터 저장"""
        try:
            # Request Info 저장
            requests_df = self.load_request_info_data()
            
            # 새 Request ID 생성
            if requests_df.empty:
                new_id = "R00001"
            else:
                last_id = requests_df['id'].iloc[-1]
                num = int(last_id[1:]) + 1
                new_id = f"R{num:05d}"
            
            new_request = {
                'id': new_id,
                'user_id': user_id,
                'extracted_data': json.dumps(test_items, ensure_ascii=False),
                'final_data': json.dumps(test_items, ensure_ascii=False),
                'is_verified': False,
                'client': request_info.get('client', ''),
                'project': request_info.get('project', '')
            }
            
            requests_df = pd.concat([requests_df, pd.DataFrame([new_request])], ignore_index=True)
            requests_df.to_csv(os.path.join(self.data_dir, "Request_Info.csv"), index=False, encoding='utf-8-sig')
            
            # Test Items 저장
            test_items_df = self.load_test_item_data()
            
            for item in test_items:
                item['request_id'] = new_id
                test_items_df = pd.concat([test_items_df, pd.DataFrame([item])], ignore_index=True)
            
            test_items_df.to_csv(os.path.join(self.data_dir, "Test_Item.csv"), index=False, encoding='utf-8-sig')
            
            # 마스터 데이터 업데이트 (유사어 추가)
            self.update_master_data(test_items)
            
            return True
        except Exception as e:
            print(f"Error saving request data: {e}")
            return False
    
    def update_master_data(self, test_items):
        """마스터 데이터 업데이트"""
        try:
            master_df = self.load_master_test_data()
            
            for item in test_items:
                test_name = item.get('test_name', '')
                master_id = item.get('test_master_id', '')
                
                if master_id and master_id in master_df['id'].values:
                    # 기존 마스터에 유사어 추가
                    idx = master_df[master_df['id'] == master_id].index[0]
                    aliases = master_df.at[idx, 'aliases']
                    
                    try:
                        aliases_list = json.loads(aliases)
                    except:
                        aliases_list = []
                    
                    if test_name not in aliases_list:
                        aliases_list.append(test_name)
                        master_df.at[idx, 'aliases'] = json.dumps(aliases_list, ensure_ascii=False)
                
                elif not master_id and test_name:
                    # 새 마스터 추가
                    if master_df.empty:
                        new_id = "M001"
                    else:
                        last_id = master_df['id'].iloc[-1]
                        num = int(last_id[1:]) + 1
                        new_id = f"M{num:03d}"
                    
                    new_master = {
                        'id': new_id,
                        'std_name': test_name,
                        'std_category': item.get('category', ''),
                        'aliases': json.dumps([test_name], ensure_ascii=False),
                        'ref_standard': item.get('ref_standard', '')
                    }
                    
                    master_df = pd.concat([master_df, pd.DataFrame([new_master])], ignore_index=True)
            
            master_df.to_csv(os.path.join(self.data_dir, "Master_Test.csv"), index=False, encoding='utf-8-sig')
        except Exception as e:
            print(f"Error updating master data: {e}")
