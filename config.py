import os

# Gemini API 설정
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-2.0-flash-exp"
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"

# 데이터베이스 파일 경로
DB_PATH = "database"
USER_LIST_FILE = f"{DB_PATH}/User_List.csv"
MASTER_TEST_FILE = f"{DB_PATH}/Master_Test.csv"
REQUEST_INFO_FILE = f"{DB_PATH}/Request_Info.csv"
TEST_ITEM_FILE = f"{DB_PATH}/Test_Item.csv"
SCHEDULE_ITEM_FILE = f"{DB_PATH}/Schedule_Item.csv"

# 기본 설정
DEFAULT_SAMPLE_COUNT = 3
DEFAULT_TEST_DURATION = 1
MAX_PARALLEL_TESTS = 2
