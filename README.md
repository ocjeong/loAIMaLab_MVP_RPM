# RPM - Reliable Planning Manager

블로워 모터 테스트 지원 시스템

## 🚀 기능

- 📄 테스트 스펙 문서 자동 파싱 (PDF, DOCX)
- 🤖 LLM 기반 지능형 시험 항목 추출
- 📊 시험 계획서 자동 생성
- 📅 Gantt Chart 기반 일정 관리
- 💾 Excel 계획서 내보내기

## 📦 설치 방법

```bash
pip install -r requirements.txt
```

## ▶️ 실행 방법
```BASH
streamlit run app.py
```

## 📁 프로젝트 구조
```
rpm-app/
├── app.py
├── requirements.txt
├── database.py
├── llm_processor.py
├── utils.py
└── README.md
```
## 🌐 배포
Streamlit Community Cloud에 배포 가능합니다.

GitHub에 코드 업로드
https://share.streamlit.io 접속
Repository 연결 및 배포


## 📝 라이선스
MIT License


## 🎯 배포 방법

### Streamlit Community Cloud 배포 단계:

1. **GitHub Repository 생성**
   - 위 파일들을 GitHub 저장소에 업로드

2. **Streamlit Cloud 접속**
   - https://share.streamlit.io 접속
   - GitHub 계정으로 로그인

3. **앱 배포**
   - "New app" 클릭
   - Repository, Branch, Main file (app.py) 선택
   - "Deploy" 클릭

4. **환경 변수 설정 (선택사항)**
   - Advanced settings에서 API 키 등 환경변수 설정 가능

## 📌 주요 특징

✅ **완전한 Streamlit 기반 구현**\
✅ **JSON 기반 간단한 데이터 저장** (SQLite로 전환 가능)\
✅ **LLM 연동 준비 완료** (OpenAI API 등)\
✅ **Gantt Chart 시각화**\
✅ **Excel 내보내기 기능**\
✅ **사용자별 데이터 관리**\
✅ **반응형 UI 디자인**\

이 코드는 바로 Streamlit Community Cloud에 배포 가능하며, 실제 LLM API를 연동하려면 `llm_processor.py`의 주석 처리된 부분을 활성화하고 API 키를 환경변수로 설정하면 됩니다!
