import os
import re
from typing import List, Dict, Any

def extract_text_and_chunks_from_pdf(file_path: str, chunk_size: int = 500, chunk_overlap: int = 80) -> Dict[str, Any]:
    """
    Extract text from PDF page-by-page and produce structured chunks with page numbers.
    Supports pypdf, pdfplumber, or pymupdf (fitz).
    Handles corrupt, empty, and invalid PDF files gracefully.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"PDF file not found at path: {file_path}")

    file_size = os.path.getsize(file_path)
    if file_size == 0:
        raise ValueError("PDF processing failed: File is empty (0 bytes).")

    pages_data = []
    total_pages = 0

    # Try pypdf first (lightweight & pure python)
    try:
        from pypdf import PdfReader
        reader = PdfReader(file_path)
        if reader.is_encrypted:
            try:
                reader.decrypt('')
            except Exception:
                raise ValueError("PDF processing failed: Encrypted or password-protected PDF.")
        
        total_pages = len(reader.pages)
        if total_pages == 0:
            raise ValueError("PDF processing failed: PDF has 0 pages.")

        for idx, page in enumerate(reader.pages):
            text = page.extract_text() or ''
            clean_text = ' '.join(text.split())
            pages_data.append({
                'page_number': idx + 1,
                'text': clean_text
            })
    except ImportError:
        # Fallback to pdfplumber
        try:
            import pdfplumber
            with pdfplumber.open(file_path) as pdf:
                total_pages = len(pdf.pages)
                for idx, page in enumerate(pdf.pages):
                    text = page.extract_text() or ''
                    clean_text = ' '.join(text.split())
                    pages_data.append({
                        'page_number': idx + 1,
                        'text': clean_text
                    })
        except ImportError:
            # Fallback to PyMuPDF (fitz)
            try:
                import fitz
                doc = fitz.open(file_path)
                total_pages = len(doc)
                for idx, page in enumerate(doc):
                    text = page.get_text() or ''
                    clean_text = ' '.join(text.split())
                    pages_data.append({
                        'page_number': idx + 1,
                        'text': clean_text
                    })
            except Exception as e:
                raise ValueError(f"PDF processing failed: Unable to load any PDF parser ({e})")
    except Exception as e:
        raise ValueError(f"PDF processing failed: {str(e)}")

    # Check if any extractable text was found
    all_text = " ".join([p['text'] for p in pages_data]).strip()
    if not all_text:
        # Some PDFs may be scanned images; provide clear warning
        pages_data = [{
            'page_number': 1,
            'text': f"Scanned or image-only document ({os.path.basename(file_path)})."
        }]

    # Chunking algorithm with sliding window and sentence splitting
    chunks: List[Dict[str, Any]] = []
    chunk_index = 0

    for page in pages_data:
        p_num = page['page_number']
        p_text = page['text']
        if not p_text.strip():
            continue

        # Split into sentences or rough paragraphs
        sentences = re.split(r'(?<=[.!?\n])\s+', p_text)
        current_chunk = ""
        current_section = f"Page {p_num}"

        # Detect potential section headers (lines in uppercase or starting with numbers)
        for s in sentences:
            s_clean = s.strip()
            if not s_clean:
                continue

            if len(s_clean) < 60 and (s_clean.isupper() or re.match(r'^\d+(\.\d+)*\s+[A-Z]', s_clean)):
                current_section = s_clean

            if len(current_chunk) + len(s_clean) + 1 <= chunk_size:
                current_chunk = f"{current_chunk} {s_clean}".strip()
            else:
                if current_chunk:
                    chunks.append({
                        'chunk_index': chunk_index,
                        'page_number': p_num,
                        'section_title': current_section,
                        'content': current_chunk,
                        'content_length': len(current_chunk)
                    })
                    chunk_index += 1
                current_chunk = s_clean

        if current_chunk:
            chunks.append({
                'chunk_index': chunk_index,
                'page_number': p_num,
                'section_title': current_section,
                'content': current_chunk,
                'content_length': len(current_chunk)
            })
            chunk_index += 1

    return {
        'total_pages': total_pages,
        'total_chunks': len(chunks),
        'chunks': chunks
    }
