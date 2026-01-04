import base64
from PyPDF2 import PdfReader
from docx import Document
import io

class DocumentParser:
    """문서 파싱 클래스"""
    
    def parse_pdf(self, file_content):
        """PDF 파일 파싱"""
        try:
            pdf_reader = PdfReader(io.BytesIO(file_content))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
            return text
        except Exception as e:
            print(f"Error parsing PDF: {e}")
            return None
    
    def parse_docx(self, file_content):
        """DOCX 파일 파싱"""
        try:
            doc = Document(io.BytesIO(file_content))
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except Exception as e:
            print(f"Error parsing DOCX: {e}")
            return None
    
    def encode_to_base64(self, file_content):
        """Base64 인코딩"""
        return base64.b64encode(file_content).decode('utf-8')
