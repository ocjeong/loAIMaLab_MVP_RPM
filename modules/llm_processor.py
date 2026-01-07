import google.generativeai as genai
import base64
import json
import os
from io import BytesIO
import PyPDF2
from docx import Document
# 기존 LLMProcessor 클래스에 메서드 추가

class LLMProcessor:
    def __init__(self, db):
        self.db = db
        # Gemini API 키 설정 (환경 변수에서 가져오기)
        api_key = os.getenv('GEMINI_API_KEY', '')
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
        else:
            self.model = None
    
    def process_document(self, uploaded_file):
        """문서 처리 및 데이터 추출"""
        try:
            # 파일 읽기
            file_content = uploaded_file.read()
            file_type = uploaded_file.type
            
            return self.process_document_from_bytes(file_content, file_type)
            
        except Exception as e:
            print(f"Error processing document: {e}")
            return None
    
    def process_document_from_bytes(self, file_content, file_type):
        """바이트 데이터로부터 문서 처리 및 데이터 추출 (새로 추가)"""
        try:
            # 텍스트 추출
            if 'pdf' in file_type:
                text = self._extract_text_from_pdf(file_content)
            elif 'docx' in file_type or 'word' in file_type:
                text = self._extract_text_from_docx(file_content)
            else:
                return None
            
            # LLM으로 데이터 추출
            if self.model:
                extracted_data = self._extract_with_llm(text)
            else:
                # API 키가 없는 경우 샘플 데이터 반환
                extracted_data = self._get_sample_data()
            
            return extracted_data
            
        except Exception as e:
            print(f"Error processing document from bytes: {e}")
            return None
    
    # 나머지 메서드들은 동일...

    
    def _extract_text_from_pdf(self, file_content):
        """PDF에서 텍스트 추출"""
        pdf_file = BytesIO(file_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    
    def _extract_text_from_docx(self, file_content):
        """DOCX에서 텍스트 추출"""
        doc = Document(BytesIO(file_content))
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    
    def _extract_with_llm(self, text):
        """LLM을 사용한 데이터 추출"""
        # 마스터 데이터 가져오기
        master_data = self.db.master_test_df.to_dict('records')
        
        # 프롬프트 생성
        prompt = self._create_extraction_prompt(master_data)
        
        try:
            # Gemini API 호출
            response = self.model.generate_content([prompt, text])
            
            # JSON 파싱
            response_text = response.text
            # JSON 부분만 추출
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            json_text = response_text[start_idx:end_idx]
            
            extracted_data = json.loads(json_text)
            return extracted_data
            
        except Exception as e:
            print(f"LLM extraction error: {e}")
            return self._get_sample_data()
    
    def _create_extraction_prompt(self, master_data):
        """데이터 추출 프롬프트 생성"""
        prompt = """# Role
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
      "test_name": "표준 시험명",
      "category": "분류",
      "ref_standard": "참조 규격",
      "sample_assembly": "시료 구성",
      "test_sample_no": "샘플 번호",
      "sample_count": "시료 수",
      "test_duration": "시험 기간(days)",
      "test_equipment": "시험 기기",
      "test_master_id": "매핑된 마스터 ID",
      "custom_specs": {}
    }
  ]
}

# test_master (표준 시험 규격 정의)
"""
        prompt += json.dumps(master_data, indent=2, ensure_ascii=False)
        
        return prompt
    
    def _get_sample_data(self):
        """샘플 데이터 반환 (API 키가 없을 때)"""
        return {
            "request_info": {
                "client": "샘플 발주처",
                "project": "샘플 프로젝트"
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
                        "frequency": "10-2000Hz",
                        "acceleration": "10G"
                    }
                },
                {
                    "test_name": "Noise Test",
                    "category": "Acoustic Test",
                    "ref_standard": "",
                    "sample_assembly": "Motor only",
                    "test_sample_no": "S003",
                    "sample_count": "3",
                    "test_duration": "2",
                    "test_equipment": "Sound Level Meter",
                    "test_master_id": "M005",
                    "custom_specs": {
                        "max_noise_level": "60dB"
                    }
                }
            ]
        }
