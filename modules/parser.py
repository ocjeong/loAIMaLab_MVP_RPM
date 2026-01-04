from .gemini_api import GeminiAPI
from .database import DatabaseManager
import PyPDF2
from docx import Document
import io

class DocumentParser:
    def __init__(self, api_key):
        self.gemini = GeminiAPI(api_key)
        self.db = DatabaseManager()
    
    def parse_document(self, uploaded_file):
        """문서 파싱 메인 함수"""
        
        # 파일 타입 확인
        file_type = uploaded_file.name.split('.')[-1].lower()
        
        # 파일 내용 읽기
        file_content = uploaded_file.read()
        
        # 마스터 데이터 로드
        master_data = self.db.get_master_tests()
        
        # Gemini API로 파싱
        extracted_data = self.gemini.parse_document(
            file_content,
            file_type,
            master_data
        )
        
        return extracted_data
    
    def extract_text_from_pdf(self, file_content):
        """PDF에서 텍스트 추출 (fallback용)"""
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    
    def extract_text_from_docx(self, file_content):
        """DOCX에서 텍스트 추출 (fallback용)"""
        doc = Document(io.BytesIO(file_content))
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
