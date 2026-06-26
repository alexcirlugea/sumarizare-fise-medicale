# backend/chains/sql.py
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq
import json

# Use the main LLM (same as in ai_service)
llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.1)

# Prompt for SQL generation
sql_generation_prompt = ChatPromptTemplate.from_template(
    """Ești un asistent AI expert în baze de date SQLite aplicate în domeniul medical.
Rolul tău este să generezi o singură interogare SQL SELECT validă pentru a răspunde la întrebarea utilizatorului.

Baza de date folosește următoarele vederi temporare (TEMP VIEW), care conțin exclusiv datele autorizate pentru utilizatorul curent:

1. Table/View: `auth_users`
   - `id` (INTEGER PRIMARY KEY)
   - `full_name` (TEXT)
   - `email` (TEXT)
   - `role` (TEXT CHECK(role IN ('admin', 'medic', 'pacient')))

2. Table/View: `auth_ehr_records`
   - `id` (INTEGER PRIMARY KEY)
   - `patient_id` (INTEGER, face legătură cu auth_users.id)
   - `filename` (TEXT)
   - `specialty` (TEXT - specialitatea medicală precum 'Cardiologie', 'Neurologie', 'Medicină Internă')
   - `diagnosis` (TEXT - diagnosticul principal la externare)
   - `summary` (TEXT - rezumatul fișei)
   - `created_at` (TIMESTAMP)

REGULI IMPORTANTE:
1. Folosește EXCLUSIV vederile temporare `auth_ehr_records` și `auth_users`. NU folosește tabelele brute fizice `ehr_records` etc.
2. Generează o singură interogare `SELECT` validă. Nu folosi comentarii, nu genera text introductiv. Returnează doar query-ul SQL curat.
3. Când cauți diagnostice în `auth_ehr_records`, folosește `LIKE` case-insensitive (ex: `diagnosis LIKE '%diabet%'`).
4. Când cauți specialități în `auth_ehr_records`, folosește de asemenea `LIKE` (ex: `specialty LIKE '%cardiologie%'`).
5. Returnează STRICT codul SQL, fără blocuri markdown (cum ar fi ```sql ... ```). Începe direct cu `SELECT`.

ÎNTREBAREA UTILIZATORULUI: {question}
"""
)

chain_sql_gen = sql_generation_prompt | llm | StrOutputParser()

# Prompt for SQL correction
sql_correction_prompt = ChatPromptTemplate.from_template(
    """Ești un expert în interogări SQLite aplicate în domeniul medical.
Interogarea SQL generată anterior a eșuat la rulare.

DETALII EȘEC:
ÎNTREBAREA UTILIZATORULUI: {question}
QUERY ERONAT: {bad_sql}
EROARE SQLITE: {error_msg}

Reguli de corectare:
1. Corectează interogarea astfel încât să fie o interogare `SELECT` SQLite validă.
2. Folosește exclusiv vederile temporare: `auth_ehr_records` și `auth_users`.
3. Asigură-te că toate numele de coloane și tabele sunt corecte.
4. Returnează STRICT interogarea SQL corectată, fără blocuri markdown sau text explicativ.

SQL CORECTAT:
"""
)

chain_sql_correct = sql_correction_prompt | llm | StrOutputParser()

# Prompt for synthesis of SQL results
sql_synthesis_prompt = ChatPromptTemplate.from_template(
    """Ești un asistent medical AI avansat și obiectiv. Rolul tău este să răspunzi clar și precis la întrebarea utilizatorului pe baza rezultatelor obținute direct din baza de date SQLite.

ÎNTREBAREA UTILIZATORULUI:
{question}

INTEROGAREA SQL RULATĂ:
{sql_query}

REZULTATE BAZĂ DE DATE (JSON):
{db_results}

REGULI DE RĂSPUNS:
1. Răspunde în limba română într-un mod natural, politicos și profesional.
2. Bazează-te STRICT pe rezultatele din baza de date. Nu inventa alte date.
3. Dacă rezultatul este gol sau 0, spune exact acest lucru (de exemplu, "Nu s-a găsit nicio fișă cu aceste criterii").
4. Nu afișa cod SQL sau detalii tehnice brute de baze de date în răspunsul final, doar informația sintetizată pe înțelesul utilizatorului.
"""
)

chain_sql_synthesis = sql_synthesis_prompt | llm | StrOutputParser()
