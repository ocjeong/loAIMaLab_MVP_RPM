import pandas as pd

def get_master_by_id(master_id, master_data):
    """마스터 ID로 마스터 데이터 조회"""
    result = master_data[master_data['id'] == master_id]
    if not result.empty:
        return result.iloc[0].to_dict()
    return None

def standardize_test_item(test_item, master_data):
    """시험 항목을 마스터 데이터 기준으로 표준화"""
    # 원본 데이터 보존
    if 'test_name' in test_item and 'test_name_original' not in test_item:
        test_item['test_name_original'] = test_item.get('test_name', '')
    if 'category' in test_item and 'category_original' not in test_item:
        test_item['category_original'] = test_item.get('category', '')
    
    # test_master_id가 있으면 표준화 적용
    if test_item.get('test_master_id'):
        master = get_master_by_id(test_item['test_master_id'], master_data)
        if master:
            # 표준명 적용
            test_item['test_name'] = master.get('std_name', test_item.get('test_name', ''))
            test_item['category'] = master.get('std_category', test_item.get('category', ''))
            
            # ref_standard가 없으면 마스터에서 가져오기
            if not test_item.get('ref_standard'):
                test_item['ref_standard'] = master.get('ref_standard', '')
    
    return test_item
