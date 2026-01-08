import google.generativeai as genai
import json
import base64
from config import GEMINI_API_KEY, GEMINI_MODEL

class LLMHandler:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel(GEMINI_MODEL)
    
    def extract_test_data(self, file_content, file_type):
        """문서에서 시험 데이터 추출"""
        # 마스터 데이터 가져오기
        masters = self.db_manager.get_all_masters()
        master_list = []
        for _, row in masters.iterrows():
            try:
                aliases = json.loads(row['aliases']) if pd.notna(row['aliases']) else []
            except:
                aliases = []
            
            master_list.append({
                'id': row['id'],
                'std_name': row['std_name'],
                'std_category': row['std_category'],
                'ref_standard': row['ref_standard'],
                'aliases': aliases
            })
        
        # 프롬프트 생성
        prompt = self._create_extraction_prompt(master_list)
        
        try:
            # 파일 업로드 및 처리
            if file_type == 'application/pdf':
                mime_type = 'application/pdf'
            else:
                mime_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            
            # Gemini API 호출
            uploaded_file = genai.upload_file(file_content, mime_type=mime_type)
            
            response = self.model.generate_content([
                prompt,
                uploaded_file
            ])
            
            # JSON 파싱
            response_text = response.text
            # JSON 코드 블록 제거
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0]
            elif '```' in response_text:
                response_text = response_text.split('```')[1].split('```')[0]
            
            result = json.loads(response_text.strip())
            return result
        
        except Exception as e:
            print(f"LLM 추출 오류: {str(e)}")
            return None
    
    def _create_extraction_prompt(self, master_list):
        """시험 규격 추출 프롬프트 생성"""
        prompt = f"""# Role
너는 차량용 블로워 모터(Blower Motor) 시험 규격 분석가야.
첨부된 비정형 제품 시험 규격 문서에서 핵심 시험 항목과 조건을 추출하여 정해진 JSON 형식으로 변환하는 업무를 수행해.

# Objective
1. 각 시험 항목을 식별하고 test_master(표준 시험 규격 정의)와 매핑해 master의 'id'값을 'test_master_id' 필드에 표기할 것.
2. 시험별 세부 조건(온도, 전압, 시간 등)을 정밀하게 추출할 것.
3. 발주처 별 특수 요구사항이나 예외 조건 등 정의된 필드가 없는 값은 'custom_specs'에 하위 필드를 추가하여 상세히 출력할 것.

# Extraction Rules
1. **정규화**: 충분히 유사한 test_master가 없을 경우 'test_master_id' 필드에 공백("")으로 출력
2. **표기 보존**: 모든 수치는 문서에 기재된 단어를 그대로 유지(예: 85C, 1000hr, 12V).
3. **누락 처리**: 시험 규격 문서에 정보가 없는 필드는 null이 아닌 공백("")으로 출력.
4. **엄격한 형식**: JSON 외의 설명이나 서론은 생략하고 순수 JSON 코드만 출력할 것.

# Schema Definition (JSON)
{{
  "request_info": {{ "client": "발주처명", "project": "프로젝트명" }},
  "test_items": [
    {{
      "test_name": "표준 시험명(예: High Temperature, Low Temperature, Noise, Random Vibration 등)",
      "category": "분류(예: Operational and Environmental tests, Electrical Tests 등)",
      "ref_standard": "참조 규격 (예: ISO 20653, ISO 16750-3 등)",
      "sample_assembly": "시험에 사용되는 시료의 부품 구성(예: Motor only, HVAC 등)",
      "test_sample_no": "시험에 사용되는 샘플 번호",
      "sample_count": "시료 수; 단일 시험 항목에 필요한 시료 수",
      "test_duration": "단일 시험 항목에 필요한 일수(days)",
      "test_equipment": "시험 기기 이름",
      "test_master_id": "매핑 된 시험 마스터 데이터 ID",
      "custom_specs": {{
        "example_conditions_1": "예시 특이사항 1; 해당 시험 세부 조건",
        "example_conditions_2": "예시 특이사항 2; 발주처 특화 시험 조건",
        "example_conditions_3": "예시 특이사항 3; 제품 특화 시험 조건"
      }}
    }}
  ]
}}

# test_master (표준 시험 규격 정의) (JSON)
{json.dumps(master_list, ensure_ascii=False, indent=2)}
"""
        return prompt
    
    def standardize_test_item(self, test_item):
        """시험 항목 표준화"""
        if not test_item.get('test_master_id') or test_item['test_master_id'] == '':
            return test_item
        
        master = self.db_manager.get_master_by_id(test_item['test_master_id'])
        if not master:
            return test_item
        
        # 원본 데이터 보존
        if 'test_name_original' not in test_item or not test_item['test_name_original']:
            test_item['test_name_original'] = test_item.get('test_name', '')
        if 'category_original' not in test_item or not test_item['category_original']:
            test_item['category_original'] = test_item.get('category', '')
        
        # 표준화 적용
        test_item['test_name'] = master['std_name']
        test_item['category'] = master['std_category']
        if not test_item.get('ref_standard'):
            test_item['ref_standard'] = master['ref_standard']
        
        return test_item

import pandas as pd
