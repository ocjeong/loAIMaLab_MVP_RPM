import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import streamlit as st

DB_PATH = "rpm_data.db"

def get_connection():
    """데이터베이스 연결"""
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_database():
    """데이터베이스 초기화"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # master_test_data 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS master_test_data (
            id TEXT PRIMARY KEY,
            std_name TEXT NOT NULL,
            std_category TEXT,
            aliases TEXT,
            ref_standard TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # users 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            department TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # request_info_data 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS request_info_data (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            client TEXT,
            project TEXT,
            extracted_data TEXT,
            final_data TEXT,
            is_verified INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # test_item_data 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS test_item_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id TEXT NOT NULL,
            test_name TEXT,
            category TEXT,
            ref_standard TEXT,
            sample_assembly TEXT,
            test_sample_no INTEGER,
            sample_count INTEGER,
            test_duration REAL,
            test_equipment TEXT,
            test_master_id TEXT,
            custom_specs TEXT,
            priority_order INTEGER,
            start_date DATE,
            end_date DATE,
            is_included INTEGER DEFAULT 1,
            FOREIGN KEY (request_id) REFERENCES request_info_data(id),
            FOREIGN KEY (test_master_id) REFERENCES master_test_data(id)
        )
    ''')
    
    conn.commit()
    
    # 초기 마스터 데이터 삽입
    cursor.execute("SELECT COUNT(*) FROM master_test_data")
    if cursor.fetchone()[0] == 0:
        initial_masters = [
            ("M001", "Undervoltage Test", "Electrical", '["저전압 시험", "언더볼티지"]', "KS R 1234"),
            ("M002", "Overvoltage Test", "Electrical", '["과전압 시험", "오버볼티지"]', "KS R 1234"),
            ("M003", "High Temperature Test", "Environmental", '["고온 시험", "고온 내구"]', "KS R 5678"),
            ("M004", "Low Temperature Test", "Environmental", '["저온 시험", "저온 내구"]', "KS R 5678"),
            ("M005", "Endurance Test", "Endurance", '["내구 시험", "수명 시험"]', "KS R 9012"),
        ]
        
        for master in initial_masters:
            cursor.execute('''
                INSERT INTO master_test_data (id, std_name, std_category, aliases, ref_standard)
                VALUES (?, ?, ?, ?, ?)
            ''', master)
        
        conn.commit()
    
    # 초기 사용자 데이터 삽입
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        initial_users = [
            ("U001", "홍길동", "시험팀"),
            ("U002", "김철수", "품질팀"),
        ]
        
        for user in initial_users:
            cursor.execute('''
                INSERT INTO users (id, name, department)
                VALUES (?, ?, ?)
            ''', user)
        
        conn.commit()
    
    conn.close()

# ===== 사용자 관련 함수 =====

def get_users() -> List[Tuple]:
    """모든 사용자 조회"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, department FROM users ORDER BY name")
    users = cursor.fetchall()
    conn.close()
    return users

def create_user(user_id: str, name: str, department: str):
    """새 사용자 생성"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO users (id, name, department)
        VALUES (?, ?, ?)
    ''', (user_id, name, department))
    conn.commit()
    conn.close()

# ===== 의뢰 관련 함수 =====

def get_user_requests(user_id: str) -> List[Tuple]:
    """사용자의 의뢰 목록 조회"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, user_id, client, project, created_at, is_verified
        FROM request_info_data
        WHERE user_id = ?
        ORDER BY created_at DESC
    ''', (user_id,))
    requests = cursor.fetchall()
    conn.close()
    return requests

def create_request(user_id: str, client: str, project: str, extracted_data: Dict) -> str:
    """새 의뢰 생성"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # 의뢰 ID 생성 (REQ + 타임스탬프)
    request_id = f"REQ{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    cursor.execute('''
        INSERT INTO request_info_data (id, user_id, client, project, extracted_data, final_data)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (request_id, user_id, client, project, 
          json.dumps(extracted_data, ensure_ascii=False),
          json.dumps(extracted_data, ensure_ascii=False)))
    
    conn.commit()
    conn.close()
    
    return request_id

def get_request_data(request_id: str) -> Optional[Dict]:
    """의뢰 데이터 조회"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, user_id, client, project, extracted_data, final_data, is_verified
        FROM request_info_data
        WHERE id = ?
    ''', (request_id,))
    
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return {
            'id': result[0],
            'user_id': result[1],
            'client': result[2],
            'project': result[3],
            'extracted_data': json.loads(result[4]) if result[4] else {},
            'final_data': json.loads(result[5]) if result[5] else {},
            'is_verified': bool(result[6])
        }
    return None

def update_request_data(request_id: str, final_data: Dict):
    """의뢰 데이터 업데이트"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE request_info_data
        SET final_data = ?, modified_at = ?, is_verified = 1
        WHERE id = ?
    ''', (json.dumps(final_data, ensure_ascii=False), datetime.now(), request_id))
    conn.commit()
    conn.close()

# ===== 시험 항목 관련 함수 =====

def save_test_items(request_id: str, test_items: List[Dict]):
    """시험 항목 저장"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # 기존 항목 삭제
    cursor.execute("DELETE FROM test_item_data WHERE request_id = ?", (request_id,))
    
    # 새 항목 삽입
    for idx, item in enumerate(test_items):
        cursor.execute('''
            INSERT INTO test_item_data (
                request_id, test_name, category, ref_standard, sample_assembly,
                test_sample_no, sample_count, test_duration, test_equipment,
                test_master_id, custom_specs, priority_order, is_included
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            request_id,
            item.get('test_name', ''),
            item.get('category', ''),
            item.get('ref_standard', ''),
            item.get('sample_assembly', ''),
            item.get('test_sample_no', 0),
            item.get('sample_count', 0),
            item.get('test_duration', 1.0),
            item.get('test_equipment', ''),
            item.get('test_master_id', ''),
            json.dumps(item.get('custom_specs', {}), ensure_ascii=False),
            idx + 1,
            1
        ))
    
    conn.commit()
    conn.close()

def get_test_items(request_id: str) -> List[Dict]:
    """시험 항목 조회"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, test_name, category, ref_standard, sample_assembly,
               test_sample_no, sample_count, test_duration, test_equipment,
               test_master_id, custom_specs, priority_order, start_date, end_date, is_included
        FROM test_item_data
        WHERE request_id = ?
        ORDER BY priority_order
    ''', (request_id,))
    
    rows = cursor.fetchall()
    conn.close()
    
    items = []
    for row in rows:
        items.append({
            'id': row[0],
            'test_name': row[1],
            'category': row[2],
            'ref_standard': row[3],
            'sample_assembly': row[4],
            'test_sample_no': row[5],
            'sample_count': row[6],
            'test_duration': row[7],
            'test_equipment': row[8],
            'test_master_id': row[9],
            'custom_specs': json.loads(row[10]) if row[10] else {},
            'priority_order': row[11],
            'start_date': row[12],
            'end_date': row[13],
            'is_included': bool(row[14])
        })
    
    return items

def update_test_schedule(request_id: str, schedule_data: List[Dict]):
    """시험 일정 업데이트"""
    conn = get_connection()
    cursor = conn.cursor()
    
    for item in schedule_data:
        cursor.execute('''
            UPDATE test_item_data
            SET start_date = ?, end_date = ?, priority_order = ?, is_included = ?
            WHERE id = ?
        ''', (
            item.get('start_date'),
            item.get('end_date'),
            item.get('priority_order'),
            1 if item.get('is_included', True) else 0,
            item.get('id')
        ))
    
    conn.commit()
    conn.close()

# ===== 마스터 데이터 관련 함수 =====

def get_master_data() -> List[Dict]:
    """마스터 시험 데이터 조회"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, std_name, std_category, aliases, ref_standard
        FROM master_test_data
        ORDER BY std_category, std_name
    ''')
    
    rows = cursor.fetchall()
    conn.close()
    
    masters = []
    for row in rows:
        masters.append({
            'id': row[0],
            'std_name': row[1],
            'std_category': row[2],
            'aliases': json.loads(row[3]) if row[3] else [],
            'ref_standard': row[4]
        })
    
    return masters

def update_master_aliases(master_id: str, new_alias: str):
    """마스터 데이터 별칭 업데이트"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT aliases FROM master_test_data WHERE id = ?", (master_id,))
    result = cursor.fetchone()
    
    if result:
        aliases = json.loads(result[0]) if result[0] else []
        if new_alias not in aliases:
            aliases.append(new_alias)
            cursor.execute('''
                UPDATE master_test_data
                SET aliases = ?, updated_at = ?
                WHERE id = ?
            ''', (json.dumps(aliases, ensure_ascii=False), datetime.now(), master_id))
            conn.commit()
    
    conn.close()

def create_master_data(std_name: str, std_category: str, aliases: List[str], ref_standard: str) -> str:
    """새 마스터 데이터 생성"""
    import uuid
    
    conn = get_connection()
    cursor = conn.cursor()
    
    master_id = f"M{str(uuid.uuid4())[:8].upper()}"
    
    cursor.execute('''
        INSERT INTO master_test_data (id, std_name, std_category, aliases, ref_standard)
        VALUES (?, ?, ?, ?, ?)
    ''', (master_id, std_name, std_category, json.dumps(aliases, ensure_ascii=False), ref_standard))
    
    conn.commit()
    conn.close()
    
    return master_id
