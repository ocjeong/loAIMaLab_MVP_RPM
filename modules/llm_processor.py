import google.generativeai as genai
import json
import os

class LLMProcessor:
    """LLM 처리 클래스"""
    
    def __init__(self, data_manager):
        self.data_manager = data_manager
        self.setup_gemini()
    
    def setup_gemini(self):
        """Gemini API 설정"""
        # API 키는 환경 변수 또는 Streamlit secrets에서 가져오기
        api_key = os.getenv('GEMINI_API_KEY', '')
        if not api_key:
            try:
                import streamlit as st
                api_key = st.secrets.get('GEMINI_API_KEY', '')
            except:
                pass
        
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        else:
            self.model = None
    
    def get_extraction_prompt(self):
        """데이터 추출 프롬프트 생성"""
        # 마스터 데이터 로드
        master_df = self.data_manager.load_master_test_data()
        master_json = master_df.to_dict('records')
        
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
      "test_name": "표준 시험명",
      "category": "분류",
      "ref_standard": "참조 규격",
      "sample_assembly": "시험 시료의 부품 구성",
      "test_sample_no": "시험에 사용되는 샘플 번호",
      "sample_count": "시료 수",
      "test_duration": "단일 시험 항목에 필요한 일수",
      "test_equipment": "시험 기기 이름",
      "test_master_id": "매핑 된 시험 마스터 데이터 ID",
      "custom_specs": {{
        "temperature": "온도 조건",
        "voltage": "전압 조건",
        "other_conditions": "기타 특이사항"
      }}
    }}
  ]
}}

# test_master (표준 시험 규격 정의) (JSON)
{json.dumps(master_json, ensure_ascii=False, indent=2)}
"""
        return prompt
    
    def extract_test_data(self, file_content, file_type):
        """시험 데이터 추출"""
        if not self.model:
            # API 키가 없는 경우 샘플 데이터 반환
            return self.get_sample_data()
        
        try:
            # 파일을 Base64로 인코딩
            import base64
            file_base64 = base64.b64encode(file_content).decode('utf-8')
            
            # MIME 타입 결정
            mime_type = "application/pdf" if "pdf" in file_type else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            
            # 프롬프트 생성
            prompt = self.get_extraction_prompt()
            
            # Gemini API 호출
            response = self.model.generate_content([
                prompt,
                {
                    "mime_type": mime_type,
                    "data": file_base64
                }
            ])
            
            # JSON 파싱
            result_text = response.text.strip()
            
            # JSON 코드 블록 제거
            if result_text.startswith("```json"):
                result_text = result_text[7:]
            if result_text.startswith("```"):
                result_text = result_text[3:]
            if result_text.endswith("```"):
                result_text = result_text[:-3]
            
            result_text = result_text.strip()
            
            data = json.loads(result_text)
            return data
            
        except Exception as e:
            print(f"Error extracting data: {e}")
            # 에러 발생 시 샘플 데이터 반환
            return self.get_sample_data()
    
    def get_sample_data(self):
        """샘플 데이터 반환 (테스트용)"""
        return {
            "request_info": {
                "client": "샘플 발주처",
                "project": "테스트 프로젝트"
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
                        "duration": "1000hr"
                    }
                },
                {
                    "test_name": "Vibration Test",
                    "category": "Mechanical Test",
                    "ref_standard": "ISO 16750-3",
                    "sample_assembly": "HVAC",
                    "test_sample_no": "S002",
                    "sample_count": "2",
                    "test_duration": "3",
                    "test_equipment": "Vibration Shaker",
                    "test_master_id": "M004",
                    "custom_specs": {
                        "frequency": "10-2000 Hz",
                        "amplitude": "10g"
                    }
                }
            ]
        }
