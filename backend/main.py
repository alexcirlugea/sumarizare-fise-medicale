import os
import sqlite3
import hashlib
import fitz  # PyMuPDF pentru PDF-uri
from typing import List
from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq
import uvicorn

from lingua import Language, LanguageDetectorBuilder
detector = LanguageDetectorBuilder.from_languages(
    Language.ROMANIAN, Language.ENGLISH, Language.FRENCH, Language.GERMAN
).build()

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

llm = ChatGroq(
    model="llama-3.3-70b-versatile", 
    temperature=0.1, 
)

db_path = os.path.join(os.path.dirname(__file__), "ehr_database.db")
conn = sqlite3.connect(db_path, check_same_thread=False)
cursor = conn.cursor()

# RECREARE TABEL: Adăugat translated_text și translated_summary
cursor.execute("""
    CREATE TABLE IF NOT EXISTS ehr_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT,
        original_text TEXT,
        summary TEXT,
        file_hash TEXT,
        language TEXT,
        translated_text TEXT,
        translated_summary TEXT
    )
""")
conn.commit()

summary_prompt = ChatPromptTemplate.from_template(
    """You are a medical specialist. Your task is to analyze the following medical record and extract an accurate clinical summary, exclusively in English.
    
    MEDICAL RECORD TEXT:
    {text}
    
    TASK: Generate the structured summary EXACTLY in this Markdown format:
    - **Reason for Presentation**: 
    - **Medical History**: 
    - **Discharge Diagnosis**: 
    - **Treatment and Interventions**: 
    - **Recommendations**: 
    
    Your response must contain STRICTLY this summary.
    """
)

summary_prompt_ro = ChatPromptTemplate.from_template(
    """Ești un specialist medical. Sarcina ta este să analizezi următoarea fișă medicală și să extragi un rezumat clinic precis, exclusiv în limba ROMÂNĂ.
    
    TEXT FIȘĂ MEDICALĂ:
    {text}
    
    SARCINĂ: Generează rezumatul structurat EXACT în acest format Markdown:
    - **Motivul Prezentării**: 
    - **Istoric Medical**: 
    - **Diagnostic la Externare**: 
    - **Tratament și Intervenții**: 
    - **Recomandări**: 
    
    Răspunsul tău trebuie să conțină STRICT acest rezumat.
    """
)

translate_prompt = ChatPromptTemplate.from_template(
    """Ești un expert medical. Tradu următorul text medical din limba engleză în limba română. 
    Păstrează formatarea Markdown inițială, fii precis și folosește terminologia medicală corectă.
    
    TEXT DE TRADUS:
    {text}
    """
)

chat_prompt = ChatPromptTemplate.from_template(
    """Ești un asistent medical inteligent și un traducător medical expert. Răspunde la întrebarea utilizatorului folosind STRICT informațiile din fișele medicale de mai jos. 
    Dacă răspunsul nu se află în fișe, spune clar că nu ai aceste informații. Nu inventa.

    FIȘELE MEDICALE ÎNCĂRCATE PÂNĂ ACUM:
    {context}

    ÎNTREBAREA UTILIZATORULUI:
    {question}
    """
)

chain_summary = summary_prompt | llm | StrOutputParser()
chain_summary_ro = summary_prompt_ro | llm | StrOutputParser()
chain_translate = translate_prompt | llm | StrOutputParser()
chain_chat = chat_prompt | llm | StrOutputParser()

class ChatMessage(BaseModel):
    message: str
    selected_ids: list[int] = []

# NOU: Model pentru cererea de traducere legată de o fișă specifică
class RecordTranslateRequest(BaseModel):
    id: int
    original_text: str
    summary: str

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

# --- RUTĂ UPLOAD MODIFICATĂ (Returnează ID-ul și traducerile existente) ---
@app.post("/upload-summary")
async def create_upload_files(files: List[UploadFile] = File(...)):
    if len(files) > 10:
        raise HTTPException(status_code=400, detail="Poți încărca maxim 10 fișiere simultan.")
    
    results = []
    for file in files:
        if not (file.filename.lower().endswith(".txt") or file.filename.lower().endswith(".pdf")):
            continue
            
        try:
            contents = await file.read()
            file_hash = get_file_hash(contents)
            
            # Verificăm duplicatele și aducem tot, inclusiv traducerile dacă existau deja!
            cursor.execute("SELECT id, filename, original_text, summary, language, translated_text, translated_summary FROM ehr_records WHERE file_hash = ?", (file_hash,))
            existing_record = cursor.fetchone()
            
            if existing_record:
                print(f"🔄 Duplicat găsit pentru: {file.filename}.")
                results.append({
                    "id": existing_record[0],
                    "filename": existing_record[1],
                    "original_text": existing_record[2],
                    "summary": existing_record[3],
                    "language": existing_record[4],
                    "translated_text": existing_record[5],
                    "translated_summary": existing_record[6],
                    "is_duplicate": True
                })
                continue
            
            print(f"📄 Se procesează fișierul {file.filename}...")
            text_content = extract_text_from_bytes(file.filename, contents)
            
            detected_lang = detector.detect_language_of(text_content)
            lang_code = detected_lang.name if detected_lang else "UNKNOWN"
            
            if lang_code == "ROMANIAN":
                summary = chain_summary_ro.invoke({"text": text_content})
            else:
                summary = chain_summary.invoke({"text": text_content})
            
            unique_filename = get_unique_filename(cursor, file.filename)
            
            cursor.execute(
                "INSERT INTO ehr_records (filename, original_text, summary, file_hash, language, translated_text, translated_summary) VALUES (?, ?, ?, ?, ?, NULL, NULL)", 
                (unique_filename, text_content, summary, file_hash, lang_code)
            )
            new_id = cursor.lastrowid
            conn.commit()
            
            results.append({
                "id": new_id,
                "filename": unique_filename,
                "summary": summary, 
                "original_text": text_content,
                "language": lang_code,
                "translated_text": None,
                "translated_summary": None,
                "is_duplicate": False
            })
            
        except Exception as e:
            print(f"Eroare la procesarea {file.filename}: {e}")
            pass
            
    if not results:
        raise HTTPException(status_code=400, detail="Nu s-a putut procesa niciun fișier.")
    return {"processed_files": results}

@app.get("/api/ehr")
async def get_all_ehr():
    cursor.execute("SELECT id, filename, original_text, summary, language, translated_text, translated_summary FROM ehr_records ORDER BY id DESC")
    rows = cursor.fetchall()
    
    records = []
    for row in rows:
        records.append({
            "id": row[0],
            "filename": row[1],
            "original_text": row[2],
            "summary": row[3],
            "language": row[4],
            "translated_text": row[5],
            "translated_summary": row[6]
        })
    return records

# --- ENDPOINT NOU/ACTUALIZAT PENTRU TRADUCERE SIMULTANĂ ȘI SALVARE PERMANENTĂ ---
@app.post("/api/ehr/translate")
async def translate_record_endpoint(req: RecordTranslateRequest):
    try:
        print(f"🌐 Se generează și se salvează traducerea permanentă pentru ID {req.id}...")
        translated_text = chain_translate.invoke({"text": req.original_text})
        translated_summary = chain_translate.invoke({"text": req.summary})
        
        # Salvare directă în rândul corespunzător din baza de date
        cursor.execute(
            "UPDATE ehr_records SET translated_text = ?, translated_summary = ? WHERE id = ?",
            (translated_text, translated_summary, req.id)
        )
        conn.commit()
        
        return {
            "translated_text": translated_text,
            "translated_summary": translated_summary
        }
    except Exception as e:
        print(f"❌ Eroare la traducere/salvare: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def chat_endpoint(req: ChatMessage):
    try:
        if req.selected_ids:
            placeholders = ','.join('?' * len(req.selected_ids))
            query = f"SELECT filename, summary FROM ehr_records WHERE id IN ({placeholders})"
            cursor.execute(query, req.selected_ids)
        else:
            cursor.execute("SELECT filename, summary FROM ehr_records ORDER BY id DESC LIMIT 5")
            
        rows = cursor.fetchall()
        
        if not rows:
            return {"reply": "Baza de date este goală sau fișierele selectate nu există. Te rog să încarci o fișă."}
        
        all_records = [f"--- REZUMAT FIȘIER: {row[0]} ---\n{row[1]}" for row in rows]
        combined_context = "\n\n".join(all_records)
        
        response = chain_chat.invoke({
            "context": combined_context,
            "question": req.message
        })
        return {"reply": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)