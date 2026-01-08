```
rpm_app/
├── app.py                 # 메인 애플리케이션
├── requirements.txt       # 패키지 의존성
├── .streamlit/
│   └── config.toml       # Streamlit 설정
├── modules/
│   ├── __init__.py
│   ├── database.py       # 데이터베이스 관리
│   ├── llm_handler.py    # LLM API 처리
│   ├── standardization.py # 표준화 로직
│   ├── planning.py       # 계획서 생성
│   └── scheduling.py     # 일정 관리
├── data/
│   ├── User_List.csv
│   ├── Master_Test.csv
│   ├── Request_Info.csv
│   ├── Test_Item.csv
│   └── Schedule_Item.csv
└── utils/
    ├── __init__.py
    └── helpers.py        # 유틸리티 함수
```
