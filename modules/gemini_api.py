import requests
import base64
import json
import os

class GeminiAPI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent"
    
    def parse_document(self, file_content, file_type, master_data):
        """문서 파싱 및 데이터 추출"""
        
        # Base64 인코딩
        base64_content = base64.b64encode(file_content).decode('utf-8')
        
        # MIME 타입 설정
        mime_type = 'application/pdf' if file_type == 'pdf' else 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        
        # 프롬프트 생성
        prompt = self._create_prompt(master_data)
        
        # API 요청
        payload = {
            "contents": [{
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
            }],
            "generationConfig": {
                "temperature": 0.1,
                "topK": 32,
                "topP": 1,
                "maxOutputTokens": 8192,
            }
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}?key={self.api_key}",
                headers=headers,
                json=payload,
                timeout=60
            )
            
            response.raise_for_status()
            result = response.json()
            
            # 응답 파싱
            if 'candidates' in result and len(result['candidates']) > 0:
                text = result['candidates'][0]['content']['parts'][0]['text']
                
                # JSON 추출
                json_start = text.find('{')
                json_end = text.rfind('}') + 1
                
                if json_start != -1 and json_end > json_start:
                    json_str = text[json_start:json_end]
                    extracted_data = json.loads(json_str)
                    return extracted_data
                else:
                    raise ValueError("JSON 데이터를 찾을 수 없습니다.")
            else:
                raise ValueError("API 응답에 결과가 없습니다.")
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"API 요청 실패: {str(e)}")
        except json.JSONDecodeError as e:
            raise Exception(f"JSON 파싱 실패: {str(e)}")
    
    def _create_prompt(self, master_data):
        """프롬프트 생성"""
        
        # 마스터 데이터를 JSON 문자열로 변환
        master_json = master_data.to_json(orient='records', force_ascii=False)
        
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
"""
        
        return prompt
