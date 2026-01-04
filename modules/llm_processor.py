import base64
import json
import os
import requests

class LLMProcessor:
    def __init__(self, database):
        self.db = database
        self.api_key = os.getenv('GEMINI_API_KEY', '')
    
    def process_document(self, uploaded_file):
        """
        문서 처리 및 데이터 추출
        """
        # 실제 API 사용 시
        if self.api_key:
            try:
                # 파일 읽기
                file_content = uploaded_file.read()
                
                # MIME 타입 결정
                mime_type = uploaded_file.type
                if not mime_type:
                    if uploaded_file.name.endswith('.pdf'):
                        mime_type = 'application/pdf'
                    elif uploaded_file.name.endswith('.docx'):
                        mime_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                
                # Gemini API 호출
                return self.call_gemini_api(file_content, mime_type)
            except Exception as e:
                print(f"Error processing document: {e}")
                return self._get_sample_data()
        else:
            # API 키가 없으면 샘플 데이터 반환
            return self._get_sample_data()
    
    def _get_sample_data(self):
        """샘플 데이터 반환 (데모용)"""
        return {
            "request_info": {
                "client": "Sample Client",
                "project": "Blower Motor Test Project"
            },
            "test_items": [
                {
                    "test_name": "High Temperature Test",
                    "category": "Environmental Tests",
                    "ref_standard": "ISO 16750-4",
                    "sample_assembly": "Motor only",
                    "test_sample_no": "S001",
                    "sample_count": "3",
                    "test_duration": "5",
                    "test_instrument": "Temperature Chamber",
                    "test_master_id": "M001",
                    "custom_specs": {
                        "temperature": "85°C",
                        "duration": "1000 hours",
                        "voltage": "12V"
                    }
                },
                {
                    "test_name": "Low Temperature Test",
                    "category": "Environmental Tests",
                    "ref_standard": "ISO 16750-4",
                    "sample_assembly": "Motor only",
                    "test_sample_no": "S002",
                    "sample_count": "3",
                    "test_duration": "5",
                    "test_instrument": "Temperature Chamber",
                    "test_master_id": "M002",
                    "custom_specs": {
                        "temperature": "-40°C",
                        "duration": "1000 hours",
                        "voltage": "12V"
                    }
                },
                {
                    "test_name": "Vibration Test",
                    "category": "Mechanical Tests",
                    "ref_standard": "ISO 16750-3",
                    "sample_assembly": "HVAC",
                    "test_sample_no": "S003",
                    "sample_count": "2",
                    "test_duration": "3",
                    "test_instrument": "Vibration Shaker",
                    "test_master_id": "M003",
                    "custom_specs": {
                        "frequency": "10-2000 Hz",
                        "acceleration": "10G",
                        "duration": "8 hours"
                    }
                }
            ]
        }
    
    def call_gemini_api(self, file_content, mime_type):
        """
        Gemini API 호출 (실제 구현)
        """
        try:
            # 파일을 base64로 인코딩
            file_base64 = base64.b64encode(file_content).decode('utf-8')
            
            # 마스터 데이터 가져오기
            master_tests = self.db.get_master_tests()
            master_json = master_tests.to_json(orient='records', force_ascii=False)
            
            # 프롬프트 구성
            prompt = self.get_extraction_prompt(master_json)
            
            # API 호출
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={self.api_key}"
            
            payload = {
                "contents": [{
                    "role": "user",
                    "parts": [
                        {"text": prompt},
                        {"inline_data": {
                            "mime_type": mime_type,
                            "data": file_base64
                        }}
                    ]
                }],
                "generationConfig": {
                    "temperature": 0.1,
                    "maxOutputTokens": 8192
                }
            }
            
            headers = {
                "Content-Type": "application/json"
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            
            # JSON 추출
            extracted_json = self.extract_json_from_response(result)
            return extracted_json if extracted_json else self._get_sample_data()
            
        except Exception as e:
            print(f"Error calling Gemini API: {e}")
            return self._get_sample_data()
    
    def get_extraction_prompt(self, master_json):
        """추출 프롬프트 생성"""
        prompt = f"""
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
        "other_conditions 1": "기타 특이사항1",
        "other_conditions 2": "기타 특이사항2"
      }}
    }}
  ]
}}

# test_master (표준 시험 규격 정의) (JSON)
{master_json}
"""
        return prompt
    
    def extract_json_from_response(self, response):
        """API 응답에서 JSON 추출"""
        try:
            # Gemini API 응답 구조
            text = response['candidates'][0]['content']['parts'][0]['text']
            
            # JSON 코드 블록 제거
            if '```json' in text:
                text = text.split('```json')[1].split('```')[0]
            elif '```' in text:
                text = text.split('```')[1].split('```')[0]
            
            # JSON 파싱
            text = text.strip()
            return json.loads(text)
            
        except Exception as e:
            print(f"Error extracting JSON: {e}")
            print(f"Response: {response}")
            return None
