import streamlit as st
import pandas as pd
from io import BytesIO
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

def init_session_state():
    """세션 상태 초기화"""
    if 'page' not in st.session_state:
        st.session_state.page = 'user_selection'
    if 'current_user' not in st.session_state:
        st.session_state.current_user = None
    if 'current_request' not in st.session_state:
        st.session_state.current_request = None
    if 'current_test_items' not in st.session_state:
        st.session_state.current_test_items = []

def save_to_excel(df, request_info):
    """DataFrame을 엑셀 파일로 변환"""
    output = BytesIO()
    
    # Workbook 생성
    wb = Workbook()
    ws = wb.active
    ws.title = "Test Plan"
    
    # 헤더 정의
    headers = ['No', 'Group', 'Specification', '§', 'Test Title', 'Component', 
               'Test by.', 'Sample quantity', 'Test Timing', 'Start', 'End', 
               'OK/NOK', 'Result', 'Remark', 'Customer Feedback']
    
    # 헤더 스타일
    header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF")
    border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    # 헤더 작성
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.border = border
        cell.alignment = Alignment(horizontal='center', vertical='center')
    
    # 데이터 작성
    row_num = 2
    for idx, row in df.iterrows():
        ws.cell(row=row_num, column=1, value=idx+1)
        ws.cell(row=row_num, column=2, value='Individual')
        ws.cell(row=row_num, column=3, value=row.get('ref_standard', ''))
        ws.cell(row=row_num, column=4, value=f"1.{idx+1}.1")
        ws.cell(row=row_num, column=5, value=row.get('test_name', ''))
        ws.cell(row=row_num, column=6, value=row.get('sample_assembly', ''))
        ws.cell(row=row_num, column=7, value='')
        ws.cell(row=row_num, column=8, value=row.get('sample_count', ''))
        
        # 테두리 적용
        for col in range(1, len(headers) + 1):
            ws.cell(row=row_num, column=col).border = border
        
        row_num += 1
    
    # 열 너비 조정
    column_widths = [5, 12, 15, 8, 30, 15, 12, 12, 12, 10, 10, 10, 15, 15, 20]
    for idx, width in enumerate(column_widths, 1):
        ws.column_dimensions[ws.cell(row=1, column=idx).column_letter].width = width
    
    wb.save(output)
    output.seek(0)
    
    return output.getvalue()
