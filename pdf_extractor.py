"""
Enhanced PDF text extraction with OCR support for image-heavy documents.
"""

import io
import logging
import os
from typing import Optional

import PyPDF2

logger = logging.getLogger(__name__)

# Try to import OCR libraries (optional)
try:
    from pdf2image import convert_from_bytes
    import pytesseract
    from PIL import Image
    
    # Configure Tesseract path for Windows if needed
    if os.name == 'nt':  # Windows
        possible_paths = [
            r'C:\Program Files\Tesseract-OCR\tesseract.exe',
            r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
            r'C:\Tesseract-OCR\tesseract.exe',
        ]
        for path in possible_paths:
            if os.path.exists(path):
                pytesseract.pytesseract.tesseract_cmd = path
                logger.info(f"Found Tesseract at: {path}")
                break
    
    # Configure Poppler path for Windows if needed
    if os.name == 'nt':  # Windows
        poppler_path = r'C:\poppler\Library\bin'
        if os.path.exists(poppler_path):
            # Add to PATH for current process
            os.environ['PATH'] = poppler_path + os.pathsep + os.environ.get('PATH', '')
            logger.info(f"Added Poppler to PATH: {poppler_path}")
    
    OCR_AVAILABLE = True
    logger.info("OCR support available (pdf2image + pytesseract)")
except ImportError as e:
    OCR_AVAILABLE = False
    logger.warning(f"OCR not available: {e}. Install: pip install pdf2image pytesseract pillow")
except Exception as e:
    OCR_AVAILABLE = False
    logger.warning(f"OCR configuration error: {e}")


def extract_text_with_ocr(pdf_bytes: bytes, use_ocr: bool = True) -> str:
    """
    Extract text from PDF with OCR fallback for image-heavy documents.
    
    Args:
        pdf_bytes: PDF file as bytes
        use_ocr: If True and OCR is available, use OCR on pages with little text
    
    Returns:
        Extracted text from the PDF
    """
    text_parts = []
    
    # First try PyPDF2 (fast for text-based PDFs)
    try:
        reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
        total_pages = len(reader.pages)
        logger.info(f"Extracting text from {total_pages} pages")
        
        low_text_pages = []  # Track pages with little text for OCR
        
        for page_num, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""
            
            # Check if page has meaningful text
            if len(page_text.strip()) < 50:  # Less than 50 chars = probably image-heavy
                low_text_pages.append(page_num)
                logger.debug(f"Page {page_num + 1} has minimal text ({len(page_text)} chars)")
            
            text_parts.append(page_text)
        
        # If many pages have little text and OCR is available, use OCR
        if use_ocr and OCR_AVAILABLE and len(low_text_pages) > 0:
            logger.info(f"Running OCR on {len(low_text_pages)} pages with minimal text")
            ocr_text = _extract_with_ocr(pdf_bytes, page_numbers=low_text_pages)
            
            # Replace low-text pages with OCR results
            for page_num, ocr_page_text in zip(low_text_pages, ocr_text):
                if len(ocr_page_text) > len(text_parts[page_num]):
                    logger.info(f"OCR improved page {page_num + 1}: {len(text_parts[page_num])} -> {len(ocr_page_text)} chars")
                    text_parts[page_num] = ocr_page_text
        
        full_text = "\n\n".join(text_parts)
        logger.info(f"Extracted {len(full_text)} characters total")
        return full_text
        
    except Exception as e:
        logger.error(f"Error during text extraction: {e}")
        return ""


def _extract_with_ocr(pdf_bytes: bytes, page_numbers: Optional[list] = None) -> list:
    """
    Use OCR to extract text from specific PDF pages.
    
    Args:
        pdf_bytes: PDF file as bytes
        page_numbers: List of 0-indexed page numbers to OCR (None = all pages)
    
    Returns:
        List of extracted text strings (one per page)
    """
    if not OCR_AVAILABLE:
        logger.warning("OCR requested but not available")
        return []
    
    try:
        # Convert PDF pages to images
        images = convert_from_bytes(pdf_bytes, dpi=300)
        
        ocr_results = []
        pages_to_process = page_numbers if page_numbers else range(len(images))
        
        for page_num in pages_to_process:
            if page_num >= len(images):
                continue
                
            logger.debug(f"OCR processing page {page_num + 1}")
            image = images[page_num]
            
            # Run OCR
            text = pytesseract.image_to_string(image, lang='eng')
            ocr_results.append(text)
        
        return ocr_results
        
    except Exception as e:
        logger.error(f"OCR extraction failed: {e}")
        return []


def extract_text_simple(pdf_bytes: bytes) -> str:
    """
    Simple text extraction without OCR (faster, for text-based PDFs).
    
    Args:
        pdf_bytes: PDF file as bytes
    
    Returns:
        Extracted text
    """
    try:
        reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
        text_parts = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
        return "\n\n".join(text_parts)
    except Exception as e:
        logger.error(f"Simple extraction failed: {e}")
        return ""


def is_ocr_available() -> bool:
    """Check if OCR dependencies are installed."""
    return OCR_AVAILABLE
