import google.generativeai as genai
import streamlit as st
import json
import time
import base64
from typing import Dict, List

def configure_api():
    """Gemini API 설정"""
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=api_key)
    except Exception as e:
        st.error(f"API 키 설정 실패: {str(e)}")
        st.stop()

def get_extraction_prompt(master_data_list: List[Dict]) -> str:
    """마스터 데이터를 포함한 프롬프트 생성"""
    
    base_prompt = """
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
  "request_info": { 
    "client": "발주처명", 
    "project": "프로젝트명" 
  },
  "test_items": [
    {
      "test_name": "표준 시험명",
      "category": "분류",
      "ref_standard": "참조 규격",
      "sample_assembly": "시료 구성",
      "test_sample_no": 1,
      "sample_count": 3,
      "test_duration": 5.0,
      "test_equipment": "시험 장비",
      "test_master_id": "매핑된 마스터 ID",
      "custom_specs": {
        "temperature": "온도 조건",
        "voltage": "전압 조건",
        "other_conditions": "기타 조건"
      }
    }
  ]
}

# test_master (표준 시험 규격 정의)
"""
    
    # 마스터 데이터를 JSON 문자열로 변환하여 추가
    master_json = json.dumps(master_data_list, ensure_ascii=False, indent=2)
    
    return base_prompt + "\n" + master_json + "\n\n문서를 분석하여 위 형식에 맞게 JSON을 출력하세요."

def call_gemini_with_retry(prompt: str, file_data, max_retries: int = 3) -> str:
    """재시도 로직이 포함된 Gemini API 호출"""
    
    configure_api()
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    for attempt in range(max_retries):
        try:
            response = model.generate_content([prompt, file_data])
            return response.text
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # 지수 백오프
                st.warning(f"⚠️ API 호출 실패. {wait_time}초 후 재시도... ({attempt+1}/{max_retries})")
                time.sleep(wait_time)
            else:
                st.error(f"❌ API 호출 최종 실패: {str(e)}")
                raise

def extract_test_data(file_bytes: bytes, file_type: str, master_data: List[Dict]) -> Dict:
    """파일에서 시험 데이터 추출"""
    
    # 프롬프트 구성
    prompt = get_extraction_prompt(master_data)
    
    # 파일 크기 확인 (15MB 기준)
    file_size_mb = len(file_bytes) / (1024 * 1024)
    
    if file_size_mb > 15:
        # 파일 API 사용
        st.info("📤 대용량 파일 업로드 중...")
        uploaded_file = genai.upload_file(file_bytes, mime_type=file_type)
        file_part = {
            "file_data": {
                "file_uri": uploaded_file.uri,
                "mime_type": file_type
            }
        }
    else:
        # Base64 인라인 데이터
        encoded = base64.b64encode(file_bytes).decode('utf-8')
        file_part = {
            "inline_data": {
                "mime_type": file_type,
                "data": encoded
            }
        }
    
    # API 호출
    with st.spinner("🤖 AI가 문서를 분석하고 있습니다..."):
        response_text = call_gemini_with_retry(prompt, file_part)
    
    # JSON 파싱
    try:
        # 코드 블록 제거 (```json ... ``` 형식)
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]
        
        result = json.loads(response_text.strip())
        return result
    except json.JSONDecodeError as e:
        st.error(f"❌ JSON 파싱 실패: {str(e)}")
        st.code(response_text)
        st.stop()

def match_to_master(test_name: str, master_data: List[Dict]) -> str:
    """시험명을 마스터 데이터와 매칭"""
    
    # 간단한 유사도 매칭 (실제로는 LLM 기반 매칭 가능)
    test_name_lower = test_name.lower()
    
    best_match = None
    best_score = 0
    
    for master in master_data:
        # std_name 매칭
        if test_name_lower in master['std_name'].lower() or master['std_name'].lower() in test_name_lower:
            score = 0.9
            if score > best_score:
                best_score = score
                best_match = master['id']
        
        # aliases 매칭
        for alias in master.get('aliases', []):
            if test_name_lower in alias.lower() or alias.lower() in test_name_lower:
                score = 0.85
                if score > best_score:
                    best_score = score
                    best_match = master['id']
    
    # 임계값 0.7 이상만 반환
    if best_score >= 0.7:
        return best_match
    
    return ""
