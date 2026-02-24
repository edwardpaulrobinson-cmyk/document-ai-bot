import fitz  # PyMuPDF
import docx
import os

def parse_file(file_path: str) -> str:
    """Extracts text from a given PDF, DOCX, or TXT file."""
    if not os.path.exists(file_path):
        return ""
        
    ext = file_path.lower().split('.')[-1]
    
    if ext == 'pdf':
        return parse_pdf(file_path)
    elif ext in ['doc', 'docx']:
        return parse_docx(file_path)
    elif ext in ['txt', 'md', 'csv']:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    else:
        return f"[Media File: {os.path.basename(file_path)} cannot be parsed locally yet]"

def parse_pdf(file_path: str) -> str:
    text = ""
    try:
        doc = fitz.open(file_path)
        for page in doc:
            text += page.get_text() + "\n"
        doc.close()
    except Exception as e:
        print(f"Error parsing PDF {file_path}: {e}")
    return text

def parse_docx(file_path: str) -> str:
    text = ""
    try:
        doc = docx.Document(file_path)
        for para in doc.paragraphs:
            text += para.text + "\n"
    except Exception as e:
        print(f"Error parsing DOCX {file_path}: {e}")
    return text

def get_all_kb_text(kb_dir: str) -> str:
    """Reads all files in the KB directory and combines their text."""
    if not os.path.exists(kb_dir):
        return ""
        
    combined_text = ""
    for filename in os.listdir(kb_dir):
        filepath = os.path.join(kb_dir, filename)
        if os.path.isfile(filepath):
            combined_text += f"\n\n--- DOCUMENT: {filename} ---\n"
            combined_text += parse_file(filepath)
            
    return combined_text
