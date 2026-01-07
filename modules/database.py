import pandas as pd
import os
from datetime import datetime
import json


class DatabaseManager:
    """데이터베이스 관리 클래스"""
    
    def __init__(self, data_dir='data'):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        
        self.master_file = os.path.join(data_dir, 'Master_Test.csv')
        self.request_file = os.path.join(data_dir, 'Request_Info.csv')
        self.test_item_file = os.path.join(data_dir, 'Test_Item.csv')
        self.user_file = os.path.join(data_dir, 'User_List.csv')
        
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
                    'EMC Test',
                    'Undervoltage and Overvoltage Test'
                ],
                'std_category': [
                    'Endurance Test',
                    'Environmental Test',
                    'Environmental Test',
                    'Performance Test',
                    'Mechanical Test',
                    'Environmental Test',
                    'Environmental Test',
                    'Electrical Tests',
                    'Electrical Tests'
                ],
                'aliases': [
                    json.dumps(['작동성 시험', '온오프', 'On/Off']),
                    json.dumps(['고온 시험', '고온 내구', 'High Temp']),
                    json.dumps(['저온 시험', '저온 내구', 'Low Temp']),
                    json.dumps(['소음 시험', '노이즈', 'Sound']),
                    json.dumps(['진동 시험', 'Vibration']),
                    json.dumps(['분진 시험', 'Dust']),
                    json.dumps(['방수 시험', 'Water']),
                    json.dumps(['전자파 적합성', 'EMI/EMC']),
                    json.dumps(['과저전압', '정지 전압 확인', 'Under/Over Voltage'])
                ],
                'ref_standard': [
                    '',
                    'ISO 16750-4',
                    'ISO 16750-4',
                    '',
                    'ISO 16750-3',
                    'ISO 20653',
                    'ISO 20653',
                    'ISO 11452',
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
            pd.DataFrame(columns=[
                'id', 'user_id', 'extracted_data', 'final_data',
                'is_verified', 'client', 'project', 'created_date'
            ]).to_csv(self.request_file, index=False, encoding='utf-8-sig')
        
        # Test Item Data
        if not os.path.exists(self.test_item_file):
            pd.DataFrame(columns=[
                'test_name', 'test_name_original', 'category', 'category_original',
                'ref_standard', 'sample_assembly', 'test_sample_no', 'sample_count',
                'test_duration', 'test_equipment', 'test_master_id', 'custom_specs',
                'request_id'
            ]).to_csv(self.test_item_file, index=False, encoding='utf-8-sig')
    
    # User 관련 메서드
    def get_all_users(self):
        """모든 사용자 조회"""
        df = pd.read_csv(self.user_file, encoding='utf-8-sig')
        return df.to_dict('records')
    
    def add_user(self, user_name):
        """사용자 추가"""
        df = pd.read_csv(self.user_file, encoding='utf-8-sig')
        
        # 새 ID 생성
        if len(df) > 0:
            last_id = df['id'].iloc[-1]
            new_id = f"U{int(last_id[1:]) + 1:03d}"
        else:
            new_id = "U001"
        
        new_user = {
            'id': new_id,
            'user_name': user_name,
            'created_date': datetime.now().strftime('%Y-%m-%d'),
            'last_access': datetime.now().strftime('%Y-%m-%d')
        }
        
        df = pd.concat([df, pd.DataFrame([new_user])], ignore_index=True)
        df.to_csv(self.user_file, index=False, encoding='utf-8-sig')
        
        return new_id
    
    def update_user_last_access(self, user_id):
        """사용자 마지막 접속 시간 업데이트"""
        df = pd.read_csv(self.user_file, encoding='utf-8-sig')
        df.loc[df['id'] == user_id, 'last_access'] = datetime.now().strftime('%Y-%m-%d')
        df.to_csv(self.user_file, index=False, encoding='utf-8-sig')
    
    # Request 관련 메서드
    def create_request(self, user_id, client, project, extracted_data, final_data):
        """새 의뢰 생성"""
        df = pd.read_csv(self.request_file, encoding='utf-8-sig')
        
        # 새 ID 생성
        if len(df) > 0:
            last_id = df['id'].iloc[-1]
            new_id = f"R{int(last_id[1:]) + 1:05d}"
        else:
            new_id = "R00001"
        
        new_request = {
            'id': new_id,
            'user_id': user_id,
            'extracted_data': json.dumps(extracted_data),
            'final_data': json.dumps(final_data),
            'is_verified': False,
            'client': client,
            'project': project,
            'created_date': datetime.now().strftime('%Y-%m-%d')
        }
        
        df = pd.concat([df, pd.DataFrame([new_request])], ignore_index=True)
        df.to_csv(self.request_file, index=False, encoding='utf-8-sig')
        
        return new_id
    
    def get_user_requests(self, user_id):
        """사용자의 모든 의뢰 조회"""
        df = pd.read_csv(self.request_file, encoding='utf-8-sig')
        user_requests = df[df['user_id'] == user_id]
        return user_requests.to_dict('records')
    
    def get_request_by_id(self, request_id):
        """ID로 의뢰 조회"""
        df = pd.read_csv(self.request_file, encoding='utf-8-sig')
        request = df[df['id'] == request_id]
        
        if len(request) > 0:
            request_dict = request.iloc[0].to_dict()
            
            # JSON 문자열을 파이썬 객체로 변환
            if isinstance(request_dict.get('extracted_data'), str):
                request_dict['extracted_data'] = json.loads(request_dict['extracted_data'])
            if isinstance(request_dict.get('final_data'), str):
                request_dict['final_data'] = json.loads(request_dict['final_data'])
            
            return request_dict
        return None
    
    def update_request_final_data(self, request_id, final_data):
        """의뢰의 최종 데이터 업데이트"""
        df = pd.read_csv(self.request_file, encoding='utf-8-sig')
        df.loc[df['id'] == request_id, 'final_data'] = json.dumps(final_data)
        df.to_csv(self.request_file, index=False, encoding='utf-8-sig')
    
    # Master 관련 메서드
    def get_all_masters(self):
        """모든 마스터 데이터 조회"""
        df = pd.read_csv(self.master_file, encoding='utf-8-sig')
        masters = df.to_dict('records')
        
        # aliases를 리스트로 변환
        for master in masters:
            if isinstance(master.get('aliases'), str):
                master['aliases'] = json.loads(master['aliases'])
        
        return masters
    
    def get_master_by_id(self, master_id):
        """ID로 마스터 데이터 조회"""
        df = pd.read_csv(self.master_file, encoding='utf-8-sig')
        master = df[df['id'] == master_id]
        
        if len(master) > 0:
            master_dict = master.iloc[0].to_dict()
            
            # aliases를 리스트로 변환
            if isinstance(master_dict.get('aliases'), str):
                master_dict['aliases'] = json.loads(master_dict['aliases'])
            
            return master_dict
        return None
    
    def update_master_aliases(self, master_id, new_alias):
        """마스터 데이터의 유사어 업데이트"""
        df = pd.read_csv(self.master_file, encoding='utf-8-sig')
        
        idx = df[df['id'] == master_id].index
        if len(idx) > 0:
            aliases = json.loads(df.loc[idx[0], 'aliases'])
            
            if new_alias not in aliases:
                aliases.append(new_alias)
                df.loc[idx[0], 'aliases'] = json.dumps(aliases)
                df.to_csv(self.master_file, index=False, encoding='utf-8-sig')
    
    def add_master_test(self, std_name, std_category, ref_standard, aliases):
        """새 마스터 테스트 추가"""
        df = pd.read_csv(self.master_file, encoding='utf-8-sig')
        
        # 새 ID 생성
        if len(df) > 0:
            last_id = df['id'].iloc[-1]
            new_id = f"M{int(last_id[1:]) + 1:03d}"
        else:
            new_id = "M001"
        
        new_master = {
            'id': new_id,
            'std_name': std_name,
            'std_category': std_category,
            'aliases': json.dumps(aliases),
            'ref_standard': ref_standard
        }
        
        df = pd.concat([df, pd.DataFrame([new_master])], ignore_index=True)
        df.to_csv(self.master_file, index=False, encoding='utf-8-sig')
        
        return new_id
    
    # Schedule 관련 메서드
    def save_schedules(self, user_id, request_id, schedules):
        """일정 저장 (Test Item Data에 저장)"""
        df = pd.read_csv(self.test_item_file, encoding='utf-8-sig')
        
        # 기존 해당 의뢰의 데이터 삭제
        df = df[df['request_id'] != request_id]
        
        # 새 데이터 추가
        for schedule in schedules:
            schedule['request_id'] = request_id
            df = pd.concat([df, pd.DataFrame([schedule])], ignore_index=True)
        
        df.to_csv(self.test_item_file, index=False, encoding='utf-8-sig')
    
    def get_user_schedules(self, user_id):
        """사용자의 모든 일정 조회"""
        # Request에서 user의 request_id 조회
        request_df = pd.read_csv(self.request_file, encoding='utf-8-sig')
        user_requests = request_df[request_df['user_id'] == user_id]['id'].tolist()
        
        # Test Item에서 해당 request_id의 일정 조회
        test_item_df = pd.read_csv(self.test_item_file, encoding='utf-8-sig')
        schedules = test_item_df[test_item_df['request_id'].isin(user_requests)]
        
        return schedules.to_dict('records')
    
    # Export 관련 메서드
    def export_to_csv(self, data_type):
        """데이터를 CSV로 내보내기"""
        if data_type == 'master':
            df = pd.read_csv(self.master_file, encoding='utf-8-sig')
        elif data_type == 'request':
            df = pd.read_csv(self.request_file, encoding='utf-8-sig')
        elif data_type == 'test_item':
            df = pd.read_csv(self.test_item_file, encoding='utf-8-sig')
        elif data_type == 'user':
            df = pd.read_csv(self.user_file, encoding='utf-8-sig')
