import pandas as pd
import os
from datetime import datetime
import json
from typing import List, Dict, Optional

class Database:
    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        self._initialize_csv_files()
    
    def _initialize_csv_files(self):
        """CSV 파일 초기화"""
        # User List
        user_list_path = os.path.join(self.data_dir, "User_List.csv")
        if not os.path.exists(user_list_path):
            df = pd.DataFrame(columns=["id", "user_name", "created_date", "last_access"])
            df.to_csv(user_list_path, index=False, encoding='utf-8-sig')
        
        # Master Test
        master_test_path = os.path.join(self.data_dir, "Master_Test.csv")
        if not os.path.exists(master_test_path):
            initial_masters = [
                {
                    "id": "M001",
                    "std_name": "On & Off Test",
                    "std_category": "Endurance Test",
                    "aliases": '["작동성 시험", "온오프"]',
                    "ref_standard": "ISO 16750-3"
                },
                {
                    "id": "M002",
                    "std_name": "High Temperature Test",
                    "std_category": "Operational and Environmental tests",
                    "aliases": '["고온 시험", "고온 내구"]',
                    "ref_standard": "ISO 16750-4"
                },
                {
                    "id": "M003",
                    "std_name": "Low Temperature Test",
                    "std_category": "Operational and Environmental tests",
                    "aliases": '["저온 시험", "저온 내구"]',
                    "ref_standard": "ISO 16750-4"
                },
                {
                    "id": "M004",
                    "std_name": "Noise Test",
                    "std_category": "Operational and Environmental tests",
                    "aliases": '["소음 시험", "노이즈 테스트"]',
                    "ref_standard": ""
                },
                {
                    "id": "M005",
                    "std_name": "Random Vibration Test",
                    "std_category": "Operational and Environmental tests",
                    "aliases": '["랜덤 진동", "진동 시험"]',
                    "ref_standard": "ISO 16750-3"
                },
                {
                    "id": "M006",
                    "std_name": "Functional Test",
                    "std_category": "Operational and Environmental tests",
                    "aliases": '["기능 시험", "작동 확인"]',
                    "ref_standard": ""
                },
                {
                    "id": "M007",
                    "std_name": "Voltage Drop Test",
                    "std_category": "Electrical Tests",
                    "aliases": '["전압 강하", "전압강하 시험"]',
                    "ref_standard": "ISO 16750-3"
                },
                {
                    "id": "M008",
                    "std_name": "Short Circuit Test",
                    "std_category": "Electrical Tests",
                    "aliases": '["단락 시험", "쇼트 테스트"]',
                    "ref_standard": "ISO 16750-3"
                },
                {
                    "id": "M009",
                    "std_name": "Undervoltage and Overvoltage Test",
                    "std_category": "Electrical Tests",
                    "aliases": '["과저전압", "정지 전압 확인"]',
                    "ref_standard": "ISO 16750-3"
                }
            ]
            df = pd.DataFrame(initial_masters)
            df.to_csv(master_test_path, index=False, encoding='utf-8-sig')
        
        # Request Info
        request_info_path = os.path.join(self.data_dir, "Request_Info.csv")
        if not os.path.exists(request_info_path):
            df = pd.DataFrame(columns=["id", "user_id", "extracted_data", "final_data", 
                                      "is_verified", "client", "project"])
            df.to_csv(request_info_path, index=False, encoding='utf-8-sig')
        
        # Test Item
        test_item_path = os.path.join(self.data_dir, "Test_Item.csv")
        if not os.path.exists(test_item_path):
            df = pd.DataFrame(columns=["id", "test_name", "test_name_original", "category", 
                                      "category_original", "ref_standard", "sample_assembly",
                                      "test_sample_no", "sample_count", "test_duration",
                                      "test_equipment", "test_master_id", "custom_specs", 
                                      "request_id"])
            df.to_csv(test_item_path, index=False, encoding='utf-8-sig')
        
        # Schedule Item
        schedule_item_path = os.path.join(self.data_dir, "Schedule_Item.csv")
        if not os.path.exists(schedule_item_path):
            df = pd.DataFrame(columns=["test_item_id", "start_date", "end_date", 
                                      "start_day", "end_day", "duration", "status"])
            df.to_csv(schedule_item_path, index=False, encoding='utf-8-sig')
    
    # User List 관련
    def get_all_users(self) -> pd.DataFrame:
        """모든 사용자 조회"""
        path = os.path.join(self.data_dir, "User_List.csv")
        return pd.read_csv(path, encoding='utf-8-sig')
    
    def add_user(self, user_name: str) -> str:
        """사용자 추가"""
        df = self.get_all_users()
        new_id = f"U{str(len(df) + 1).zfill(3)}"
        new_user = pd.DataFrame([{
            "id": new_id,
            "user_name": user_name,
            "created_date": datetime.now().strftime("%Y-%m-%d"),
            "last_access": datetime.now().strftime("%Y-%m-%d")
        }])
        df = pd.concat([df, new_user], ignore_index=True)
        path = os.path.join(self.data_dir, "User_List.csv")
        df.to_csv(path, index=False, encoding='utf-8-sig')
        return new_id
    
    def update_user_access(self, user_id: str):
        """사용자 마지막 접속 시간 업데이트"""
        df = self.get_all_users()
        df.loc[df['id'] == user_id, 'last_access'] = datetime.now().strftime("%Y-%m-%d")
        path = os.path.join(self.data_dir, "User_List.csv")
        df.to_csv(path, index=False, encoding='utf-8-sig')
    
    # Master Test 관련
    def get_all_masters(self) -> pd.DataFrame:
        """모든 마스터 데이터 조회"""
        path = os.path.join(self.data_dir, "Master_Test.csv")
        return pd.read_csv(path, encoding='utf-8-sig')
    
    def get_master_by_id(self, master_id: str) -> Optional[Dict]:
        """마스터 ID로 조회"""
        df = self.get_all_masters()
        result = df[df['id'] == master_id]
        if len(result) == 0:
            return None
        master = result.iloc[0].to_dict()
        if pd.notna(master.get('aliases')):
            try:
                master['aliases'] = json.loads(master['aliases'])
            except:
                master['aliases'] = []
        else:
            master['aliases'] = []
        return master
    
    def update_master_aliases(self, master_id: str, new_alias: str):
        """마스터 데이터의 유사어 업데이트"""
        df = self.get_all_masters()
        idx = df[df['id'] == master_id].index
        if len(idx) > 0:
            aliases = json.loads(df.loc[idx[0], 'aliases']) if pd.notna(df.loc[idx[0], 'aliases']) else []
            if new_alias not in aliases:
                aliases.append(new_alias)
                df.loc[idx[0], 'aliases'] = json.dumps(aliases, ensure_ascii=False)
                path = os.path.join(self.data_dir, "Master_Test.csv")
                df.to_csv(path, index=False, encoding='utf-8-sig')
    
    def add_master(self, test_item: Dict) -> str:
        """새로운 마스터 데이터 추가"""
        df = self.get_all_masters()
        new_id = f"M{str(len(df) + 1).zfill(3)}"
        new_master = pd.DataFrame([{
            "id": new_id,
            "std_name": test_item.get('test_name', ''),
            "std_category": test_item.get('category', ''),
            "aliases": json.dumps([test_item.get('test_name_original', '')], ensure_ascii=False),
            "ref_standard": test_item.get('ref_standard', '')
        }])
        df = pd.concat([df, new_master], ignore_index=True)
        path = os.path.join(self.data_dir, "Master_Test.csv")
        df.to_csv(path, index=False, encoding='utf-8-sig')
        return new_id
    
    # Request Info 관련
    def get_all_requests(self, user_id: Optional[str] = None) -> pd.DataFrame:
        """의뢰 정보 조회"""
        path = os.path.join(self.data_dir, "Request_Info.csv")
        df = pd.read_csv(path, encoding='utf-8-sig')
        if user_id:
            df = df[df['user_id'] == user_id]
        return df
    
    def add_request(self, user_id: str, extracted_data: List[Dict], 
                   client: str, project: str) -> str:
        """새 의뢰 추가"""
        df = self.get_all_requests()
        new_id = f"R{str(len(df) + 1).zfill(5)}"
        new_request = pd.DataFrame([{
            "id": new_id,
            "user_id": user_id,
            "extracted_data": json.dumps(extracted_data, ensure_ascii=False),
            "final_data": json.dumps(extracted_data, ensure_ascii=False),
            "is_verified": False,
            "client": client,
            "project": project
        }])
        df = pd.concat([df, new_request], ignore_index=True)
        path = os.path.join(self.data_dir, "Request_Info.csv")
        df.to_csv(path, index=False, encoding='utf-8-sig')
        return new_id
    
    def update_request(self, request_id: str, final_data: List[Dict]):
        """의뢰 데이터 업데이트"""
        df = self.get_all_requests()
        idx = df[df['id'] == request_id].index
        if len(idx) > 0:
            df.loc[idx[0], 'final_data'] = json.dumps(final_data, ensure_ascii=False)
            df.loc[idx[0], 'is_verified'] = True
            path = os.path.join(self.data_dir, "Request_Info.csv")
            df.to_csv(path, index=False, encoding='utf-8-sig')
    
    def get_request_by_id(self, request_id: str) -> Optional[Dict]:
        """의뢰 ID로 조회"""
        df = self.get_all_requests()
        result = df[df['id'] == request_id]
        if len(result) == 0:
            return None
        request = result.iloc[0].to_dict()
        if pd.notna(request.get('extracted_data')):
            request['extracted_data'] = json.loads(request['extracted_data'])
        if pd.notna(request.get('final_data')):
            request['final_data'] = json.loads(request['final_data'])
        return request
    
    # Test Item 관련
    def get_test_items(self, request_id: Optional[str] = None) -> pd.DataFrame:
        """시험 항목 조회"""
        path = os.path.join(self.data_dir, "Test_Item.csv")
        df = pd.read_csv(path, encoding='utf-8-sig')
        if request_id:
            df = df[df['request_id'] == request_id]
        return df
    
    def add_test_items(self, test_items: List[Dict], request_id: str):
        """시험 항목 추가"""
        df = self.get_test_items()
        start_id = len(df) + 1
        
        new_items = []
        for idx, item in enumerate(test_items):
            item['id'] = f"TI{str(start_id + idx).zfill(5)}"
            item['request_id'] = request_id
            if 'custom_specs' in item and isinstance(item['custom_specs'], dict):
                item['custom_specs'] = json.dumps(item['custom_specs'], ensure_ascii=False)
            new_items.append(item)
        
        new_df = pd.DataFrame(new_items)
        df = pd.concat([df, new_df], ignore_index=True)
        path = os.path.join(self.data_dir, "Test_Item.csv")
        df.to_csv(path, index=False, encoding='utf-8-sig')
    
    # Schedule Item 관련
    def get_schedule_items(self, user_id: Optional[str] = None, 
                          month: Optional[str] = None) -> pd.DataFrame:
        """일정 조회"""
        path = os.path.join(self.data_dir, "Schedule_Item.csv")
        df = pd.read_csv(path, encoding='utf-8-sig')
        
        if user_id or month:
            # Test Item과 조인하여 user_id 필터링
            test_items = self.get_test_items()
            requests = self.get_all_requests()
            
            # request_id로 user_id 매핑
            df = df.merge(test_items[['id', 'request_id']], 
                         left_on='test_item_id', right_on='id', how='left')
            df = df.merge(requests[['id', 'user_id']], 
                         left_on='request_id', right_on='id', how='left', suffixes=('', '_req'))
            
            if user_id:
                df = df[df['user_id'] == user_id]
            
            if month:
                df['start_date'] = pd.to_datetime(df['start_date'])
                df = df[df['start_date'].dt.strftime('%Y-%m') == month]
        
        return df
    
    def add_schedule_items(self, schedule_items: List[Dict]):
        """일정 추가"""
        df = self.get_schedule_items()
        new_df = pd.DataFrame(schedule_items)
        df = pd.concat([df, new_df], ignore_index=True)
        path = os.path.join(self.data_dir, "Schedule_Item.csv")
        df.to_csv(path, index=False, encoding='utf-8-sig')
    
    def get_last_schedule_date(self, user_id: str) -> Optional[datetime]:
        """사용자의 마지막 일정 종료일 조회"""
        schedules = self.get_schedule_items(user_id=user_id)
        if len(schedules) == 0:
            return None
        schedules['end_date'] = pd.to_datetime(schedules['end_date'])
        return schedules['end_date'].max()
    
    # Export 기능
    def export_to_csv(self, table_name: str) -> str:
        """테이블을 CSV로 내보내기"""
        path = os.path.join(self.data_dir, f"{table_name}.csv")
        return path
