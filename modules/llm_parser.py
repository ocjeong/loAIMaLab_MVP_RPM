import google.generativeai as genai
import json
import base64
import streamlit as st
from modules.data_manager import DataManager

class LLMParser:
    def __init__(self, api_key):
        self.api_key = api_key
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        self.dm = DataManager()
    
    def get_extraction_prompt(self):
        """시험 규격 데이터 추출 프롬프트 생성"""
        # 마스터 데이터 로드
        master_df = self.dm.load_master_test()
        master_list = []
        
        for _, row in master_df.iterrows():
            master_list.append({
                "id": row['id'],
                "std_name": row['std_name'],
                "std_category": row['std_category'],
                "ref_standard": row['ref_standard'],
                "aliases": json.loads(row['aliases']) if pd.notna(row['aliases']) else []
            })
        
        prompt = f"""# Role
너는 차량용 블로워 모터(Blower Motor) 시험 규격 분석가야. 첨부된 비정형 제품 시험 규격 문서에서 핵심 시험 항목과 조건을 추출하여 정해진 JSON 형식으로 변환하는 업무를 수행해.

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
  "request_info": {{
    "client": "발주처명",
    "project": "프로젝트명"
  }},
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

문서를 분석하고 위 형식에 맞춰 JSON만 출력해줘."""
        
        return prompt
    
    def parse_document(self, file_bytes, file_type):
        """문서 파싱 및 데이터 추출"""
        try:
            # Base64 인코딩
            base64_data = base64.b64encode(file_bytes).decode('utf-8')
            
            # MIME 타입 설정
            mime_type = "application/pdf" if file_type == "pdf" else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            
            # 프롬프트 생성
            prompt = self.get_extraction_prompt()
            
            # API 호출
            response = self.model.generate_content([
                prompt,
                {
                    "mime_type": mime_type,
                    "data": base64_data
                }
            ])
            
            # JSON 파싱
            response_text = response.text.strip()
            
            # 마크다운 코드 블록 제거
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            response_text = response_text.strip()
            
            result = json.loads(response_text)
            
            return result
            
        except Exception as e:
            st.error(f"문서 파싱 중 오류 발생: {str(e)}")
            return None
    
    def extract_sample_data(self):
        """샘플 데이터 생성 (테스트용)"""
        return {
            "request_info": {
                "client": "Sample Client",
                "project": "Blower Motor Test Project"
            },
            "test_items": [
                {
                    "test_name": "High Temperature Test",
                    "category": "Environmental Test",
                    "ref_standard": "ISO 16750-3",
                    "sample_assembly": "Motor only",
                    "test_sample_no": "S001",
                    "sample_count": "3",
                    "test_duration": "7",
                    "test_equipment": "Temperature Chamber",
                    "test_master_id": "M002",
                    "custom_specs": {
                        "temperature": "85°C",
                        "duration": "1000 hours"
                    }
                },
                {
                    "test_name": "Low Temperature Test",
                    "category": "Environmental Test",
                    "ref_standard": "ISO 16750-3",
                    "sample_assembly": "Motor only",
                    "test_sample_no": "S002",
                    "sample_count": "3",
                    "test_duration": "5",
                    "test_equipment": "Temperature Chamber",
                    "test_master_id": "M003",
                    "custom_specs": {
                        "temperature": "-40°C",
                        "duration": "500 hours"
                    }
                },
                {
                    "test_name": "Undervoltage and Overvoltage Test",
                    "category": "Electrical Tests",
                    "ref_standard": "ISO 16750-3",
                    "sample_assembly": "HVAC",
                    "test_sample_no": "S003",
                    "sample_count": "3",
                    "test_duration": "3",
                    "test_equipment": "Power Supply",
                    "test_master_id": "M009",
                    "custom_specs": {
                        "undervoltage": "9V",
                        "overvoltage": "16V",
                        "cycles": "100"
                    }
                }
            ]
        }

import pandas as pd
