import pandas as pd
import os
from datetime import datetime
import json

class DatabaseManager:
    def __init__(self):
        self.data_dir = 'data'
        os.makedirs(self.data_dir, exist_ok=True)
        
        self.user_file = os.path.join(self.data_dir, 'User_List.csv')
        self.master_file = os.path.join(self.data_dir, 'Master_Test.csv')
        self.request_file = os.path.join(self.data_dir, 'Request_Info.csv')
        self.test_item_file = os.path.join(self.data_dir, 'Test_Item.csv')
        
        self._initialize_files()
    
    def _initialize_files(self):
        """CSV 파일 초기화"""
        # User List
        if not os.path.exists(self.user_file):
            df = pd.DataFrame(columns=['id', 'user_name', 'created_date', 'last_access'])
            # 기본 사용자 추가
            df.loc[0] = ['U001', '기본사용자', datetime.now().strftime('%Y-%m-%d'), datetime.now().strftime('%Y-%m-%d')]
            df.to_csv(self.user_file, index=False, encoding='utf-8-sig')
        
        # Master Test
        if not os.path.exists(self.master_file):
            df = pd.DataFrame(columns=['id', 'std_name', 'std_category', 'aliases', 'ref_standard'])
            # 샘플 데이터
            sample_data = [
                ['M001', 'High Temperature Test', 'Environmental Tests', '고온시험,고온테스트', 'ISO 16750-3'],
                ['M002', 'Low Temperature Test', 'Environmental Tests', '저온시험,저온테스트', 'ISO 16750-3'],
                ['M003', 'Thermal Shock Test', 'Environmental Tests', '열충격시험', 'ISO 16750-3'],
                ['M004', 'Humidity Test', 'Environmental Tests', '습도시험,내습성', 'ISO 16750-3'],
                ['M005', 'Vibration Test', 'Mechanical Tests', '진동시험,내진동', 'ISO 16750-3'],
                ['M006', 'Mechanical Shock Test', 'Mechanical Tests', '기계적충격', 'ISO 16750-3'],
                ['M007', 'Voltage Test', 'Electrical Tests', '전압시험', 'ISO 16750-2'],
                ['M008', 'Current Test', 'Electrical Tests', '전류시험', 'ISO 16750-2'],
                ['M009', 'Undervoltage and Overvoltage Test', 'Electrical Tests', '과저전압,정지전압확인', 'ISO 16750-3'],
                ['M010', 'Noise Test', 'Performance Tests', '소음시험,노이즈', ''],
            ]
            df = pd.DataFrame(sample_data, columns=['id', 'std_name', 'std_category', 'aliases', 'ref_standard'])
            df.to_csv(self.master_file, index=False, encoding='utf-8-sig')
        
        # Request Info
        if not os.path.exists(self.request_file):
            df = pd.DataFrame(columns=['id', 'user_id', 'extracted_data', 'final_data', 'is_verified', 'client', 'project'])
            df.to_csv(self.request_file, index=False, encoding='utf-8-sig')
        
        # Test Item
        if not os.path.exists(self.test_item_file):
            df = pd.DataFrame(columns=[
                'test_name', 'category', 'ref_standard', 'sample_assembly',
                'test_sample_no', 'sample_count', 'test_duration', 'test_equipment',
                'test_master_id', 'custom_specs', 'request_id'
            ])
            df.to_csv(self.test_item_file, index=False, encoding='utf-8-sig')
    
    def get_users(self):
        """사용자 목록 조회"""
        return pd.read_csv(self.user_file, encoding='utf-8-sig')
    
    def add_user(self, user_name):
        """사용자 추가"""
        df = self.get_users()
        new_id = f"U{str(len(df) + 1).zfill(3)}"
        new_user = pd.DataFrame([{
            'id': new_id,
            'user_name': user_name,
            'created_date': datetime.now().strftime('%Y-%m-%d'),
            'last_access': datetime.now().strftime('%Y-%m-%d')
        }])
        df = pd.concat([df, new_user], ignore_index=True)
        df.to_csv(self.user_file, index=False, encoding='utf-8-sig')
        return new_id
    
    def update_last_access(self, user_id):
        """마지막 접속 시간 업데이트"""
        df = self.get_users()
        df.loc[df['id'] == user_id, 'last_access'] = datetime.now().strftime('%Y-%m-%d')
        df.to_csv(self.user_file, index=False, encoding='utf-8-sig')
    
    def get_master_tests(self):
        """마스터 테스트 데이터 조회"""
        return pd.read_csv(self.master_file, encoding='utf-8-sig')
    
    def get_user_requests(self, user_id):
        """사용자의 의뢰 목록 조회"""
        df = pd.read_csv(self.request_file, encoding='utf-8-sig')
        return df[df['user_id'] == user_id]
    
    def get_request_data(self, request_id):
        """특정 의뢰 데이터 조회"""
        df = pd.read_csv(self.request_file, encoding='utf-8-sig')
        return df[df['id'] == request_id].iloc[0].to_dict()
    
    def get_test_items(self, request_id):
        """의뢰의 시험 항목 조회"""
        df = pd.read_csv(self.test_item_file, encoding='utf-8-sig')
        return df[df['request_id'] == request_id]
    
    def save_request(self, user_id, request_info, test_items):
        """새 의뢰 저장"""
        # Request Info 저장
        df_request = pd.read_csv(self.request_file, encoding='utf-8-sig')
        new_id = f"R{str(len(df_request) + 1).zfill(5)}"
        
        new_request = pd.DataFrame([{
            'id': new_id,
            'user_id': user_id,
            'extracted_data': json.dumps(test_items),
            'final_data': json.dumps(test_items),
            'is_verified': False,
            'client': request_info.get('client', ''),
            'project': request_info.get('project', '')
        }])
        
        df_request = pd.concat([df_request, new_request], ignore_index=True)
        df_request.to_csv(self.request_file, index=False, encoding='utf-8-sig')
        
        # Test Items 저장
        df_items = pd.read_csv(self.test_item_file, encoding='utf-8-sig')
        
        for item in test_items:
            new_item = {
                'test_name': item.get('test_name', ''),
                'category': item.get('category', ''),
                'ref_standard': item.get('ref_standard', ''),
                'sample_assembly': item.get('sample_assembly', ''),
                'test_sample_no': item.get('test_sample_no', ''),
                'sample_count': item.get('sample_count', ''),
                'test_duration': item.get('test_duration', ''),
                'test_equipment': item.get('test_equipment', ''),
                'test_master_id': item.get('test_master_id', ''),
                'custom_specs': str(item.get('custom_specs', {})),
                'request_id': new_id
            }
            df_items = pd.concat([df_items, pd.DataFrame([new_item])], ignore_index=True)
        
        df_items.to_csv(self.test_item_file, index=False, encoding='utf-8-sig')
        
        return new_id
    
    def update_request(self, request_id, test_items):
        """기존 의뢰 업데이트"""
        # Request Info 업데이트
        df_request = pd.read_csv(self.request_file, encoding='utf-8-sig')
        df_request.loc[df_request['id'] == request_id, 'final_data'] = json.dumps(test_items)
        df_request.to_csv(self.request_file, index=False, encoding='utf-8-sig')
        
        # Test Items 업데이트 (기존 삭제 후 재저장)
        df_items = pd.read_csv(self.test_item_file, encoding='utf-8-sig')
        df_items = df_items[df_items['request_id'] != request_id]
        
        for item in test_items:
            new_item = {
                'test_name': item.get('test_name', ''),
                'category': item.get('category', ''),
                'ref_standard': item.get('ref_standard', ''),
                'sample_assembly': item.get('sample_assembly', ''),
                'test_sample_no': item.get('test_sample_no', ''),
                'sample_count': item.get('sample_count', ''),
                'test_duration': item.get('test_duration', ''),
                'test_equipment': item.get('test_equipment', ''),
                'test_master_id': item.get('test_master_id', ''),
                'custom_specs': str(item.get('custom_specs', {})),
                'request_id': request_id
            }
            df_items = pd.concat([df_items, pd.DataFrame([new_item])], ignore_index=True)
        
        df_items.to_csv(self.test_item_file, index=False, encoding='utf-8-sig')
    
    def get_user_schedule(self, user_id):
        """사용자의 전체 일정 조회"""
        # 실제로는 별도 Schedule 테이블이 필요하지만, 간단히 Request 기반으로 구현
        df_request = pd.read_csv(self.request_file, encoding='utf-8-sig')
        user_requests = df_request[df_request['user_id'] == user_id]
        
        schedule_data = []
        for _, req in user_requests.iterrows():
            df_items = pd.read_csv(self.test_item_file, encoding='utf-8-sig')
            items = df_items[df_items['request_id'] == req['id']]
            
            for _, item in items.iterrows():
                schedule_data.append({
                    '의뢰 ID': req['id'],
                    '프로젝트': req['project'],
                    '시험명': item['test_name'],
                    '시험 기간': item['test_duration']
                })
        
        return pd.DataFrame(schedule_data)
    
    def save_schedule(self, user_id, request_id, schedule_details):
        """일정 저장 (현재는 Request에 포함)"""
        # 실제 구현에서는 별도 Schedule 테이블에 저장
        pass
    
    def export_to_csv(self, data_type):
        """데이터 CSV 내보내기"""
        if data_type == 'master':
            df = pd.read_csv(self.master_file, encoding='utf-8-sig')
        elif data_type == 'request':
            df = pd.read_csv(self.request_file, encoding='utf-8-sig')
        elif data_type == 'test_item':
            df = pd.read_csv(self.test_item_file, encoding='utf-8-sig')
        elif data_type == 'user':
            df = pd.read_csv(self.user_file, encoding='utf-8-sig')
        else:
            return ""
        
        return df.to_csv(index=False, encoding='utf-8-sig')
