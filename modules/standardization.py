from typing import Dict, Any, Optional


def get_master_by_id(master_id: str, db) -> Optional[Dict[str, Any]]:
    """
    마스터 ID로 마스터 데이터 조회
    
    Args:
        master_id: 마스터 ID
        db: DatabaseManager 인스턴스
        
    Returns:
        마스터 데이터 딕셔너리 또는 None
    """
    return db.get_master_by_id(master_id)


def standardize_test_item(test_item: Dict[str, Any], db) -> Dict[str, Any]:
    """
    시험 항목을 마스터 데이터 기준으로 표준화
    
    Args:
        test_item: 시험 항목 딕셔너리
        db: DatabaseManager 인스턴스
        
    Returns:
        표준화된 시험 항목 딕셔너리
    """
    # 원본 데이터 보존
    standardized_item = test_item.copy()
    
    # test_master_id가 존재하는 경우
    if test_item.get('test_master_id'):
        master = get_master_by_id(test_item['test_master_id'], db)
        
        if master:
            # 원본 값 보존
            standardized_item['test_name_original'] = test_item.get('test_name', '')
            standardized_item['category_original'] = test_item.get('category', '')
            
            # 표준화 적용
            standardized_item['test_name'] = master.get('std_name', test_item.get('test_name', ''))
            standardized_item['category'] = master.get('std_category', test_item.get('category', ''))
            
            # ref_standard가 없는 경우 마스터에서 가져오기
            if not standardized_item.get('ref_standard'):
                standardized_item['ref_standard'] = master.get('ref_standard', '')
    else:
        # 매칭되지 않은 경우 원본 유지
        standardized_item['test_name_original'] = test_item.get('test_name', '')
        standardized_item['category_original'] = test_item.get('category', '')
    
    return standardized_item


def find_similar_master(test_name: str, category: str, db) -> Optional[str]:
    """
    유사한 마스터 데이터 찾기 (간단한 키워드 매칭)
    
    Args:
        test_name: 시험명
        category: 분류
        db: DatabaseManager 인스턴스
        
    Returns:
        매칭된 마스터 ID 또는 None
    """
    masters = db.get_all_masters()
    
    test_name_lower = test_name.lower()
    
    for master in masters:
        # 표준명과 비교
        if master['std_name'].lower() in test_name_lower or test_name_lower in master['std_name'].lower():
            return master['id']
        
        # 유사어와 비교
        aliases = master.get('aliases', [])
        for alias in aliases:
            if alias.lower() in test_name_lower or test_name_lower in alias.lower():
                return master['id']
    
    return None


def batch_standardize(test_items: list, db) -> list:
    """
    여러 시험 항목을 일괄 표준화
    
    Args:
        test_items: 시험 항목 리스트
        db: DatabaseManager 인스턴스
        
    Returns:
        표준화된 시험 항목 리스트
    """
    standardized_items = []
    
    for item in test_items:
        # test_master_id가 없는 경우 자동 매칭 시도
        if not item.get('test_master_id'):
            matched_id = find_similar_master(
                item.get('test_name', ''),
                item.get('category', ''),
                db
            )
            if matched_id:
                item['test_master_id'] = matched_id
        
        # 표준화 적용
        standardized_item = standardize_test_item(item, db)
        standardized_items.append(standardized_item)
    
    return standardized_items
