import os
from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq # Am schimbat cu ChatGroq din Langchain
import uvicorn

# Încărcăm variabilele de mediu din fișierul .env
load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inițializare LLM (Groq)
# ChatGroq va prelua automat GROQ_API_KEY din mediul încărcat de dotenv.
# Poți schimba modelul cu "llama3-70b-8192"
llm = ChatGroq(
    model="llama-3.3-70b-versatile", 
    temperature=0.1, 
)

# Definirea prompt-ului
summary_prompt = ChatPromptTemplate.from_template(
    """Ești un medic specialist și un traducător medical expert. Sarcina ta este să analizezi următoarea fișă medicală (care poate conține abrevieri și termeni în engleză) și să extragi un rezumat clinic precis, exclusiv în limba română.
    
    REGULI GENERALE DE REDACTARE CLINICĂ:
    1. Traducere corectă: Folosește exclusiv terminologia medicală standard din România. Evită complet "romgleza".
    2. Acuratețe maximă: Fii extrem de atent la negații (ex: "fără durere"), la valorile anormale (crescut/scăzut) și la diagnostice. Nu inventa informații care nu există în text (fără halucinații).
    3. Ton: Obiectiv, clar, concis și profesional. 

    TEXT FIȘĂ MEDICALĂ:
    {text}
    
    SARCINĂ:
    Generează rezumatul structurat EXACT în acest format Markdown (folosește strict aceste 5 titluri):
    
    - **Motivul Prezentării**: Care a fost simptomul sau problema principală care a adus pacientul la spital (Chief Complaint)?
    - **Istoric Medical**: Care sunt bolile cronice sau antecedentele medicale majore ale pacientului?
    - **Diagnostic la Externare**: Care sunt diagnosticele principale și secundare stabilite la finalul internării?
    - **Tratament și Intervenții**: Ce proceduri majore s-au efectuat în spital și ce medicamente cheie i-au fost prescrise la externare? (Fii concis).
    - **Recomandări**: Ce instrucțiuni a primit pacientul la externare (dietă, stil de viață, semne de alarmă, programări viitoare)?
    
    Răspunsul tău trebuie să conțină STRICT acest rezumat, fără nicio altă introducere, concluzie sau comentariu suplimentar.
    """
)

chain = summary_prompt | llm | StrOutputParser()

@app.post("/upload-summary")
async def create_upload_file(file: UploadFile = File(...)):
    if not file.filename.endswith(".txt"):
        raise HTTPException(status_code=400, detail="Doar fișiere .txt sunt permise momentan.")
    
    try:
        contents = await file.read()
        text_content = contents.decode("utf-8")
        
        print("Se procesează fișierul prin Groq...")
        summary = chain.invoke({"text": text_content})
        
        return {"summary": summary}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)