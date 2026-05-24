import os
import sqlite3
from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq
import uvicorn

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

cursor.execute("""
    CREATE TABLE IF NOT EXISTS ehr_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT,
        original_text TEXT,
        summary TEXT
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
chain_translate = translate_prompt | llm | StrOutputParser()
chain_chat = chat_prompt | llm | StrOutputParser()

class ChatMessage(BaseModel):
    message: str
    selected_ids: list[int] = []


class TranslateRequest(BaseModel):
    text: str

@app.post("/upload-summary")
async def create_upload_file(file: UploadFile = File(...)):
    if not file.filename.endswith(".txt"):
        raise HTTPException(status_code=400, detail="Doar fișiere .txt sunt permise momentan.")
    
    try:
        contents = await file.read()
        text_content = contents.decode("utf-8")
        
        print(f"Se procesează fișierul {file.filename}...")
        summary = chain_summary.invoke({"text": text_content})
        
        # Salvăm și numele fișierului în baza de date
        cursor.execute(
            "INSERT INTO ehr_records (filename, original_text, summary) VALUES (?, ?, ?)", 
            (file.filename, text_content, summary)
        )
        conn.commit()
        
        return {
            "filename": file.filename,
            "summary": summary, 
            "original_text": text_content
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/ehr")
async def get_all_ehr():
    """Returnează toate fișele salvate în baza de date."""
    cursor.execute("SELECT id, filename, original_text, summary FROM ehr_records ORDER BY id DESC")
    rows = cursor.fetchall()
    
    records = []
    for row in rows:
        records.append({
            "id": row[0],
            "filename": row[1],
            "original_text": row[2],
            "summary": row[3]
        })
    return records

@app.post("/api/translate")
async def translate_text(req: TranslateRequest):
    try:
        translation = chain_translate.invoke({"text": req.text})
        return {"translation": translation}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat")
async def chat_endpoint(req: ChatMessage):
    try:
        # Dacă frontend-ul a trimis ID-uri specifice, le folosim pe acelea
        if req.selected_ids:
            # Creăm un șir de semne de întrebare (?,?,?) în funcție de câte ID-uri avem
            placeholders = ','.join('?' * len(req.selected_ids))
            query = f"SELECT filename, summary FROM ehr_records WHERE id IN ({placeholders})"
            cursor.execute(query, req.selected_ids)
        else:
            # Fallback: dacă nu a trimis nimic (lista e goală), luăm ultimele 5
            cursor.execute("SELECT filename, summary FROM ehr_records ORDER BY id DESC LIMIT 5")
            
        rows = cursor.fetchall()
        
        if not rows:
            return {"reply": "Baza de date este goală sau fișierele selectate nu există. Te rog să încarci o fișă."}
        
        # Le combinăm folosind doar rezumatele scurte
        all_records = [f"--- REZUMAT FIȘIER: {row[0]} ---\n{row[1]}" for row in rows]
        combined_context = "\n\n".join(all_records)
        
        print(f"Trimit către Groq un context de {len(combined_context)} caractere din {len(rows)} fișiere...") 
        
        response = chain_chat.invoke({
            "context": combined_context,
            "question": req.message
        })
        
        return {"reply": response}
        
    except sqlite3.Error as sql_e:
        print(f"EROARE BAZA DE DATE: {sql_e}")
        raise HTTPException(status_code=500, detail=f"Eroare SQL: {sql_e}")
    except Exception as e:
        print(f"EROARE CHAT (Groq/Python): {e}") 
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)