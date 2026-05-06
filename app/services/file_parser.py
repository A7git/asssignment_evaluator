"""File parser service — extracts text from PDF, Word, and code files."""
import os


def parse_file(filepath):
    """Auto-detect file type and extract text content.

    Args:
        filepath: Absolute or relative path to the file.

    Returns:
        str: Extracted text content from the file.
    """
    ext = os.path.splitext(filepath)[1].lower().lstrip('.')

    parsers = {
        'pdf': parse_pdf,
        'docx': parse_docx,
        'doc': parse_docx,
        'txt': parse_text,
        'py': read_code_file,
        'java': read_code_file,
        'cpp': read_code_file,
        'c': read_code_file,
        'h': read_code_file,
        'hpp': read_code_file,
    }

    parser = parsers.get(ext)
    if parser:
        return parser(filepath)

    # Fallback: try to read as text
    return read_code_file(filepath)


def parse_pdf(filepath):
    """Extract text from a PDF file using PyPDF2."""
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(filepath)
        text_parts = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
        return '\n'.join(text_parts)
    except Exception as e:
        print(f"Error parsing PDF {filepath}: {str(e)}")
        return ""


def parse_docx(filepath):
    """Extract text from a Word document using python-docx."""
    try:
        from docx import Document
        doc = Document(filepath)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return '\n'.join(paragraphs)
    except Exception as e:
        print(f"Error parsing DOCX {filepath}: {str(e)}")
        return ""


def parse_text(filepath):
    """Read plain text file."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading text {filepath}: {str(e)}")
        return ""


def read_code_file(filepath):
    """Read a source code file as plain text."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading code {filepath}: {str(e)}")
        return ""
