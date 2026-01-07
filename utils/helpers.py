from datetime import datetime

def format_date(date_str):
    """날짜 포맷팅"""
    if isinstance(date_str, str):
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            return date_obj.strftime('%Y년 %m월 %d일')
        except:
            return date_str
    return str(date_str)

def generate_id(prefix, number):
    """ID 생성 (예: U001, R00001, M001)"""
    if prefix == 'R':
        return f"{prefix}{str(number).zfill(5)}"
    else:
        return f"{prefix}{str(number).zfill(3)}"

def parse_duration(duration_str):
    """기간 문자열 파싱 (예: "5 days" -> 5)"""
    if isinstance(duration_str, (int, float)):
        return int(duration_str)
    
    if isinstance(duration_str, str):
        # 숫자만 추출
        import re
        numbers = re.findall(r'\d+', duration_str)
        if numbers:
            return int(numbers[0])
    
    return 1  # 기본값
