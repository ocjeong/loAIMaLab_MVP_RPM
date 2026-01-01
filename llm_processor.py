import base64
from typing import List, Dict, Any
import random

class LLMProcessor:
    """LLM 기반 문서 파싱 및 데이터 추출 (실제 배포 시 OpenAI API 등 연동)"""
    
    def __init__(self):
        self.api_key = None  # 실제 사용 시 환경변수에서 로드
    
    def parse_document(self, uploaded_file) -> List[Dict]:
        """
        문서 파싱 및 시험 항목 추출
        실제 구현 시 OpenAI API, Anthropic Claude API 등을 사용
        """
        # 데모용 샘플 데이터 반환
        sample_data = [
            {
                "test_name": "On & Off Endurance Test",
                "category": "Endurance Test",
                "temperature": "25°C ± 5°C",
                "voltage": "12V DC",
                "cycles": 18000,
                "duration_hours": 600,
                "standard_id": "M001",
                "notes": "1분 ON / 1분 OFF 사이클"
            },
            {
                "test_name": "Low Voltage Operation Test",
                "category": "Electrical Test",
                "temperature": "25°C",
                "voltage": "9V DC",
                "cycles": 100,
                "duration_hours": 2,
                "standard_id": "M002",
                "notes": "정상 작동 확인"
            },
            {
                "test_name": "High Voltage Operation Test",
                "category": "Electrical Test",
                "temperature": "25°C",
                "voltage": "16V DC",
                "cycles": 100,
                "duration_hours": 2,
                "standard_id": "M003",
                "notes": "정상 작동 확인"
            },
            {
                "test_name": "Temperature Cycling Test",
                "category": "Environmental Test",
                "temperature": "-40°C to +85°C",
                "voltage": "12V DC",
                "cycles": 500,
                "duration_hours": 250,
                "standard_id": "M004",
                "notes": "30분 간격 온도 변화"
            }
        ]
        
        # 실제 구현 예시 (주석 처리)
        """
        import openai
        
        # 파일을 base64로 인코딩
        file_content = base64.b64encode(uploaded_file.read()).decode('utf-8')
        
        # OpenAI API 호출
        response = openai.ChatCompletion.create(
            model="gpt-4-vision-preview",
            messages=[
                {
                    "role": "system",
                    "content": "당신은 블로워 모터 테스트 스펙 문서를 분석하는 전문가입니다."
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": '''
                            다음 테스트 스펙 문서에서 시험 항목을 추출하고 JSON 형태로 반환하세요.
                            각 항목은 다음 필드를 포함해야 합니다:
                            - test_name: 시험명
                            - category: 시험 분류
                            - temperature: 온도 조건
                            - voltage: 전압 조건
                            - cycles: 사이클 수
                            - duration_hours: 예상 소요 시간
                            - standard_id: 매칭된 마스터 데이터 ID
                            - notes: 비고
                            '''
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{file_content}"
                            }
                        }
                    ]
                }
            ]
        )
        
        # JSON 파싱
        extracted_data = json.loads(response.choices[0].message.content)
        return extracted_data
        """
        
        return sample_data
    
    def match_master_data(self, test_name: str, master_data: List[Dict]) -> str:
        """
        시험명을 마스터 데이터와 매칭
        실제 구현 시 임베딩 기반 유사도 검색 사용
        """
        # 간단한 키워드 매칭 (데모용)
        test_name_lower = test_name.lower()
        
        for master in master_data:
            for alias in master['aliases']:
                if alias.lower() in test_name_lower:
                    return master['id']
        
        return ""
