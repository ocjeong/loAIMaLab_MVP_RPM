import json
from datetime import datetime
from typing import List, Dict, Any
import os

class Database:
    """간단한 JSON 기반 데이터베이스 (실제 배포 시 SQLite나 PostgreSQL 권장)"""
    
    def __init__(self):
        self.data_dir = "data"
        self.users_file = os.path.join(self.data_dir, "users.json")
        self.requests_file = os.path.join(self.data_dir, "requests.json")
        self.master_file = os.path.join(self.data_dir, "master_data.json")
        self.schedule_file = os.path.join(self.data_dir, "schedules.json")
        
        # 데이터 디렉토리 생성
        os.makedirs(self.data_dir, exist_ok=True)
        
        # 초기 데이터 로드
        self.users = self._load_json(self.users_file, [])
        self.requests = self._load_json(self.requests_file, {})
        self.master_data = self._load_json(self.master_file, self._init_master_data())
        self.schedules = self._load_json(self.schedule_file, {})
    
    def _load_json(self, filepath: str, default: Any) -> Any:
        """JSON 파일 로드"""
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        return default
    
    def _save_json(self, filepath: str, data: Any):
        """JSON 파일 저장"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _init_master_data(self) -> List[Dict]:
        """마스터 데이터 초기화"""
        return [
            {
                "id": "M001",
                "standard_name": "On & Off Test",
                "category": "Endurance Test",
                "aliases": ["작동성 시험", "온오프", "ON/OFF 시험"],
                "default_rule": "1min ON / 1min OFF"
            },
            {
                "id": "M002",
                "standard_name": "Undervoltage Test",
                "category": "Electrical Test",
                "aliases": ["저전압 시험", "Low Voltage Test"],
                "default_rule": "9V DC"
            },
            {
                "id": "M003",
                "standard_name": "Overvoltage Test",
                "category": "Electrical Test",
                "aliases": ["과전압 시험", "High Voltage Test"],
                "default_rule": "16V DC"
            },
            {
                "id": "M004",
                "standard_name": "Temperature Cycle Test",
                "category": "Environmental Test",
                "aliases": ["온도 사이클", "열충격 시험"],
                "default_rule": "-40°C to +85°C"
            }
        ]
    
    def get_all_users(self) -> List[str]:
        """모든 사용자 목록 반환"""
        if not self.users:
            self.users = ["사용자1", "사용자2", "사용자3"]
            self._save_json(self.users_file, self.users)
        return self.users
    
    def add_user(self, username: str):
        """새 사용자 추가"""
        if username not in self.users:
            self.users.append(username)
            self._save_json(self.users_file, self.users)
    
    def get_user_requests(self, username: str) -> List[Dict]:
        """특정 사용자의 의뢰 목록 반환"""
        user_requests = [
            {"request_id": req_id, "created_at": data["created_at"]}
            for req_id, data in self.requests.items()
            if data.get("user") == username
        ]
        return sorted(user_requests, key=lambda x: x["created_at"], reverse=True)
    
    def create_new_request(self, username: str, filename: str) -> str:
        """새 의뢰 생성"""
        request_id = f"REQ_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.requests[request_id] = {
            "user": username,
            "filename": filename,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "data": []
        }
        self._save_json(self.requests_file, self.requests)
        return request_id
    
    def save_request_data(self, request_id: str, data: List[Dict]):
        """의뢰 데이터 저장"""
        if request_id in self.requests:
            self.requests[request_id]["data"] = data
            self.requests[request_id]["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self._save_json(self.requests_file, self.requests)
    
    def get_request_data(self, request_id: str) -> List[Dict]:
        """의뢰 데이터 조회"""
        return self.requests.get(request_id, {}).get("data", [])
    
    def get_user_schedule(self, username: str, month: str = None) -> List[Dict]:
        """사용자의 전체 또는 월별 일정 조회"""
        user_schedules = []
        for schedule_id, schedule_data in self.schedules.items():
            if schedule_data.get("user") == username:
                if month is None or schedule_data.get("month") == month:
                    user_schedules.extend(schedule_data.get("tasks", []))
        return user_schedules
    
    def get_request_schedule(self, request_id: str) -> List[Dict]:
        """특정 의뢰의 일정 조회"""
        for schedule_data in self.schedules.values():
            if schedule_data.get("request_id") == request_id:
                return schedule_data.get("tasks", [])
        return []
    
    def save_schedule(self, username: str, request_id: str, tasks: List[Dict]):
        """일정 저장"""
        schedule_id = f"SCH_{request_id}"
        self.schedules[schedule_id] = {
            "user": username,
            "request_id": request_id,
            "month": datetime.now().strftime("%Y-%m"),
            "tasks": tasks,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self._save_json(self.schedule_file, self.schedules)
    
    def get_master_data(self) -> List[Dict]:
        """마스터 데이터 조회"""
        return self.master_data
    
    def update_master_data(self, new_item: Dict):
        """마스터 데이터 업데이트"""
        self.master_data.append(new_item)
        self._save_json(self.master_file, self.master_data)
