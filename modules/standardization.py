from typing import Dict, List, Optional

class Standardization:
    def __init__(self, database):
        self.db = database
    
    def standardize_test_item(self, test_item: Dict) -> Dict:
        """시험 항목 표준화"""
        # 원본 데이터 보존
        if 'test_name_original' not in test_item:
            test_item['test_name_original'] = test_item.get('test_name', '')
        if 'category_original' not in test_item:
            test_item['category_original'] = test_item.get('category', '')
        
        # 마스터 ID가 있으면 표준화 적용
        master_id = test_item.get('test_master_id', '')
        if master_id and master_id != '':
            master = self.db.get_master_by_id(master_id)
            if master:
                test_item['test_name'] = master['std_name']
                test_item['category'] = master['std_category']
                if not test_item.get('ref_standard'):
                    test_item['ref_standard'] = master.get('ref_standard', '')
        
        return test_item
    
    def standardize_test_items(self, test_items: List[Dict]) -> List[Dict]:
        """여러 시험 항목 표준화"""
        return [self.standardize_test_item(item) for item in test_items]
    
    def update_master_from_test_item(self, test_item: Dict):
        """시험 항목에서 마스터 데이터 업데이트"""
        master_id = test_item.get('test_master_id', '')
        original_name = test_item.get('test_name_original', '')
        
        if master_id and master_id != '' and original_name:
            # 마스터 존재 시 유사어 업데이트
            master = self.db.get_master_by_id(master_id)
            if master:
                self.db.update_master_aliases(master_id, original_name)
        elif not master_id or master_id == '':
            # 마스터 없으면 새로 추가
            new_master_id = self.db.add_master(test_item)
            test_item['test_master_id'] = new_master_id
    
    def update_masters_from_test_items(self, test_items: List[Dict]):
        """여러 시험 항목에서 마스터 데이터 업데이트"""
        for item in test_items:
            self.update_master_from_test_item(item)
