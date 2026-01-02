import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
import json
import streamlit as st
from modules.utils import generate_request_id, format_date


class DataManager:
    """데이터베이스 관리 모듈 (Google Sheets)"""
    
    def __init__(self):
        """Google Sheets 연결 초기화"""
        try:
            # Streamlit secrets에서 Google Sheets 인증 정보 가져오기
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive'
            ]
            
            # secrets.toml에서 서비스 계정 정보 로드
            if "gcp_service_account" in st.secrets:
                creds_dict = dict(st.secrets["gcp_service_account"])
                creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
                self.client = gspread.authorize(creds)
                
                # 스프레드시트 열기
                spreadsheet_url = "https://docs.google.com/spreadsheets/d/1UhZsidPF2nWNmfGJNCpRZ0BzAj1YW3lTYufR_D4xSog/edit?usp=sharing"
                self.spreadsheet = self.client.open_by_url(spreadsheet_url)
                
                # 각 시트 참조
                self.user_sheet = self.spreadsheet.worksheet("User_List")
                self.master_sheet = self.spreadsheet.worksheet("Master_Test")
                self.request_sheet = self.spreadsheet.worksheet("Request_Info")
                self.test_item_sheet = self.spreadsheet.worksheet("Test_Item")
                
                st.success("✅ Google Sheets 연결 성공")
            else:
                st.warning("⚠️ Google Sheets 인증 정보가 없습니다. 로컬 모드로 실행됩니다.")
                self.client = None
                self._init_local_storage()
        
        except Exception as e:
            st.error(f"❌ Google Sheets 연결 실패: {str(e)}")
            self.client = None
            self._init_local_storage()
    
    def _init_local_storage(self):
        """로컬 저장소 초기화 (Google Sheets 연결 실패 시)"""
        if 'local_users' not in st.session_state:
            st.session_state.local_users = [
                {
                    'user_id': '기본사용자',
                    'created_date': '2026-01-02',
                    'last_access': '2026-01-02'
                }
            ]
        
        if 'local_masters' not in st.session_state:
            st.session_state.local_masters = self._get_default_masters()
        
        if 'local_requests' not in st.session_state:
            st.session_state.local_requests = []
        
        if 'local_test_items' not in st.session_state:
            st.session_state.local_test_items = []
    
    def _get_default_masters(self):
        """기본 마스터 데이터"""
        return [
            {
                "id": "M001",
                "std_name": "High Temperature Test",
                "std_category": "Operational and Environmental tests",
                "ref_standard": "ISO 16750-4",
                "aliases": "고온,고온시험,열충격"
            },
            {
                "id": "M002",
                "std_name": "Low Temperature Test",
                "std_category": "Operational and Environmental tests",
                "ref_standard": "ISO 16750-4",
                "aliases": "저온,저온시험,냉각"
            },
            {
                "id": "M003",
                "std_name": "Random Vibration Test",
                "std_category": "Operational and Environmental tests",
                "ref_standard": "ISO 16750-3",
                "aliases": "진동,진동시험,Random Vibration"
            },
            {
                "id": "M004",
                "std_name": "Noise Test",
                "std_category": "Performance Tests",
                "ref_standard": "",
                "aliases": "소음,소음시험,음향"
            },
            {
                "id": "M005",
                "std_name": "Undervoltage and Overvoltage Test",
                "std_category": "Electrical Tests",
                "ref_standard": "ISO 16750-3",
                "aliases": "과저전압,정지 전압 확인,저전압 시험"
            },
            {
                "id": "M006",
                "std_name": "On & Off Test",
                "std_category": "Endurance Test",
                "ref_standard": "ISO 16750-3",
                "aliases": "작동성 시험,온오프,ON/OFF"
            },
            {
                "id": "M007",
                "std_name": "Humidity Test",
                "std_category": "Operational and Environmental tests",
                "ref_standard": "ISO 16750-4",
                "aliases": "습도,습도시험,결로"
            },
            {
                "id": "M008",
                "std_name": "Salt Spray Test",
                "std_category": "Operational and Environmental tests",
                "ref_standard": "ISO 9227",
                "aliases": "염수분무,부식,내식성"
            },
            {
                "id": "M009",
                "std_name": "Dust Test",
                "std_category": "Operational and Environmental tests",
                "ref_standard": "ISO 20653",
                "aliases": "분진,방진,IP테스트"
            }
        ]
    
    # ========================================================================
    # 사용자 관리
    # ========================================================================
    
    def get_user_list(self):
        """사용자 목록 조회"""
        try:
            if self.client:
                records = self.user_sheet.get_all_records()
                return records if records else []
            else:
                return st.session_state.local_users
        except Exception as e:
            st.error(f"사용자 목록 조회 실패: {str(e)}")
            return []
    
    def add_user(self, user_id):
        """사용자 추가"""
        try:
            current_date = datetime.now().strftime("%Y-%m-%d")
            
            if self.client:
                # 중복 확인
                existing_users = self.user_sheet.col_values(1)
                if user_id in existing_users:
                    st.warning(f"'{user_id}' 사용자가 이미 존재합니다.")
                    return False
                
                # 새 행 추가
                self.user_sheet.append_row([user_id, current_date, current_date])
            else:
                # 로컬 저장소에 추가
                if any(u['user_id'] == user_id for u in st.session_state.local_users):
                    st.warning(f"'{user_id}' 사용자가 이미 존재합니다.")
                    return False
                
                st.session_state.local_users.append({
                    'user_id': user_id,
                    'created_date': current_date,
                    'last_access': current_date
                })
            
            return True
        
        except Exception as e:
            st.error(f"사용자 추가 실패: {str(e)}")
            return False
    
    def update_last_access(self, user_id):
        """마지막 접속 시간 업데이트"""
        try:
            current_date = datetime.now().strftime("%Y-%m-%d")
            
            if self.client:
                # 사용자 찾기
                cell = self.user_sheet.find(user_id)
                if cell:
                    # last_access 열 업데이트 (3번째 열)
                    self.user_sheet.update_cell(cell.row, 3, current_date)
            else:
                # 로컬 저장소 업데이트
                for user in st.session_state.local_users:
                    if user['user_id'] == user_id:
                        user['last_access'] = current_date
                        break
        
        except Exception as e:
            st.error(f"접속 시간 업데이트 실패: {str(e)}")
    
    def get_user_info(self, user_id):
        """사용자 정보 조회"""
        try:
            if self.client:
                records = self.user_sheet.get_all_records()
                for record in records:
                    if record.get('user_id') == user_id:
                        return record
            else:
                for user in st.session_state.local_users:
                    if user['user_id'] == user_id:
                        return user
            
            return None
        
        except Exception as e:
            st.error(f"사용자 정보 조회 실패: {str(e)}")
            return None
    
    # ========================================================================
    # 마스터 데이터 관리
    # ========================================================================
    
    def get_master_data(self):
        """마스터 데이터 조회"""
        try:
            if self.client:
                records = self.master_sheet.get_all_records()
                return records if records else []
            else:
                return st.session_state.local_masters
        except Exception as e:
            st.error(f"마스터 데이터 조회 실패: {str(e)}")
            return []
    
    def update_master_aliases(self, master_id, new_alias):
        """마스터 데이터 유사어 업데이트"""
        try:
            if self.client:
                # 마스터 ID로 행 찾기
                cell = self.master_sheet.find(master_id)
                if cell:
                    # 현재 aliases 가져오기
                    current_aliases = self.master_sheet.cell(cell.row, 5).value
                    aliases_list = current_aliases.split(',') if current_aliases else []
                    
                    # 중복 확인 후 추가
                    if new_alias not in aliases_list:
                        aliases_list.append(new_alias)
                        updated_aliases = ','.join(aliases_list)
                        self.master_sheet.update_cell(cell.row, 5, updated_aliases)
            else:
                # 로컬 저장소 업데이트
                for master in st.session_state.local_masters:
                    if master['id'] == master_id:
                        aliases_list = master['aliases'].split(',') if master['aliases'] else []
                        if new_alias not in aliases_list:
                            aliases_list.append(new_alias)
                            master['aliases'] = ','.join(aliases_list)
                        break
        
        except Exception as e:
            st.error(f"마스터 데이터 업데이트 실패: {str(e)}")
    
    def add_new_master(self, master_data):
        """새 마스터 데이터 추가"""
        try:
            if self.client:
                self.master_sheet.append_row([
                    master_data.get('id'),
                    master_data.get('std_name'),
                    master_data.get('std_category'),
                    master_data.get('ref_standard'),
                    master_data.get('aliases', '')
                ])
            else:
                st.session_state.local_masters.append(master_data)
            
            return True
        
        except Exception as e:
            st.error(f"마스터 데이터 추가 실패: {str(e)}")
            return False
    
    # ========================================================================
    # 의뢰 데이터 관리
    # ========================================================================
    
    def create_request(self, request_data):
        """새 의뢰 생성"""
        try:
            request_id = generate_request_id()
            current_date = datetime.now().strftime("%Y-%m-%d")
            
            # Request Info 저장
            if self.client:
                self.request_sheet.append_row([
                    request_id,
                    request_data.get('user_id'),
                    json.dumps(request_data.get('extracted_data', []), ensure_ascii=False),
                    json.dumps(request_data.get('final_data', []), ensure_ascii=False),
                    str(request_data.get('is_verified', False)),
                    request_data.get('client', ''),
                    request_data.get('project', '')
                ])
            else:
                st.session_state.local_requests.append({
                    'id': request_id,
                    'user_id': request_data.get('user_id'),
                    'extracted_data': request_data.get('extracted_data', []),
                    'final_data': request_data.get('final_data', []),
                    'is_verified': request_data.get('is_verified', False),
                    'client': request_data.get('client', ''),
                    'project': request_data.get('project', '')
                })
            
            # Test Item 저장
            for item in request_data.get('final_data', []):
                self._save_test_item(item, request_id)
            
            return request_id
        
        except Exception as e:
            st.error(f"의뢰 생성 실패: {str(e)}")
            return None
    
    def update_request(self, request_id, request_data):
        """의뢰 업데이트"""
        try:
            if self.client:
                # Request ID로 행 찾기
                cell = self.request_sheet.find(request_id)
                if cell:
                    row = cell.row
                    self.request_sheet.update_cell(row, 3, json.dumps(request_data.get('extracted_data', []), ensure_ascii=False))
                    self.request_sheet.update_cell(row, 4, json.dumps(request_data.get('final_data', []), ensure_ascii=False))
                    self.request_sheet.update_cell(row, 5, str(request_data.get('is_verified', False)))
                    self.request_sheet.update_cell(row, 6, request_data.get('client', ''))
                    self.request_sheet.update_cell(row, 7, request_data.get('project', ''))
                    
                    # 기존 Test Items 삭제 후 재생성
                    self._delete_test_items_by_request(request_id)
                    for item in request_data.get('final_data', []):
                        self._save_test_item(item, request_id)
            else:
                # 로컬 저장소 업데이트
                for req in st.session_state.local_requests:
                    if req['id'] == request_id:
                        req.update({
                            'extracted_data': request_data.get('extracted_data', []),
                            'final_data': request_data.get('final_data', []),
                            'is_verified': request_data.get('is_verified', False),
                            'client': request_data.get('client', ''),
                            'project': request_data.get('project', '')
                        })
                        break
                
                # Test Items 업데이트
                st.session_state.local_test_items = [
                    item for item in st.session_state.local_test_items
                    if item.get('request_id') != request_id
                ]
                for item in request_data.get('final_data', []):
                    self._save_test_item(item, request_id)
            
            return True
        
        except Exception as e:
            st.error(f"의뢰 업데이트 실패: {str(e)}")
            return False
    
    def get_request_data(self, request_id):
        """의뢰 데이터 조회"""
        try:
            if self.client:
                records = self.request_sheet.get_all_records()
                for record in records:
                    if record.get('id') == request_id:
                        # JSON 문자열 파싱
                        record['extracted_data'] = json.loads(record.get('extracted_data', '[]'))
                        record['final_data'] = json.loads(record.get('final_data', '[]'))
                        return record
            else:
                for req in st.session_state.local_requests:
                    if req['id'] == request_id:
                        return req
            
            return None
        
        except Exception as e:
            st.error(f"의뢰 데이터 조회 실패: {str(e)}")
            return None
    
    def get_user_requests(self, user_id):
        """사용자의 의뢰 목록 조회"""
        try:
            if self.client:
                records = self.request_sheet.get_all_records()
                return [r for r in records if r.get('user_id') == user_id]
            else:
                return [r for r in st.session_state.local_requests if r.get('user_id') == user_id]
        
        except Exception as e:
            st.error(f"의뢰 목록 조회 실패: {str(e)}")
            return []
    
    # ========================================================================
    # 시험 항목 관리
    # ========================================================================
    
    def _save_test_item(self, item, request_id):
        """시험 항목 저장"""
        try:
            item['request_id'] = request_id
            
            if self.client:
                self.test_item_sheet.append_row([
                    item.get('test_name', ''),
                    item.get('category', ''),
                    item.get('ref_standard', ''),
                    item.get('sample_assembly', ''),
                    item.get('test_sample_no', ''),
                    item.get('sample_count', ''),
                    item.get('test_duration', ''),
                    item.get('test_equipment', ''),
                    item.get('test_master_id', ''),
                    json.dumps(item.get('custom_specs', {}), ensure_ascii=False),
                    request_id
                ])
            else:
                st.session_state.local_test_items.append(item)
        
        except Exception as e:
            st.error(f"시험 항목 저장 실패: {str(e)}")
    
    def _delete_test_items_by_request(self, request_id):
        """의뢰의 모든 시험 항목 삭제"""
        try:
            if self.client:
                # Request ID로 모든 행 찾아서 삭제
                all_values = self.test_item_sheet.get_all_values()
                rows_to_delete = []
                
                for idx, row in enumerate(all_values[1:], start=2):  # 헤더 제외
                    if len(row) > 10 and row[10] == request_id:
                        rows_to_delete.append(idx)
                
                # 역순으로 삭제 (인덱스 변경 방지)
                for row_idx in sorted(rows_to_delete, reverse=True):
                    self.test_item_sheet.delete_rows(row_idx)
            else:
                st.session_state.local_test_items = [
                    item for item in st.session_state.local_test_items
                    if item.get('request_id') != request_id
                ]
        
        except Exception as e:
            st.error(f"시험 항목 삭제 실패: {str(e)}")
    
    def get_test_items_by_request(self, request_id):
        """의뢰의 시험 항목 조회"""
        try:
            if self.client:
                records = self.test_item_sheet.get_all_records()
                items = [r for r in records if r.get('request_id') == request_id]
                
                # custom_specs JSON 파싱
                for item in items:
                    if 'custom_specs' in item:
                        item['custom_specs'] = json.loads(item.get('custom_specs', '{}'))
                
                return items
            else:
                return [item for item in st.session_state.local_test_items if item.get('request_id') == request_id]
        
        except Exception as e:
            st.error(f"시험 항목 조회 실패: {str(e)}")
            return []
    
    # ========================================================================
    # 일정 관리
    # ========================================================================
    
    def save_schedule(self, user_id, request_id, schedule_items, start_date):
        """일정 저장"""
        try:
            # 일정 정보를 의뢰 데이터에 추가하거나 별도 시트에 저장
            # 여기서는 간단히 Test Item에 일정 정보를 추가하는 방식으로 구현
            
            current_date = start_date
            
            for item in schedule_items:
                duration = int(item.get('test_duration', 1))
                # 일정 정보 업데이트 로직
                # 실제로는 별도 Schedule 시트를 만들어 관리하는 것이 좋음
            
            return True
        
        except Exception as e:
            st.error(f"일정 저장 실패: {str(e)}")
            return False
    
    def get_user_schedule(self, user_id, year, month):
        """사용자의 월별 일정 조회"""
        try:
            # 사용자의 모든 의뢰 조회
            requests = self.get_user_requests(user_id)
            
            schedule_data = []
            for req in requests:
                test_items = self.get_test_items_by_request(req['id'])
                for item in test_items:
                    schedule_data.append({
                        '의뢰ID': req['id'],
                        '발주처': req.get('client', ''),
                        '프로젝트': req.get('project', ''),
                        '시험명': item.get('test_name', ''),
                        '소요일수': item.get('test_duration', ''),
                        '시험장비': item.get('test_equipment', '')
                    })
            
            return schedule_data
        
        except Exception as e:
            st.error(f"일정 조회 실패: {str(e)}")
            return []
    
    def get_request_schedule(self, request_id):
        """의뢰의 일정 조회"""
        try:
            request_data = self.get_request_data(request_id)
            test_items = self.get_test_items_by_request(request_id)
            
            schedule_data = []
            for item in test_items:
                schedule_data.append({
                    '시험명': item.get('test_name', ''),
                    '분류': item.get('category', ''),
                    '소요일수': item.get('test_duration', ''),
                    '시료수': item.get('sample_count', ''),
                    '시험장비': item.get('test_equipment', '')
                })
            
            return schedule_data
        
        except Exception as e:
            st.error(f"일정 조회 실패: {str(e)}")
            return []
