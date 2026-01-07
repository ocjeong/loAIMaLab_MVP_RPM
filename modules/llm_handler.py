import base64
import json
import os
import google.generativeai as genai
from typing import Dict, Any

class LLMHandler:
    def __init__(self):
        # Gemini API 키 설정 (환경 변수 또는 Streamlit secrets 사용)
        api_key = os.getenv('GEMINI_API_KEY') or self._get_api_key_from_secrets()
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        else:
            self.model = None
    
    def _get_api_key_from_secrets(self):
        """Streamlit secrets에서 API 키 가져오기"""
        try:
            import streamlit as st
            return st.secrets.get("GEMINI_API_KEY")
        except:
            return None
    
    def extract_test_data(self, uploaded_file) -> Dict[str, Any]:
        """시험 규격 문서에서 데이터 추출"""
        
        if not self.model:
            # API 키가 없을 경우 샘플 데이터 반환
            return self._get_sample_extracted_data()
        
        try:
            # 파일을 base64로 인코딩
            file_bytes = uploaded_file.read()
            file_base64 = base64.b64encode(file_bytes).decode('utf-8')
            
            # MIME 타입 결정
            mime_type = 'application/pdf' if uploaded_file.name.endswith('.pdf') else 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            
            # 마스터 데이터 로드
            from modules.database import DatabaseManager
            db = DatabaseManager()
            masters = db.load_master_data()
            master_json = masters.to_dict('records')
            
            # 프롬프트 생성
            prompt = self._create_extraction_prompt(master_json)
            
            # Gemini API 호출
            response = self.model.generate_content([
                prompt,
                {
                    'mime_type': mime_type,
                    'data': file_base64
                }
            ])
            
            # JSON 파싱
            result_text = response.text
            
            # JSON 추출 (마크다운 코드 블록 제거)
            if '```json' in result_text:
                result_text = result_text.split('```json')[1].split('```')[0]
            elif '```' in result_text:
                result_text = result_text.split('```')[1].split('```')[0]
            
            extracted_data = json.loads(result_text.strip())
            
            return extracted_data
            
        except Exception as e:
            print(f"LLM 추출 오류: {str(e)}")
            # 오류 시 샘플 데이터 반환
            return self._get_sample_extracted_data()
    
    def _create_extraction_prompt(self, master_data):
        """시험 규격 추출 프롬프트 생성"""
        
        master_json_str = json.dumps(master_data, ensure_ascii=False, indent=2)
        
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
        "temperature": "온도 조건(단위 포함)",
        "voltage": "전압 조건(단위 포함)",
        "other_conditions_1": "기타 특이사항1",
        "other_conditions_2": "기타 특이사항2"
      }}
    }}
  ]
}}

# test_master (표준 시험 규격 정의) (JSON)
{master_json_str}

위 정보를 바탕으로 첨부된 문서에서 시험 규격 데이터를 추출하여 JSON 형식으로 출력해줘.
"""
        
        return prompt
    
    def _get_sample_extracted_data(self):
        """샘플 추출 데이터 (API 키가 없거나 오류 시)"""
        return {
            "request_info": {
                "client": "Sample Client",
                "project": "Blower Motor Test Project"
            },
            "test_items": [
                {
                    "test_name": "High Temperature Test",
                    "category": "Environmental Test",
                    "ref_standard": "ISO 16750-4",
                    "sample_assembly": "Motor only",
                    "test_sample_no": "S001",
                    "sample_count": "3",
                    "test_duration": "5",
                    "test_instrument": "Temperature Chamber",
                    "test_master_id": "M002",
                    "custom_specs": {
                        "temperature": "85°C",
                        "duration": "1000 hours"
                    }
                },
                {
                    "test_name": "Low Temperature Test",
                    "category": "Environmental Test",
                    "ref_standard": "ISO 16750-4",
                    "sample_assembly": "Motor only",
                    "test_sample_no": "S002",
                    "sample_count": "3",
                    "test_duration": "5",
                    "test_instrument": "Temperature Chamber",
                    "test_master_id": "M003",
                    "custom_specs": {
                        "temperature": "-40°C",
                        "duration": "500 hours"
                    }
                },
                {
                    "test_name": "Noise Test",
                    "category": "Performance Test",
                    "ref_standard": "",
                    "sample_assembly": "HVAC",
                    "test_sample_no": "S003",
                    "sample_count": "3",
                    "test_duration": "2",
                    "test_instrument": "Sound Level Meter",
                    "test_master_id": "M004",
                    "custom_specs": {
                        "max_noise_level": "< 60 dB"
                    }
                }
            ]
        }
