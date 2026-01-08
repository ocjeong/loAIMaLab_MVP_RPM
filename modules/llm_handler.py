import google.generativeai as genai
import base64
import json
from typing import Dict, List, Optional
import os

class LLMHandler:
    def __init__(self, api_key: str):
        """Gemini API 초기화"""
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    def encode_file_to_base64(self, file_bytes: bytes) -> str:
        """파일을 Base64로 인코딩"""
        return base64.b64encode(file_bytes).decode('utf-8')
    
    def get_extraction_prompt(self, master_data: List[Dict]) -> str:
        """시험 규격 추출 프롬프트 생성"""
        master_json = json.dumps(master_data, ensure_ascii=False, indent=2)
        
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
      "test_name": "표준 시험명(예: High Temperature,  Low Temperature, Noise,  Random Vibration 등)",
      "category": "분류(예: Operational and Environmental tests, Electrical Tests 등)",
      "ref_standard": "참조 규격 (예: ISO 20653, ISO 16750-3 등)",
      "sample_assembly": "시험에 사용되는 시료의 부품 구성(예: Motor only, HVAC 등)",
      "test_sample_no": "시험에 사용되는 샘플 번호",
      "sample_count": "시료 수; 단일 시험 항목에 필요한 시료 수",
      "test_duration": "단일 시험 항목에 필요한 일수(days)",
      "test_instrument": "시험 기기 이름",
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
{master_json}
"""
        return prompt
    
    def extract_test_specifications(self, file_bytes: bytes, 
                                   mime_type: str, 
                                   master_data: List[Dict]) -> Optional[Dict]:
        """문서에서 시험 규격 추출"""
        try:
            prompt = self.get_extraction_prompt(master_data)
            
            # 파일 업로드
            file = genai.upload_file(path=None, mime_type=mime_type)
            
            # API 호출
            response = self.model.generate_content([
                prompt,
                file
            ])
            
            # JSON 추출
            response_text = response.text.strip()
            
            # 마크다운 코드 블록 제거
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            response_text = response_text.strip()
            
            # JSON 파싱
            result = json.loads(response_text)
            return result
            
        except Exception as e:
            print(f"LLM 추출 오류: {str(e)}")
            return None
