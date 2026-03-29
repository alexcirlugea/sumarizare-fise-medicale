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

cursor.execute("DROP TABLE IF EXISTS ehr_records")

cursor.execute("""
    CREATE TABLE ehr_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        original_text TEXT,
        summary TEXT
    )
""")
conn.commit()

summary_prompt = ChatPromptTemplate.from_template(
    """Ești un medic specialist și un traducător medical expert. Sarcina ta este să analizezi următoarea fișă medicală și să extragi un rezumat clinic precis, exclusiv în limba română.
    
    REGULI: Traducere corectă (fără romgleză), acuratețe maximă la negații/valori anormale, ton obiectiv.

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
chain_chat = chat_prompt | llm | StrOutputParser()

class ChatMessage(BaseModel):
    message: str



@app.post("/upload-summary")
async def create_upload_file(file: UploadFile = File(...)):
    if not file.filename.endswith(".txt"):
        raise HTTPException(status_code=400, detail="Doar fișiere .txt sunt permise momentan.")
    
    try:
        contents = await file.read()
        text_content = contents.decode("utf-8")
        
        print("Se procesează fișierul...")
        summary = chain_summary.invoke({"text": text_content})
        
        cursor.execute(
            "INSERT INTO ehr_records (original_text, summary) VALUES (?, ?)", 
            (text_content, summary)
        )
        conn.commit()
        
        return {
            "summary": summary, 
            "original_text": text_content
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ehr")
async def get_all_ehr():
    """Returnează toate fișele salvate în baza de date."""
    cursor.execute("SELECT id, original_text, summary FROM ehr_records ORDER BY id DESC")
    rows = cursor.fetchall()
    
    records = []
    for row in rows:
        records.append({
            "id": row[0],
            "original_text": row[1],
            "summary": row[2]
        })
    
    return records


@app.post("/chat")
async def chat_endpoint(req: ChatMessage):
    cursor.execute("SELECT original_text FROM ehr_records")
    rows = cursor.fetchall()
    
    if not rows:
        return {"reply": "Baza de date este goală. Te rog să încarci o fișă la secțiunea 'Sumarizare'."}
    
    try:
        all_records = [f"--- FIȘA {i+1} ---\n{row[0]}" for i, row in enumerate(rows)]
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