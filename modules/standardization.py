from modules.database import DatabaseManager

def get_master_by_id(master_id):
    """마스터 ID로 마스터 데이터 조회"""
    db = DatabaseManager()
    return db.get_master_by_id(master_id)

def standardize_test_item(test_item):
    """시험 항목을 마스터 데이터 기준으로 표준화"""
    
    # test_master_id가 없으면 원본 그대로 반환
    if not test_item.get('test_master_id'):
        return test_item
    
    # 마스터 데이터 조회
    master = get_master_by_id(test_item['test_master_id'])
    
    if not master:
        return test_item
    
    # 원본 데이터 보존
    if 'test_name_original' not in test_item:
        test_item['test_name_original'] = test_item.get('test_name', '')
    
    if 'category_original' not in test_item:
        test_item['category_original'] = test_item.get('category', '')
    
    # 표준화 적용
    test_item['test_name'] = master.get('std_name', test_item.get('test_name', ''))
    test_item['category'] = master.get('std_category', test_item.get('category', ''))
    
    # ref_standard가 없는 경우에만 마스터의 값 적용
    if not test_item.get('ref_standard'):
        test_item['ref_standard'] = master.get('ref_standard', '')
    
    return test_item
