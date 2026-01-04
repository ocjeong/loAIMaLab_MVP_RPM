import pandas as pd
from io import BytesIO
from datetime import datetime

class Utils:
    def save_plan_to_excel(self, plan_df, request_info):
        """계획서를 Excel 파일로 저장"""
        try:
            output = BytesIO()
            
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                # 의뢰 정보 시트
                info_df = pd.DataFrame([request_info])
                info_df.to_excel(writer, sheet_name='의뢰정보', index=False)
                
                # 계획서 시트
                plan_df.to_excel(writer, sheet_name='시험계획서', index=False)
            
            output.seek(0)
            return output.getvalue()
        except Exception as e:
            print(f"Error saving plan to Excel: {e}")
            return None
    
    def parse_duration(self, duration_str):
        """소요일수 문자열 파싱"""
        try:
            return int(str(duration_str).replace('days', '').strip())
        except:
            return 1
    
    def format_date(self, date):
        """날짜 포맷팅"""
        if isinstance(date, str):
            return date
        return date.strftime('%Y-%m-%d')
