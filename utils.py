import plotly.express as px
import plotly.figure_factory as ff
import pandas as pd
from io import BytesIO
from datetime import datetime

def create_gantt_chart(data, title="시험 일정"):
    """Gantt Chart 생성"""
    if not data:
        return None
    
    df = pd.DataFrame(data)
    
    # Plotly Figure Factory를 사용한 Gantt Chart
    fig = ff.create_gantt(
        df,
        colors='Category' if 'Category' in df.columns else None,
        index_col='Category' if 'Category' in df.columns else None,
        show_colorbar=True,
        group_tasks=True,
        title=title
    )
    
    fig.update_layout(
        xaxis_title="날짜",
        yaxis_title="시험 항목",
        height=max(400, len(data) * 40),
        hovermode='closest'
    )
    
    return fig


def export_to_excel(df: pd.DataFrame, request_id: str) -> bytes:
    """DataFrame을 Excel 파일로 변환"""
    output = BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='계획서', index=False)
        
        # 워크시트 포맷팅
        workbook = writer.book
        worksheet = writer.sheets['계획서']
        
        # 헤더 스타일
        header_fill = openpyxl.styles.PatternFill(start_color="1F77B4", end_color="1F77B4", fill_type="solid")
        header_font = openpyxl.styles.Font(bold=True, color="FFFFFF")
        
        for cell in worksheet[1]:
            cell.fill = header_fill
            cell.font = header_font
        
        # 열 너비 자동 조정
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(cell.value)
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width
    
    output.seek(0)
    return output.getvalue()


try:
    import openpyxl
    import openpyxl.styles
except ImportError:
    # openpyxl이 없을 경우 기본 저장만 수행
    def export_to_excel(df: pd.DataFrame, request_id: str) -> bytes:
        output = BytesIO()
        df.to_excel(output, index=False, engine='openpyxl')
        output.seek(0)
        return output.getvalue()
