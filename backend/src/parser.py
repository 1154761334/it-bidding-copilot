import os
import tempfile
from markitdown import MarkItDown
import pymupdf4llm

def parse_to_markdown(file_bytes: bytes, filename: str) -> str:
    """
    Converts a given file to Markdown format based on its extension.
    Uses MarkItDown for Office docs and PyMuPDF4LLM for PDFs.
    """
    ext = os.path.splitext(filename)[1].lower()

    # Create a temporary file because these libraries often expect file paths
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp_file:
        tmp_file.write(file_bytes)
        tmp_file_path = tmp_file.name

    try:
        if ext == '.pdf':
            md_text = pymupdf4llm.to_markdown(tmp_file_path)
            return md_text
        elif ext in ['.docx', '.pptx', '.xlsx']:
            md = MarkItDown()
            result = md.convert(tmp_file_path)
            return result.text_content
        else:
            return f"Unsupported file extension: {ext}"
    except Exception as e:
        return f"Error parsing file: {str(e)}"
    finally:
        if os.path.exists(tmp_file_path):
            os.remove(tmp_file_path)
