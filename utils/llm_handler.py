import requests
import base64
import json
import os
from io import BytesIO
import PyPDF2
from docx import Document

class LLMHandler:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.api_key = os.getenv('GEMINI_API_KEY', '')  # 환경 변수에서 API 키 로드
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={self.api_key}"
    
    def extract_test_data(self, uploaded_file):
        """업로드된 파일에서 시험 데이터 추출"""
        try:
            # 파일을 Base64로 인코딩
            file_content = uploaded_file.read()
            base64_content = base64.b64encode(file_content).decode('utf-8')
            
            # MIME 타입 결정
            if uploaded_file.name.endswith('.pdf'):
                mime_type = 'application/pdf'
            elif uploaded_file.name.endswith('.docx'):
                mime_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            else:
                return None
            
            # 마스터 데이터 로드
            master_df = self.db_manager.load_master_data()
            master_data = master_df.to_dict('records')
            
            # 프롬프트 생성
            prompt = self._create_extraction_prompt(master_data)
            
            # API 호출
            payload = {
                "contents": [
                    {
                        "role": "user",
                        "parts": [
                            {"text": prompt},
                            {
                                "inline_data": {
                                    "mime_type": mime_type,
                                    "data": base64_content
                                }
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.1,
                    "topK": 32,
                    "topP": 1,
                    "maxOutputTokens": 8192,
                }
            }
            
            # API 키가 없으면 더미 데이터 반환
            if not self.api_key:
                return self._get_dummy_data()
            
            response = requests.post(self.api_url, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                
                # 응답에서 JSON 추출
                text_response = result['candidates'][0]['content']['parts'][0]['text']
                
                # JSON 파싱
                # 코드 블록 제거
                if '```json' in text_response:
                    text_response = text_response.split('```json')[1].split('```')[0]
                elif '```' in text_response:
                    text_response = text_response.split('```')[1].split('```')[0]
                
                extracted_data = json.loads(text_response.strip())
                
                return extracted_data
            else:
                print(f"API Error: {response.status_code}")
                return self._get_dummy_data()
        
        except Exception as e:
            print(f"Extraction Error: {str(e)}")
            return self._get_dummy_data()
    
    def _create_extraction_prompt(self, master_data):
        """시험 규격 데이터 추출 프롬프트 생성"""
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

문서를 분석하고 위 형식에 맞춰 JSON만 출력하세요."""

        return prompt
    
    def _get_dummy_data(self):
        """API 키가 없거나 오류 발생 시 더미 데이터 반환"""
        return {
            "request_info": {
                "client": "샘플 발주처",
                "project": "블로워 모터 시험 프로젝트"
            },
            "test_items": [
                {
                    "test_name": "고온 시험",
                    "category": "환경 시험",
                    "ref_standard": "ISO 16750-4",
                    "sample_assembly": "Motor only",
                    "test_sample_no": "S001",
                    "sample_count": "3",
                    "test_duration": "7",
                    "test_equipment": "항온항습기",
                    "test_master_id": "M002",
                    "custom_specs": {
                        "temperature": "85°C",
                        "duration": "1000시간"
                    }
                },
                {
                    "test_name": "저온 시험",
                    "category": "환경 시험",
                    "ref_standard": "ISO 16750-4",
                    "sample_assembly": "Motor only",
                    "test_sample_no": "S002",
                    "sample_count": "3",
                    "test_duration": "5",
                    "test_equipment": "저온 챔버",
                    "test_master_id": "M003",
                    "custom_specs": {
                        "temperature": "-40°C",
                        "duration": "500시간"
                    }
                },
                {
                    "test_name": "진동 시험",
                    "category": "환경 시험",
                    "ref_standard": "ISO 16750-3",
                    "sample_assembly": "HVAC",
                    "test_sample_no": "S003",
                    "sample_count": "2",
                    "test_duration": "3",
                    "test_equipment": "진동 시험기",
                    "test_master_id": "M005",
                    "custom_specs": {
                        "frequency_range": "10-2000Hz",
                        "acceleration": "10G"
                    }
                }
            ]
        }
