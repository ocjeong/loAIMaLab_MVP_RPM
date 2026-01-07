def get_master_by_id(master_id, db):
    """마스터 ID로 마스터 데이터 조회"""
    result = db.master_test_df[db.master_test_df['id'] == master_id]
    if not result.empty:
        return result.iloc[0].to_dict()
    return None


def standardize_test_item(test_item, db):
    """시험 항목을 마스터 데이터 기준으로 표준화"""
    standardized_item = test_item.copy()
    
    # 원본 데이터 보존
    if 'test_name_original' not in standardized_item:
        standardized_item['test_name_original'] = test_item.get('test_name', '')
    if 'category_original' not in standardized_item:
        standardized_item['category_original'] = test_item.get('category', '')
    
    # test_master_id가 존재하면 표준화 적용
    if test_item.get('test_master_id'):
        master = get_master_by_id(test_item['test_master_id'], db)
        
        if master:
            # 표준명 적용
            standardized_item['test_name'] = master['std_name']
            standardized_item['category'] = master['std_category']
            
            # ref_standard 적용 (기존 값이 없는 경우)
            if not standardized_item.get('ref_standard'):
                standardized_item['ref_standard'] = master.get('ref_standard', '')
    
    return standardized_item
