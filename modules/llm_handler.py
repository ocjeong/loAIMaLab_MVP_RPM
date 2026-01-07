import google.generativeai as genai
import os
import base64
import json
from dotenv import load_dotenv

load_dotenv()

class LLMHandler:
    def __init__(self):
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            # Streamlit secrets에서 가져오기
            try:
                import streamlit as st
                api_key = st.secrets.get("GEMINI_API_KEY")
            except:
                pass
        
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
        else:
            self.model = None
    
    def extract_test_specifications(self, uploaded_file):
        """업로드된 파일에서 시험 규격 데이터 추출"""
        if not self.model:
            # API 키가 없을 경우 샘플 데이터 반환
            return self._get_sample_data()
        
        try:
            # 파일을 base64로 인코딩
            file_bytes = uploaded_file.read()
            file_b64 = base64.b64encode(file_bytes).decode('utf-8')
            
            # MIME 타입 결정
            mime_type = "application/pdf" if uploaded_file.name.endswith('.pdf') else \
                       "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            
            # 프롬프트 구성
            prompt = self._get_extraction_prompt()
            
            # API 호출
            response = self.model.generate_content([
                prompt,
                {
                    "mime_type": mime_type,
                    "data": file_b64
                }
            ])
            
            # JSON 파싱
            result_text = response.text
            # JSON 부분만 추출 (```json ... ``` 형태로 올 수 있음)
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0]
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0]
            
            extracted_data = json.loads(result_text.strip())
            return extracted_data
        
        except Exception as e:
            print(f"LLM 추출 오류: {str(e)}")
            # 오류 발생 시 샘플 데이터 반환
            return self._get_sample_data()
    
    def _get_extraction_prompt(self):
        """시험 규격 추출 프롬프트"""
        return """
# Role
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
{
  "request_info": { "client": "발주처명", "project": "프로젝트명" },
  "test_items": [
    {
      "test_name": "표준 시험명(예: High Temperature, Low Temperature, Noise, Random Vibration 등)",
      "category": "분류(예: Operational and Environmental tests, Electrical Tests 등)",
      "ref_standard": "참조 규격 (예: ISO 20653, ISO 16750-3 등)",
      "sample_assembly": "시험에 사용되는 시료의 부품 구성(예: Motor only, HVAC 등)",
      "test_sample_no": "시험에 사용되는 샘플 번호",
      "sample_count": "시료 수; 단일 시험 항목에 필요한 시료 수",
      "test_duration": "단일 시험 항목에 필요한 일수(days)",
      "test_instrument": "시험 기기 이름",
      "test_master_id": "매핑 된 시험 마스터 데이터 ID",
      "custom_specs": {
        "temperature": "온도 조건(단위 포함)",
        "voltage": "전압 조건(단위 포함)",
        "other_conditions_1": "기타 특이사항1",
        "other_conditions_2": "기타 특이사항2"
      }
    }
  ]
}

# test_master (표준 시험 규격 정의) (JSON)
[
  {
    "id": "M001",
    "std_name": "On & Off Test",
    "std_category": "Endurance Test",
    "ref_standard": "",
    "aliases": ["작동성 시험", "온오프"]
  },
  {
    "id": "M002",
    "std_name": "High Temperature Test",
    "std_category": "Environmental Test",
    "ref_standard": "ISO 16750-3",
    "aliases": ["고온 시험", "고온 내구"]
  },
  {
    "id": "M003",
    "std_name": "Low Temperature Test",
    "std_category": "Environmental Test",
    "ref_standard": "ISO 16750-3",
    "aliases": ["저온 시험", "저온 내구"]
  },
  {
    "id": "M004",
    "std_name": "Noise Test",
    "std_category": "Operational and Environmental tests",
    "ref_standard": "",
    "aliases": ["소음 시험", "소음 측정"]
  },
  {
    "id": "M005",
    "std_name": "Random Vibration Test",
    "std_category": "Environmental Test",
    "ref_standard": "ISO 16750-3",
    "aliases": ["진동 시험", "랜덤 진동"]
  },
  {
    "id": "M006",
    "std_name": "Dust Protection Test",
    "std_category": "Environmental Test",
    "ref_standard": "ISO 20653",
    "aliases": ["방진 시험", "먼지 보호"]
  },
  {
    "id": "M007",
    "std_name": "Water Protection Test",
    "std_category": "Environmental Test",
    "ref_standard": "ISO 20653",
    "aliases": ["방수 시험", "침수 시험"]
  },
  {
    "id": "M008",
    "std_name": "Salt Spray Test",
    "std_category": "Environmental Test",
    "ref_standard": "ISO 9227",
    "aliases": ["염수 분무", "내식성 시험"]
  },
  {
    "id": "M009",
    "std_name": "Undervoltage and Overvoltage Test",
    "std_category": "Electrical Tests",
    "ref_standard": "ISO 16750-3",
    "aliases": ["과저전압", "정지 전압 확인"]
  },
  {
    "id": "M010",
    "std_name": "Reverse Polarity Test",
    "std_category": "Electrical Tests",
    "ref_standard": "ISO 16750-3",
    "aliases": ["역극성", "극성 반전"]
  }
]
"""
    
    def _get_sample_data(self):
        """API 키가 없거나 오류 발생 시 반환할 샘플 데이터"""
        return {
            "request_info": {
                "client": "샘플 발주처",
                "project": "샘플 프로젝트"
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
                    "test_equipment": "Chamber",
                    "test_master_id": "M002",
                    "custom_specs": {
                        "temperature": "85°C",
                        "duration": "1000hr"
                    }
                },
                {
                    "test_name": "Low Temperature Test",
                    "category": "Environmental Test",
                    "ref_standard": "ISO 16750-3",
                    "sample_assembly": "Motor only",
                    "test_sample_no": "S002",
                    "sample_count": "3",
                    "test_duration": "7",
                    "test_equipment": "Chamber",
                    "test_master_id": "M003",
                    "custom_specs": {
                        "temperature": "-40°C",
                        "duration": "1000hr"
                    }
                },
                {
                    "test_name": "Noise Test",
                    "category": "Operational and Environmental tests",
                    "ref_standard": "",
                    "sample_assembly": "HVAC",
                    "test_sample_no": "S003",
                    "sample_count": "3",
                    "test_duration": "2",
                    "test_equipment": "Anechoic Chamber",
                    "test_master_id": "M004",
                    "custom_specs": {
                        "measurement": "Sound pressure level"
                    }
                }
            ]
        }
