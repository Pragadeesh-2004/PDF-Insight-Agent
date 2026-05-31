"""
Document Processing Service
Handles PDF/DOCX extraction and conversion to Markdown
"""

import fitz  # PyMuPDF
import io
import logging
from typing import Dict
import re
import zipfile
import xml.etree.ElementTree as ET
from google import genai
from google.genai import types
from app.core.config import settings

logger = logging.getLogger(__name__)


class PDFProcessor:
    """
    Processes supported document files and converts them to markdown
    """
    
    def __init__(self):
        self.logger = logger
        self.ocr_client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.ocr_model = settings.GEMINI_OCR_MODEL
    
    async def extract_text_from_pdf(self, file_content: bytes) -> str:
        """
        Extract text from PDF file
        """
        try:
            self.logger.info("📄 Extracting text from PDF...")
            
            # Open PDF from bytes
            pdf_document = fitz.open(stream=file_content, filetype="pdf")
            
            text = ""
            page_number = 0
            
            # Extract text from each page
            for page in pdf_document:
                page_number += 1
                page_text = page.get_text()
                if self._should_ocr_page(page_text):
                    self.logger.info(f"OCR fallback triggered for page {page_number}")
                    page_text = await self.extract_text_from_page_image(page, page_number)
                
                # Add page break marker
                text += f"\n\n--- Page {page_number} ---\n\n"
                text += page_text
            
            pdf_document.close()
            
            self.logger.info(f"✅ Extracted {len(text)} characters from {page_number} pages")
            return text
            
        except Exception as e:
            self.logger.error(f"❌ Error extracting PDF text: {e}")
            raise
    
    def _should_ocr_page(self, page_text: str) -> bool:
        """
        Decide whether a PDF page needs OCR fallback.
        """
        if not settings.OCR_ENABLED:
            return False

        return len(page_text.strip()) < settings.OCR_MIN_TEXT_CHARS

    async def extract_text_from_page_image(self, page, page_number: int) -> str:
        """
        Render a PDF page as an image and extract text using Gemini vision.
        """
        try:
            scale = settings.OCR_RENDER_DPI / 72
            matrix = fitz.Matrix(scale, scale)
            pixmap = page.get_pixmap(matrix=matrix, alpha=False)
            image_bytes = pixmap.tobytes("png")

            prompt = (
                "Extract all readable text from this document page. "
                "Preserve headings, paragraphs, tables, labels, and list order as plain text. "
                "Return only the extracted text. If no readable text is present, return an empty string."
            )

            response = self.ocr_client.models.generate_content(
                model=self.ocr_model,
                contents=[
                    types.Part.from_text(text=prompt),
                    types.Part.from_bytes(data=image_bytes, mime_type="image/png"),
                ],
            )

            extracted_text = (response.text or "").strip()
            self.logger.info(
                f"OCR extracted {len(extracted_text)} characters from page {page_number}"
            )
            return extracted_text

        except Exception as e:
            self.logger.warning(f"OCR failed for page {page_number}: {e}")
            return ""

    async def extract_metadata(self, file_content: bytes) -> Dict:
        """
        Extract metadata from PDF
        """
        try:
            pdf_document = fitz.open(stream=file_content, filetype="pdf")
            
            metadata = {
                "page_count": pdf_document.page_count,
                "title": pdf_document.metadata.get("title") or "Unknown",
                "author": pdf_document.metadata.get("author") or "Unknown",
                "subject": pdf_document.metadata.get("subject") or "Unknown",
                "creator": pdf_document.metadata.get("creator") or "Unknown",
            }
            
            pdf_document.close()
            page_count = metadata["page_count"]
            
            self.logger.info(f"📑 PDF Metadata: {page_count} pages, Title: {metadata['title']}")
            return metadata
            
        except Exception as e:
            self.logger.warning(f"⚠️  Could not extract PDF metadata: {e}")
            return {"page_count": 0, "title": "Unknown"}
    
    async def convert_to_markdown(self, text: str) -> str:
        """
        Convert extracted PDF text to markdown format
        Preserves structure while improving readability
        """
        try:
            self.logger.info("🔄 Converting text to markdown...")
            
            lines = text.split('\n')
            markdown_lines = []
            
            for line in lines:
                line = line.strip()
                
                if not line:
                    markdown_lines.append("")
                    continue
                
                # Detect headings (ALL CAPS lines or numbered sections)
                if line.isupper() and len(line) > 3:
                    markdown_lines.append(f"## {line}")
                elif re.match(r'^[\d]+\.[\s]+[A-Z]', line):
                    # Numbered headings like "1. Introduction"
                    markdown_lines.append(f"### {line}")
                # Detect references [1], [2], etc.
                elif re.match(r'^\[\d+\]', line):
                    markdown_lines.append(f"- {line}")
                # Detect bullet points
                elif line.startswith('-') or line.startswith('•'):
                    markdown_lines.append(f"- {line.lstrip('-•').strip()}")
                # Detect numbered lists
                elif re.match(r'^[\d]+\.\s', line):
                    markdown_lines.append(f"{line}")
                else:
                    markdown_lines.append(line)
            
            markdown_text = "\n".join(markdown_lines)
            
            self.logger.info(f"✅ Converted to markdown ({len(markdown_text)} chars)")
            return markdown_text
            
        except Exception as e:
            self.logger.error(f"❌ Error converting to markdown: {e}")
            # Return original text if conversion fails
            return text
    
    async def process_pdf(self, file_content: bytes, filename: str) -> Dict:
        """
        Complete PDF processing pipeline
        """
        try:
            self.logger.info(f"🚀 Processing PDF: {filename}")
            
            # Extract text
            extracted_text = await self.extract_text_from_pdf(file_content)
            
            # Extract metadata
            metadata = await self.extract_metadata(file_content)
            
            # Convert to markdown
            markdown_text = await self.convert_to_markdown(extracted_text)
            
            self.logger.info(f"✅ PDF processing complete for {filename}")
            
            return {
                "filename": filename,
                "text": markdown_text,
                "metadata": metadata,
                "raw_text": extracted_text,
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error in PDF processing pipeline: {e}")
            raise

    async def extract_text_from_docx(self, file_content: bytes) -> str:
        """
        Extract text from a DOCX file.
        """
        try:
            self.logger.info("Extracting text from DOCX...")

            with zipfile.ZipFile(io.BytesIO(file_content)) as docx_zip:
                document_xml = docx_zip.read("word/document.xml")

            root = ET.fromstring(document_xml)
            namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
            paragraphs = []

            for paragraph in root.findall(".//w:p", namespace):
                text_parts = [
                    text_node.text
                    for text_node in paragraph.findall(".//w:t", namespace)
                    if text_node.text
                ]
                paragraph_text = "".join(text_parts).strip()
                if paragraph_text:
                    paragraphs.append(paragraph_text)

            extracted_text = "\n\n".join(paragraphs)
            self.logger.info(f"Extracted {len(extracted_text)} characters from DOCX")
            return extracted_text

        except KeyError as e:
            self.logger.error(f"DOCX is missing required content: {e}")
            raise ValueError("Invalid DOCX file")
        except zipfile.BadZipFile:
            self.logger.error("DOCX file is not a valid ZIP archive")
            raise ValueError("Invalid DOCX file")
        except Exception as e:
            self.logger.error(f"Error extracting DOCX text: {e}")
            raise

    async def process_docx(self, file_content: bytes, filename: str) -> Dict:
        """
        Complete DOCX processing pipeline.
        """
        try:
            self.logger.info(f"Processing DOCX: {filename}")

            extracted_text = await self.extract_text_from_docx(file_content)
            markdown_text = await self.convert_to_markdown(extracted_text)

            self.logger.info(f"DOCX processing complete for {filename}")

            return {
                "filename": filename,
                "text": markdown_text,
                "metadata": {
                    "page_count": 1,
                    "title": filename,
                    "file_type": "docx",
                },
                "raw_text": extracted_text,
            }

        except Exception as e:
            self.logger.error(f"Error in DOCX processing pipeline: {e}")
            raise

    async def process_document(self, file_content: bytes, filename: str) -> Dict:
        """
        Process any supported document type.
        """
        lower_filename = filename.lower()

        if lower_filename.endswith(".pdf"):
            document_data = await self.process_pdf(file_content, filename)
            document_data["metadata"]["file_type"] = "pdf"
            return document_data

        if lower_filename.endswith(".docx"):
            return await self.process_docx(file_content, filename)

        raise ValueError("Only PDF and DOCX files are supported")


# Singleton instance
_pdf_processor = None


def get_pdf_processor() -> PDFProcessor:
    """
    Get or create PDFProcessor instance
    """
    global _pdf_processor
    if _pdf_processor is None:
        _pdf_processor = PDFProcessor()
    return _pdf_processor
