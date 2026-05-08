"""
PDF Extractor Module
Extracts text content from PDF files.
"""

import PyPDF2
import pdfplumber
from typing import Optional, List
import io


class PDFExtractor:
    """PDF extractor for extracting text from PDF files."""
    
    def __init__(self, use_pdfplumber: bool = True):
        """
        Initialize PDF extractor.
        
        Args:
            use_pdfplumber: If True, use pdfplumber (better for tables), 
                          otherwise use PyPDF2
        """
        self.use_pdfplumber = use_pdfplumber
    
    def extract_text_from_file(self, file_path: str) -> str:
        """
        Extract text from PDF file.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Extracted text content
        """
        if self.use_pdfplumber:
            return self._extract_with_pdfplumber(file_path)
        else:
            return self._extract_with_pypdf2(file_path)
    
    def extract_text_from_bytes(self, pdf_bytes: bytes) -> str:
        """
        Extract text from PDF bytes.
        
        Args:
            pdf_bytes: PDF file content as bytes
            
        Returns:
            Extracted text content
        """
        if self.use_pdfplumber:
            return self._extract_with_pdfplumber_bytes(pdf_bytes)
        else:
            return self._extract_with_pypdf2_bytes(pdf_bytes)
    
    def _extract_with_pdfplumber(self, file_path: str) -> str:
        """
        Extract text using pdfplumber.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Extracted text content
        """
        text = ""
        
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            raise Exception(f"Error extracting text with pdfplumber: {str(e)}")
        
        return text.strip()
    
    def _extract_with_pdfplumber_bytes(self, pdf_bytes: bytes) -> str:
        """
        Extract text from bytes using pdfplumber.
        
        Args:
            pdf_bytes: PDF file content as bytes
            
        Returns:
            Extracted text content
        """
        text = ""
        
        try:
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            raise Exception(f"Error extracting text with pdfplumber: {str(e)}")
        
        return text.strip()
    
    def _extract_with_pypdf2(self, file_path: str) -> str:
        """
        Extract text using PyPDF2.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Extracted text content
        """
        text = ""
        
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            raise Exception(f"Error extracting text with PyPDF2: {str(e)}")
        
        return text.strip()
    
    def _extract_with_pypdf2_bytes(self, pdf_bytes: bytes) -> str:
        """
        Extract text from bytes using PyPDF2.
        
        Args:
            pdf_bytes: PDF file content as bytes
            
        Returns:
            Extracted text content
        """
        text = ""
        
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
            
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        except Exception as e:
            raise Exception(f"Error extracting text with PyPDF2: {str(e)}")
        
        return text.strip()
    
    def extract_tables_from_file(self, file_path: str) -> List[List[List[str]]]:
        """
        Extract tables from PDF file using pdfplumber.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            List of tables (each table is a list of rows, each row is a list of cells)
        """
        tables = []
        
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_tables = page.extract_tables()
                    if page_tables:
                        tables.extend(page_tables)
        except Exception as e:
            raise Exception(f"Error extracting tables: {str(e)}")
        
        # Clean table data
        cleaned_tables = []
        for table in tables:
            cleaned_table = []
            for row in table:
                if row:
                    cleaned_row = [str(cell) if cell is not None else "" for cell in row]
                    cleaned_table.append(cleaned_row)
            if cleaned_table:
                cleaned_tables.append(cleaned_table)
        
        return cleaned_tables
    
    def get_page_count(self, file_path: str) -> int:
        """
        Get number of pages in PDF.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Number of pages
        """
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                return len(pdf_reader.pages)
        except Exception as e:
            raise Exception(f"Error getting page count: {str(e)}")
    
    def is_searchable(self, file_path: str) -> bool:
        """
        Check if PDF is searchable (has text layer).
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            True if PDF is searchable, False otherwise
        """
        try:
            text = self.extract_text_from_file(file_path)
            return len(text.strip()) > 0
        except Exception:
            return False


if __name__ == "__main__":
    # Test the PDF extractor
    extractor = PDFExtractor(use_pdfplumber=True)
    
    print("PDF Extractor initialized successfully")
    print("Use with actual PDF files to test extraction functionality")
