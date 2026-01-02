import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict
import io

def validate_test_items(test_items: List[Dict]) -> List[Dict]:
    """시험 항목 데이터 검증 및 정제"""
    
    validated_items = []
    
    for item in test_items:
        validated_item = {
            'test_name': item.get('test_name', ''),
            'category': item.get('category', ''),
            'ref_standard': item.get('ref_standard', ''),
            'sample_assembly': item.get('sample_assembly', ''),
            'test_sample_no': int(item.get('test_sample_no', 0)),
            'sample_count': int(item.get('sample_count', 1)),
            'test_duration': float(item.get('test_duration', 1.0)),
            'test_equipment': item.get('test_equipment', ''),
            'test_master_id': item.get('test_master_id', ''),
            'custom_specs': item.get('custom_specs', {})
        }
        
        validated_items.append(validated_item)
    
    return validated_items

def sort_test_items_by_priority(test_items: List[Dict]) -> List[Dict]:
    """시험 항목 우선순위 정렬"""
    
    priority_map = {
        'Environmental': 1,
        'Electrical': 2,
        'Endurance': 3,
    }
    
    def get_priority(item):
        category = item.get('category', '')
        return priority_map.get(category, 99)
    
    return sorted(test_items, key=get_priority)

def generate_planning_dataframe(test_items: List[Dict], start_date: datetime = None) -> pd.DataFrame:
    """계획서 데이터프레임 생성"""
    
    if start_date is None:
        start_date = datetime.now()
    
    planning_data = []
    current_date = start_date
    
    for idx, item in enumerate(test_items):
        duration = item.get('test_duration', 1.0)
        end_date = current_date + timedelta(days=duration)
        
        planning_data.append({
            '순번': idx + 1,
            '분류': item.get('category', ''),
            '시험명': item.get('test_name', ''),
            '시료수': item.get('sample_count', 0),
            '소요일수': duration,
            '시작일': current_date.strftime('%Y-%m-%d'),
            '종료일': end_date.strftime('%Y-%m-%d'),
            '비고': '',
            '포함': True
        })
        
        current_date = end_date
    
    return pd.DataFrame(planning_data)

def convert_df_to_excel(df: pd.DataFrame) -> bytes:
    """데이터프레임을 Excel 파일로 변환"""
    
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='시험계획서')
        
        # 워크시트 포맷팅
        worksheet = writer.sheets['시험계획서']
        
        # 열 너비 조정
        for idx, col in enumerate(df.columns):
            max_length = max(
                df[col].astype(str).apply(len).max(),
                len(col)
            )
            worksheet.column_dimensions[chr(65 + idx)].width = min(max_length + 2, 50)
    
    return output.getvalue()

def calculate_schedule_dates(test_items: List[Dict], start_date: datetime) -> List[Dict]:
    """일정 날짜 계산"""
    
    scheduled_items = []
    current_date = start_date
    
    for item in test_items:
        if item.get('is_included', True):
            duration = item.get('test_duration', 1.0)
            end_date = current_date + timedelta(days=duration)
            
            scheduled_item = item.copy()
            scheduled_item['start_date'] = current_date.strftime('%Y-%m-%d')
            scheduled_item['end_date'] = end_date.strftime('%Y-%m-%d')
            
            scheduled_items.append(scheduled_item)
            current_date = end_date
    
    return scheduled_items
