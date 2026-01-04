# RPM - Reliable Planning Manager

차량용 블로워 모터 시험 규격 자동 파싱 및 계획 관리 시스템

## 🚀 배포 방법

### Streamlit Community Cloud 배포

1. GitHub 저장소 생성 및 코드 푸시
2. [Streamlit Community Cloud](https://streamlit.io/cloud) 접속
3. "New app" 클릭
4. 저장소 선택 및 `app.py` 지정
5. Secrets 설정 (GEMINI_API_KEY 추가)
6. Deploy 클릭

### Secrets 설정

Streamlit Cloud의 Settings > Secrets에 다음 추가:

```toml
GEMINI_API_KEY = "your-gemini-api-key-here"
```

## 📦 로컬 실행

```BASH
코드 복사
# 패키지 설치
pip install -r requirements.txt

# 앱 실행
streamlit run app.py
```

## 🔑 환경 변수
- GEMINI_API_KEY: Google Gemini API 키 (필수)

## 📁 프로젝트 구조
```
rpm-app/
├── app.py
├── requirements.txt
├── .streamlit/
│   └── config.toml
├── modules/
│   ├── __init__.py
│   ├── document_parser.py
│   ├── data_manager.py
│   ├── llm_processor.py
│   └── scheduler.py
├── utils/
│   ├── __init__.py
│   └── helpers.py
└── data/
    ├── Master_Test.csv
    ├── Request_Info.csv
    ├── Test_Item.csv
    └── User_List.csv
```
- app.py: 메인 애플리케이션
- modules/: 핵심 모듈
- data_manager.py: 데이터 관리
- document_parser.py: 문서 파싱
- llm_processor.py: LLM 처리
- scheduler.py: 일정 관리
- utils/: 유틸리티 함수
- data/: CSV 데이터 저장소


## 🎯 배포 체크리스트

1. ✅ GitHub 저장소 생성
2. ✅ 모든 파일 커밋 및 푸시
3. ✅ Streamlit Cloud에서 앱 생성
4. ✅ GEMINI_API_KEY Secrets 설정
5. ✅ 앱 배포 및 테스트

이 코드는 Streamlit Community Cloud에 바로 배포 가능하도록 구성되었습니다. Gemini API 키만 설정하면 완전히 동작합니다!
코드 복사

