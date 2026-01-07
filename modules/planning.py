import pandas as pd
from io import BytesIO
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from collections import Counter

class PlanningModule:
    def __init__(self):
        self.default_sample_per_group = 3
        self.default_sample_per_individual = 3
    
    def create_plan(self, test_items):
        """시험 계획서 초안 생성"""
        
        # Functional Test 자동 생성
        plan_data = self._add_functional_test(test_items)
        
        # 그룹 자동 판별
        plan_data = self._determine_groups(plan_data)
        
        return plan_data
    
    def _add_functional_test(self, test_items):
        """Functional Test 자동 생성"""
        
        # 기능 시험이 이미 있는지 확인
        has_functional = any(
            'functional' in item.get('test_name', '').lower() or
            item.get('category', '') == 'Functional Test'
            for item in test_items
        )
        
        if not has_functional:
            # 가장 많이 출현한 컴포넌트 찾기
            components = [item.get('sample_assembly', '') for item in test_items if item.get('sample_assembly')]
            if components:
                most_common_component = Counter(components).most_common(1)[0][0]
            else:
                most_common_component = "Motor"
            
            # Functional Test 항목 생성
            functional_test = {
                'test_name': 'Functional Test',
                'category': 'Functional Test',
                'ref_standard': '',
                'sample_assembly': most_common_component,
                'test_sample_no': 'F001',
                'sample_count': str(self.default_sample_per_individual),
                'test_duration': '1',
                'test_equipment': '',
                'test_master_id': 'M008',
                'custom_specs': {}
            }
            
            # 최상단에 추가
            return [functional_test] + test_items
        
        return test_items
    
    def _determine_groups(self, test_items):
        """그룹 자동 판별"""
        
        # 샘플 번호별로 그룹화
        sample_groups = {}
        for item in test_items:
            sample_no = item.get('test_sample_no', '')
            if sample_no:
                if sample_no not in sample_groups:
                    sample_groups[sample_no] = []
                sample_groups[sample_no].append(item)
        
        # 그룹 타입 결정
        for item in test_items:
            sample_no = item.get('test_sample_no', '')
            if sample_no and len(sample_groups.get(sample_no, [])) > 1:
                item['group_type'] = 'Sequence'
            else:
                item['group_type'] = 'Individual'
        
        return test_items
    
    def calculate_total_samples(self, plan_data):
        """총 시료 수 계산"""
        
        total = 0
        processed_sequences = set()
        
        for item in plan_data:
            group_type = item.get('group_type', 'Individual')
            sample_no = item.get('test_sample_no', '')
            
            if group_type == 'Sequence':
                if sample_no not in processed_sequences:
                    total += self.default_sample_per_group
                    processed_sequences.add(sample_no)
            else:
                total += self.default_sample_per_individual
        
        return total
    
    def export_to_excel(self, plan_data, user_name):
        """Excel 파일로 내보내기"""
        
        wb = Workbook()
        ws = wb.active
        ws.title = "Test Plan"
        
        # 헤더 정의
        headers = [
            "No", "Group", "Specification", "§", "Test Title", "Component",
            "Test by.", "Sample quantity", "Test Timing", "Start", "End",
            "OK/NOK", "Result", "Remark", "Customer Feedback"
        ]
        
        # 헤더 스타일
        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF")
        header_alignment = Alignment(horizontal="center", vertical="center")
        
        # 헤더 작성
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_num, value=header)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = header_alignment
        
        # 데이터 작성
        row_num = 2
        section_counters = {}
        
        # 카테고리별로 그룹화
        categories = {}
        for item in plan_data:
            category = item.get('category', 'Other')
            if category not in categories:
                categories[category] = []
            categories[category].append(item)
        
        # 섹션별로 작성
        for category, items in categories.items():
            # 섹션 헤더
            ws.cell(row=row_num, column=1, value=category)
            ws.merge_cells(start_row=row_num, start_column=1, end_row=row_num, end_column=len(headers))
            section_cell = ws.cell(row=row_num, column=1)
            section_cell.font = Font(bold=True, size=12)
            section_cell.fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
            row_num += 1
            
            # 항목 작성
            if category not in section_counters:
                section_counters[category] = 1
            
            for idx, item in enumerate(items, 1):
                # § 번호 생성
                section_num = f"{len(section_counters)}.1.{section_counters[category]}"
                section_counters[category] += 1
                
                row_data = [
                    idx,
                    item.get('group_type', 'Individual'),
                    item.get('ref_standard', ''),
                    section_num,
                    item.get('test_name', ''),
                    item.get('sample_assembly', ''),
                    '',  # Test by
                    item.get('sample_count', ''),
                    '',  # Test Timing
                    '',  # Start
                    '',  # End
                    '',  # OK/NOK
                    '',  # Result
                    '',  # Remark
                    ''   # Customer Feedback
                ]
                
                for col_num, value in enumerate(row_data, 1):
                    cell = ws.cell(row=row_num, column=col_num, value=value)
                    cell.alignment = Alignment(horizontal="center", vertical="center")
                    
                    # Functional Test 하이라이트
                    if 'functional' in item.get('test_name', '').lower():
                        cell.fill = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")
                
                row_num += 1
        
        # 열 너비 조정
        column_widths = [5, 12, 15, 8, 25, 15, 12, 12, 12, 10, 10, 8, 15, 15, 20]
        for col_num, width in enumerate(column_widths, 1):
            ws.column_dimensions[ws.cell(row=1, column=col_num).column_letter].width = width
        
        # 테두리 추가
        thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        
        for row in ws.iter_rows(min_row=1, max_row=row_num-1, min_col=1, max_col=len(headers)):
            for cell in row:
                cell.border = thin_border
        
        # BytesIO로 저장
        excel_file = BytesIO()
        wb.save(excel_file)
        excel_file.seek(0)
        
        return excel_file.getvalue()
    
    def load_sample_data(self):
        """샘플 데이터 로드"""
        return [
            {
                'test_name': 'Functional Test',
                'category': 'Functional Test',
                'ref_standard': '',
                'sample_assembly': 'Motor',
                'test_sample_no': 'F001',
                'sample_count': '3',
                'test_duration': '1',
                'group_type': 'Individual'
            },
            {
                'test_name': 'High Temperature Test',
                'category': 'Environmental Test',
                'ref_standard': 'ISO 16750-4',
                'sample_assembly': 'Motor only',
                'test_sample_no': 'S001',
                'sample_count': '3',
                'test_duration': '5',
                'group_type': 'Sequence'
            },
            {
                'test_name': 'Low Temperature Test',
                'category': 'Environmental Test',
                'ref_standard': 'ISO 16750-4',
                'sample_assembly': 'Motor only',
                'test_sample_no': 'S001',
                'sample_count': '3',
                'test_duration': '5',
                'group_type': 'Sequence'
            }
        ]
