import json
import uuid
from datetime import datetime
from pathlib import Path

class Database:
    """간단한 JSON 기반 데이터베이스"""
    
    def __init__(self):
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        
        self.users_file = self.data_dir / "users.json"
        self.requests_file = self.data_dir / "requests.json"
        self.master_file = self.data_dir / "master_data.json"
        self.schedules_file = self.data_dir / "schedules.json"
        
        self._initialize_files()
    
    def _initialize_files(self):
        """데이터 파일 초기화"""
        # 사용자 파일
        if not self.users_file.exists():
            self._save_json(self.users_file, [])
        
        # 의뢰 파일
        if not self.requests_file.exists():
            self._save_json(self.requests_file, [])
        
        # 마스터 데이터 파일
        if not self.master_file.exists():
            default_master = [
                {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "std_name": "Undervoltage and Overvoltage Test",
                    "std_category": "Electrical Tests",
                    "ref_standard": "ISO 16750-3",
                    "aliases": ["과저전압", "정지 전압 확인", "전압 시험"]
                },
                {
                    "id": "550e8400-e29b-41d4-a716-446655440001",
                    "std_name": "On & Off Test",
                    "std_category": "Endurance Test",
                    "ref_standard": "",
                    "aliases": ["작동성 시험", "온오프", "반복 작동"]
                },
                {
                    "id": "550e8400-e29b-41d4-a716-446655440002",
                    "std_name": "High Temperature Test",
                    "std_category": "Operational and Environmental Tests",
                    "ref_standard": "ISO 16750-4",
                    "aliases": ["고온 시험", "내열 시험", "열 시험"]
                },
                {
                    "id": "550e8400-e29b-41d4-a716-446655440003",
                    "std_name": "Low Temperature Test",
                    "std_category": "Operational and Environmental Tests",
                    "ref_standard": "ISO 16750-4",
                    "aliases": ["저온 시험", "내한 시험", "냉각 시험"]
                }
            ]
            self._save_json(self.master_file, default_master)
        
        # 일정 파일
        if not self.schedules_file.exists():
            self._save_json(self.schedules_file, [])
    
    def _load_json(self, file_path):
        """JSON 파일 로드"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    
    def _save_json(self, file_path, data):
        """JSON 파일 저장"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    # 사용자 관련 메서드
    def get_all_users(self):
        """모든 사용자 조회"""
        return self._load_json(self.users_file)
    
    def add_user(self, name, email):
        """사용자 추가"""
        users = self.get_all_users()
        new_user = {
            "id": str(uuid.uuid4()),
            "name": name,
            "email": email,
            "created_at": datetime.now().isoformat()
        }
        users.append(new_user)
        self._save_json(self.users_file, users)
        return new_user
    
    def get_user_by_id(self, user_id):
        """사용자 조회"""
        users = self.get_all_users()
        for user in users:
            if user['id'] == user_id:
                return user
        return None
    
    # 의뢰 관련 메서드
    def get_user_requests(self, user_id):
        """사용자의 의뢰 목록 조회"""
        requests = self._load_json(self.requests_file)
        return [r for r in requests if r['user_id'] == user_id]
    
    def create_request(self, user_id, extracted_data):
        """새 의뢰 생성"""
        requests = self._load_json(self.requests_file)
        new_request = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "client": extracted_data.get('request_info', {}).get('client', ''),
            "project": extracted_data.get('request_info', {}).get('project', ''),
            "extracted_data": json.dumps(extracted_data, ensure_ascii=False),
            "final_data": json.dumps(extracted_data, ensure_ascii=False),
            "is_verified": False,
            "created_at": datetime.now().isoformat()
        }
        requests.append(new_request)
        self._save_json(self.requests_file, requests)
        return new_request['id']
    
    def get_request_by_id(self, request_id):
        """의뢰 조회"""
        requests = self._load_json(self.requests_file)
        for req in requests:
            if req['id'] == request_id:
                return req
        return None
    
    def update_request_data(self, request_id, data):
        """의뢰 데이터 업데이트"""
        requests = self._load_json(self.requests_file)
        for req in requests:
            if req['id'] == request_id:
                req['final_data'] = json.dumps(data, ensure_ascii=False)
                req['client'] = data.get('request_info', {}).get('client', '')
                req['project'] = data.get('request_info', {}).get('project', '')
                break
        self._save_json(self.requests_file, requests)
    
    def mark_request_verified(self, request_id):
        """의뢰 검증 완료 표시"""
        requests = self._load_json(self.requests_file)
        for req in requests:
            if req['id'] == request_id:
                req['is_verified'] = True
                break
        self._save_json(self.requests_file, requests)
    
    # 마스터 데이터 관련 메서드
    def get_master_data(self):
        """마스터 데이터 조회"""
        return self._load_json(self.master_file)
    
    def get_master_by_id(self, master_id):
        """마스터 데이터 ID로 조회"""
        masters = self.get_master_data()
        for master in masters:
            if master['id'] == master_id:
                return master
        return None
    
    def update_master_from_request(self, request_data):
        """의뢰 데이터로부터 마스터 데이터 업데이트 (Learning Loop)"""
        masters = self.get_master_data()
        test_items = request_data.get('test_items', [])
        
        modified = False
        
        for item in test_items:
            master_id = item.get('test_master_id', '')
            test_name = item.get('test_name', '')
            
            if master_id and test_name:
                # 기존 마스터에 유사어 추가
                for master in masters:
                    if master['id'] == master_id:
                        if test_name not in master['aliases'] and test_name != master['std_name']:
                            master['aliases'].append(test_name)
                            modified = True
                        break
            elif test_name and not master_id:
                # 새 마스터 항목 생성
                new_master = {
                    "id": str(uuid.uuid4()),
                    "std_name": test_name,
                    "std_category": item.get('category', ''),
                    "ref_standard": item.get('ref_standard', ''),
                    "aliases": []
                }
                masters.append(new_master)
                modified = True
        
        if modified:
            self._save_json(self.master_file, masters)
    
    # 일정 관련 메서드
    def get_user_schedule(self, user_id, year, month):
        """사용자의 월별 일정 조회"""
        schedules = self._load_json(self.schedules_file)
        user_schedules = [s for s in schedules if s['user_id'] == user_id]
        
        # 해당 월의 일정 필터링
        result = []
        for schedule in user_schedules:
            start_date = datetime.fromisoformat(schedule['start_date'])
            if start_date.year == year and start_date.month == month:
                result.append(schedule)
        
        return result
    
    def get_request_schedule(self, request_id):
        """의뢰의 일정 조회"""
        schedules = self._load_json(self.schedules_file)
        return [s for s in schedules if s['request_id'] == request_id]
    
    def save_schedule(self, user_id, request_id, schedule_data):
        """일정 저장"""
        schedules = self._load_json(self.schedules_file)
        
        # 기존 일정 삭제 (같은 의뢰)
        schedules = [s for s in schedules if s['request_id'] != request_id]
        
        # 새 일정 추가
        for item in schedule_data:
            schedules.append({
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "request_id": request_id,
                **item
            })
        
        self._save_json(self.schedules_file, schedules)
