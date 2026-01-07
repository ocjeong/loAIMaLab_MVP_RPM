import json
from modules.data_manager import DataManager

class Standardizer:
    def __init__(self):
        self.dm = DataManager()
    
    def standardize_test_item(self, test_item):
        """시험 항목을 마스터 데이터 기준으로 표준화"""
        test_master_id = test_item.get('test_master_id', '')
        
        # 원본 데이터 보존
        if 'test_name_original' not in test_item or not test_item['test_name_original']:
            test_item['test_name_original'] = test_item.get('test_name', '')
        if 'category_original' not in test_item or not test_item['category_original']:
            test_item['category_original'] = test_item.get('category', '')
        
        # 마스터 ID가 있는 경우 표준화 적용
        if test_master_id:
            master = self.dm.get_master_by_id(test_master_id)
            if master:
                # 표준명 적용
                test_item['test_name'] = master['std_name']
                test_item['category'] = master['std_category']
                
                # 참조 규격 적용 (기존 값이 없는 경우)
                if not test_item.get('ref_standard'):
                    test_item['ref_standard'] = master.get('ref_standard', '')
                
                # 마스터 정보 추가
                test_item['master_info'] = master
        
        return test_item
    
    def standardize_all_items(self, test_items):
        """모든 시험 항목 표준화"""
        standardized_items = []
        for item in test_items:
            standardized_item = self.standardize_test_item(item)
            standardized_items.append(standardized_item)
            
            # 마스터 데이터 업데이트 (유사어 추가)
            if standardized_item.get('test_master_id'):
                original_name = standardized_item.get('test_name_original', '')
                if original_name and original_name != standardized_item.get('test_name'):
                    self.dm.update_master_aliases(
                        standardized_item['test_master_id'],
                        original_name
                    )
            else:
                # 매칭된 마스터가 없는 경우 새로운 마스터 추가
                self.add_new_master(standardized_item)
        
        return standardized_items
    
    def add_new_master(self, test_item):
        """새로운 마스터 데이터 추가"""
        std_name = test_item.get('test_name', '')
        std_category = test_item.get('category', '')
        ref_standard = test_item.get('ref_standard', '')
        aliases = [test_item.get('test_name_original', std_name)]
        
        if std_name:
            new_id = self.dm.add_master_test(std_name, std_category, ref_standard, aliases)
            test_item['test_master_id'] = new_id
            return new_id
        return None
    
    def get_standardization_status(self, test_item):
        """표준화 상태 확인"""
        test_master_id = test_item.get('test_master_id', '')
        if test_master_id:
            return "matched"
        return "unmatched"
