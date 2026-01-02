import base64
import json
import os
import google.generativeai as genai
from PyPDF2 import PdfReader
from docx import Document
import streamlit as st


class DocumentParser:
    """문서 파싱 및 지능형 추출 모듈"""
    
    def __init__(self):
        # Gemini API 키 설정
        api_key = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY"))
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        else:
            st.warning("⚠️ Gemini API 키가 설정되지 않았습니다. secrets.toml 파일을 확인해주세요.")
            self.model = None
    
    def parse_document(self, uploaded_file):
        """문서 파싱 및 데이터 추출"""
        try:
            # 파일 타입 확인
            file_extension = uploaded_file.name.split('.')[-1].lower()
            
            # 파일 내용 읽기
            file_content = uploaded_file.read()
            
            # Base64 인코딩
            base64_content = base64.b64encode(file_content).decode('utf-8')
            
            # MIME 타입 설정
            mime_type = self._get_mime_type(file_extension)
            
            # 마스터 데이터 로드 (실제로는 DB에서 가져와야 함)
            master_data = self._load_master_data()
            
            # 프롬프트 생성
            prompt = self._create_extraction_prompt(master_data)
            
            # Gemini API 호출
            if self.model:
                extracted_data = self._call_gemini_api(prompt, base64_content, mime_type)
                return extracted_data
            else:
                # API 키가 없을 경우 더미 데이터 반환
                return self._create_dummy_data()
        
        except Exception as e:
            st.error(f"문서 파싱 중 오류 발생: {str(e)}")
            return None
    
    def _get_mime_type(self, file_extension):
        """파일 확장자에 따른 MIME 타입 반환"""
        mime_types = {
            'pdf': 'application/pdf',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        }
        return mime_types.get(file_extension, 'application/octet-stream')
    
    def _load_master_data(self):
        """마스터 데이터 로드 (실제로는 DB에서)"""
        # 더미 마스터 데이터
        return [
            {
                "id": "M001",
                "std_name": "High Temperature Test",
                "std_category": "Operational and Environmental tests",
                "ref_standard": "ISO 16750-4",
                "aliases": ["고온", "고온시험", "열충격"]
            },
            {
                "id": "M002",
                "std_name": "Low Temperature Test",
                "std_category": "Operational and Environmental tests",
                "ref_standard": "ISO 16750-4",
                "aliases": ["저온", "저온시험", "냉각"]
            },
            {
                "id": "M003",
                "std_name": "Vibration Test",
                "std_category": "Operational and Environmental tests",
                "ref_standard": "ISO 16750-3",
                "aliases": ["진동", "진동시험", "Random Vibration"]
            },
            {
                "id": "M004",
                "std_name": "Noise Test",
                "std_category": "Performance Tests",
                "ref_standard": "",
                "aliases": ["소음", "소음시험", "음향"]
            },
            {
                "id": "M005",
                "std_name": "Undervoltage and Overvoltage Test",
                "std_category": "Electrical Tests",
                "ref_standard": "ISO 16750-3",
                "aliases": ["과저전압", "정지 전압 확인", "저전압 시험"]
            }
        ]
    
    def _create_extraction_prompt(self, master_data):
        """추출 프롬프트 생성"""
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
      "test_equipment": "시험 기기 이름",
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
{master_json}

문서를 분석하고 위 스키마에 맞춰 JSON만 출력해줘."""

        return prompt
    
    def _call_gemini_api(self, prompt, base64_content, mime_type):
        """Gemini API 호출"""
        try:
            # 파일 데이터 준비
            file_data = {
                'mime_type': mime_type,
                'data': base64_content
            }
            
            # API 호출
            response = self.model.generate_content([
                prompt,
                file_data
            ])
            
            # 응답 파싱
            response_text = response.text
            
            # JSON 추출 (```json ``` 제거)
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0]
            elif '```' in response_text:
                response_text = response_text.split('```')[1].split('```')[0]
            
            # JSON 파싱
            extracted_data = json.loads(response_text.strip())
            
            return extracted_data
        
        except Exception as e:
            st.error(f"Gemini API 호출 중 오류: {str(e)}")
            return self._create_dummy_data()
    
    def _create_dummy_data(self):
        """더미 데이터 생성 (테스트용)"""
        return {
            "request_info": {
                "client": "테스트 발주처",
                "project": "테스트 프로젝트"
            },
            "test_items": [
                {
                    "test_name": "High Temperature Test",
                    "category": "Operational and Environmental tests",
                    "ref_standard": "ISO 16750-4",
                    "sample_assembly": "Motor only",
                    "test_sample_no": "S001",
                    "sample_count": "3",
                    "test_duration": "5",
                    "test_equipment": "Chamber A",
                    "test_master_id": "M001",
                    "custom_specs": {
                        "temperature": "85°C",
                        "duration": "1000 hours",
                        "voltage": "12V"
                    }
                },
                {
                    "test_name": "Vibration Test",
                    "category": "Operational and Environmental tests",
                    "ref_standard": "ISO 16750-3",
                    "sample_assembly": "HVAC",
                    "test_sample_no": "S002",
                    "sample_count": "2",
                    "test_duration": "3",
                    "test_equipment": "Vibration Shaker",
                    "test_master_id": "M003",
                    "custom_specs": {
                        "frequency": "10-2000 Hz",
                        "acceleration": "5g RMS"
                    }
                }
            ]
        }
