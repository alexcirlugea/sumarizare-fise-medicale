import os
import hashlib
import fitz  # PyMuPDF

def get_file_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()

def get_unique_filename(cursor, base_filename: str) -> str:
    name, ext = os.path.splitext(base_filename)
    counter = 1
    new_filename = base_filename
    while True:
        cursor.execute("SELECT id FROM ehr_records WHERE filename = ?", (new_filename,))
        if not cursor.fetchone():
            return new_filename
        new_filename = f"{name} ({counter}){ext}"
        counter += 1

def extract_text_from_bytes(filename: str, content: bytes) -> str:
    if filename.lower().endswith(".pdf"):
        doc = fitz.open(stream=content, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    return content.decode("utf-8", errors="ignore")