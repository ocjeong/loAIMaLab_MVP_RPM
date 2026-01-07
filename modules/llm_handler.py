import os
import base64
import json
import requests
from typing import Dict, List, Any


class LLMHandler:
    """LLM API 핸들러 클래스"""
    
    def __init__(self):
        # Gemini API 키 (환경 변수에서 가져오기)
        self.api_key = os.getenv('GEMINI_API_KEY', '')
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent"
        
    def extract_from_document(self, uploaded_file) -> Dict[str, Any]:
        """
        업로드된 문서에서 시험 규격 데이터 추출
        
        Args:
            uploaded_file: Streamlit UploadedFile 객체
            
        Returns:
            추출된 데이터 딕셔너리
        """
        try:
            # 파일을 Base64로 인코딩
            file_bytes = uploaded_file.read()
            base64_data = base64.b64encode(file_bytes).decode('utf-8')
            
            # MIME 타입 결정
            if uploaded_file.name.endswith('.pdf'):
                mime_type = 'application/pdf'
            elif uploaded_file.name.endswith('.docx'):
                mime_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            else:
                mime_type = 'application/octet-stream'
            
            # 프롬프트 생성
            prompt = self._get_extraction_prompt()
            
            # API 호출
            if self.api_key:
                response = self._call_gemini_api(prompt, base64_data, mime_type)
                
                if response:
                    return self._parse_response(response)
            
            # API 키가 없거나 실패 시 더미 데이터 반환
            print(f"API 키가 없거나 실패: 데이터 반환")
            return self._get_dummy_data()
            
        except Exception as e:
            print(f"문서 추출 오류: {e}")
            return self._get_dummy_data()
    
    def _get_extraction_prompt(self) -> str:
        """시험 규격 데이터 추출 프롬프트"""
        return """# Role
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
      "test_equipment": "시험 기기 이름",
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
    "aliases": ["작동성 시험", "온오프", "On/Off"]
  },
  {
    "id": "M002",
    "std_name": "High Temperature Test",
    "std_category": "Environmental Test",
    "ref_standard": "ISO 16750-4",
    "aliases": ["고온 시험", "고온 내구", "High Temp"]
  },
  {
    "id": "M003",
    "std_name": "Low Temperature Test",
    "std_category": "Environmental Test",
    "ref_standard": "ISO 16750-4",
    "aliases": ["저온 시험", "저온 내구", "Low Temp"]
  },
  {
    "id": "M004",
    "std_name": "Noise Test",
    "std_category": "Performance Test",
    "ref_standard": "",
    "aliases": ["소음 시험", "노이즈", "Sound"]
  },
  {
    "id": "M005",
    "std_name": "Random Vibration Test",
    "std_category": "Mechanical Test",
    "ref_standard": "ISO 16750-3",
    "aliases": ["진동 시험", "Vibration"]
  },
  {
    "id": "M006",
    "std_name": "Dust Protection Test",
    "std_category": "Environmental Test",
    "ref_standard": "ISO 20653",
    "aliases": ["분진 시험", "Dust"]
  },
  {
    "id": "M007",
    "std_name": "Water Protection Test",
    "std_category": "Environmental Test",
    "ref_standard": "ISO 20653",
    "aliases": ["방수 시험", "Water"]
  },
  {
    "id": "M008",
    "std_name": "EMC Test",
    "std_category": "Electrical Tests",
    "ref_standard": "ISO 11452",
    "aliases": ["전자파 적합성", "EMI/EMC"]
  },
  {
    "id": "M009",
    "std_name": "Undervoltage and Overvoltage Test",
    "std_category": "Electrical Tests",
    "ref_standard": "ISO 16750-3",
    "aliases": ["과저전압", "정지 전압 확인", "Under/Over Voltage"]
  }
]

문서를 분석하고 위 형식에 맞춰 JSON만 출력해줘."""
    
    def _call_gemini_api(self, prompt: str, base64_data: str, mime_type: str) -> str:
        """Gemini API 호출"""
        try:
            headers = {
                'Content-Type': 'application/json'
            }
            
            payload = {
                "contents": [
                    {
                        "role": "user",
                        "parts": [
                            {"text": prompt},
                            {
                                "inline_data": {
                                    "mime_type": mime_type,
                                    "data": base64_data
                                }
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.2,
                    "topK": 40,
                    "topP": 0.95,
                    "maxOutputTokens": 8192,
                }
            }
            
            response = requests.post(
                f"{self.api_url}?key={self.api_key}",
                headers=headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if 'candidates' in result and len(result['candidates']) > 0:
                    text = result['candidates'][0]['content']['parts'][0]['text']
                    return text
            
            return None
            
        except Exception as e:
            print(f"API 호출 오류: {e}")
            return None
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """API 응답 파싱"""
        try:
            # JSON 코드 블록 제거
            response = response.strip()
            if response.startswith('```json'):
                response = response[7:]
            if response.startswith('```'):
                response = response[3:]
            if response.endswith('```'):
                response = response[:-3]
            
            response = response.strip()
            
            # JSON 파싱
            data = json.loads(response)
            return data
            
        except Exception as e:
            print(f"응답 파싱 오류: {e}")
            return self._get_dummy_data()
    
    def _get_dummy_data(self) -> Dict[str, Any]:
        """더미 데이터 반환 (테스트용)"""
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
                    "test_equipment": "Temperature Chamber",
                    "test_master_id": "M002",
                    "custom_specs": {
                        "temperature": "85°C",
                        "voltage": "12V",
                        "duration": "1000hr"
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
                    "test_equipment": "Temperature Chamber",
                    "test_master_id": "M003",
                    "custom_specs": {
                        "temperature": "-40°C",
                        "voltage": "12V",
                        "duration": "500hr"
                    }
                },
                {
                    "test_name": "Random Vibration Test",
                    "category": "Mechanical Test",
                    "ref_standard": "ISO 16750-3",
                    "sample_assembly": "HVAC",
                    "test_sample_no": "S003",
                    "sample_count": "3",
                    "test_duration": "3",
                    "test_equipment": "Vibration Shaker",
                    "test_master_id": "M005",
                    "custom_specs": {
                        "frequency": "10-500Hz",
                        "acceleration": "5g RMS"
                    }
                },
                {
                    "test_name": "Undervoltage and Overvoltage Test",
                    "category": "Electrical Tests",
                    "ref_standard": "ISO 16750-3",
                    "sample_assembly": "Motor only",
                    "test_sample_no": "S004",
                    "sample_count": "3",
                    "test_duration": "2",
                    "test_equipment": "Power Supply",
                    "test_master_id": "M009",
                    "custom_specs": {
                        "undervoltage": "9V",
                        "overvoltage": "16V",
                        "duration": "1min each"
                    }
                }
            ]
        }
