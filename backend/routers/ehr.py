from fastapi import APIRouter, File, UploadFile, HTTPException, Form
from typing import List, Optional
import sqlite3
import json
import re

# Importăm ce avem nevoie din noile noastre fișiere
from database import conn, cursor, DB_PATH
from models import ChatMessage, RecordTranslateRequest
from utils import get_file_hash, get_unique_filename, extract_text_from_bytes
from ai_service import (
    detector, chain_summary, chain_summary_ro, chain_translate, chain_chat, 
    get_standardized_specialty, get_standardized_diagnosis,
    chain_router, chain_sql_gen, chain_sql_correct, chain_sql_synthesis,
    chunk_and_embed_document, query_vector_rag
)
from ai_service import force_sql_intent_if_aggregate

router = APIRouter()

@router.post("/upload-summary")
async def create_upload_files(
    files: List[UploadFile] = File(...),
    uid: str = Form(...),          # Acum facem uid-ul OBLIGATORIU pentru a ști mereu cine face request-ul
    patient_id: int = Form(None)
):
    if len(files) > 10:
        raise HTTPException(status_code=400, detail="Poți încărca maxim 10 fișiere simultan.")
    
    # --- LOGICA STRICTĂ DE SECURITATE (PROGRAMARE DEFENSIVĂ) ---
    cursor.execute("SELECT id, role FROM users WHERE firebase_uid = ?", (uid,))
    uploader = cursor.fetchone()
    
    if not uploader:
        raise HTTPException(status_code=404, detail="Contul care încarcă fișierul nu a fost găsit în sistem.")
        
    uploader_id = uploader[0]
    uploader_role = uploader[1]
    
    target_id = None
    
    # Verificăm permisiunile în funcție de rol
    if uploader_role == 'medic':
        if not patient_id:
            raise HTTPException(status_code=403, detail="Ca medic, trebuie să selectezi un pacient pentru a încărca fișe.")
        if patient_id == uploader_id:
            raise HTTPException(status_code=403, detail="Eroare de securitate: Medicii nu pot încărca fișe în propriul dosar medical.")
        target_id = patient_id
        
    elif uploader_role == 'pacient':
        if patient_id and patient_id != uploader_id:
            raise HTTPException(status_code=403, detail="Eroare de securitate: Pacienții pot încărca fișe doar pentru ei înșiși.")
        target_id = uploader_id
        
    else:
        # Pentru admini (dacă e nevoie vreodată), le permitem ambele variante
        target_id = patient_id if patient_id else uploader_id
    # ------------------------------------------------------------

    results = []
    # ... Restul codului rămâne absolut identic (for file in files: ...)
    for file in files:
        if not (file.filename.lower().endswith(".txt") or file.filename.lower().endswith(".pdf")):
            continue
            
        try:
            contents = await file.read()
            file_hash = get_file_hash(contents)
            
            cursor.execute("SELECT id, filename, original_text, summary, language, translated_text, translated_summary, specialty, diagnosis FROM ehr_records WHERE file_hash = ?", (file_hash,))
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
                    "specialty": existing_record[7] if existing_record[7] else "Nespecificat",
                    "diagnosis": existing_record[8] if existing_record[8] else "Nespecificat",
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
            
            # Extragem și standardizăm specialitatea
            specialty = get_standardized_specialty(text_content, lang_code)
            
            # Extragem și standardizăm diagnosticul principal
            diagnosis = get_standardized_diagnosis(text_content, lang_code)
            
            unique_filename = get_unique_filename(cursor, file.filename)
            
            # Folosim target_id calculat mai sus
            cursor.execute(
                "INSERT INTO ehr_records (patient_id, filename, original_text, summary, file_hash, language, specialty, diagnosis, translated_text, translated_summary) VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL)", 
                (target_id, unique_filename, text_content, summary, file_hash, lang_code, specialty, diagnosis)
            )
            new_id = cursor.lastrowid
            conn.commit()
            
            # Adăugăm în ChromaDB în timp real
            try:
                chunk_and_embed_document(target_id, new_id, specialty, unique_filename, text_content)
            except Exception as chroma_err:
                print(f"⚠️ Eroare la indexarea în ChromaDB: {chroma_err}")
            
            results.append({
                "id": new_id,
                "filename": unique_filename,
                "summary": summary, 
                "original_text": text_content,
                "language": lang_code,
                "specialty": specialty,
                "diagnosis": diagnosis,
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

@router.get("/api/ehr")
async def get_all_ehr(uid: str = None):
    if not uid:
        raise HTTPException(status_code=400, detail="Lipsește parametrul uid.")
        
    cursor.execute("SELECT id, role, full_name FROM users WHERE firebase_uid = ?", (uid,))
    user = cursor.fetchone()
    if not user:
        return [] 
        
    user_db_id = user[0]
    user_role = user[1]
    
    # Construim query-ul în funcție de rol
    if user_role == 'medic':
        # Medicul vede fișele tuturor pacienților săi
        cursor.execute("""
            SELECT e.id, e.filename, e.original_text, e.summary, e.language, e.translated_text, e.translated_summary, u.full_name, e.specialty, e.diagnosis
            FROM ehr_records e
            JOIN medic_pacient mp ON e.patient_id = mp.pacient_id
            JOIN users u ON e.patient_id = u.id
            WHERE mp.medic_id = ? 
            ORDER BY e.created_at DESC
        """, (user_db_id,))
    elif user_role == 'admin':
        # Adminul le vede pe toate
        cursor.execute("""
            SELECT e.id, e.filename, e.original_text, e.summary, e.language, e.translated_text, e.translated_summary, u.full_name, e.specialty, e.diagnosis
            FROM ehr_records e
            JOIN users u ON e.patient_id = u.id
            ORDER BY e.created_at DESC
        """)
    else:
        # Pacientul își vede doar propriile fișe
        cursor.execute("""
            SELECT e.id, e.filename, e.original_text, e.summary, e.language, e.translated_text, e.translated_summary, u.full_name, e.specialty, e.diagnosis
            FROM ehr_records e
            JOIN users u ON e.patient_id = u.id
            WHERE e.patient_id = ? 
            ORDER BY e.created_at DESC
        """, (user_db_id,))
    
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
            "translated_summary": row[6],
            "patient_name": row[7], # Aducem și numele pacientului către Angular!
            "specialty": row[8] if row[8] else "Nespecificat",
            "diagnosis": row[9] if row[9] else "Nespecificat"
        })
    return records

@router.get("/api/ehr/patient/{target_patient_id}")
async def get_patient_records(target_patient_id: int):
    # Această funcție este folosită de Medic pentru a vedea fișele pacientului său
    try:
        cursor.execute("""
            SELECT id, filename, original_text, summary, language, translated_text, translated_summary, specialty, diagnosis 
            FROM ehr_records 
            WHERE patient_id = ? 
            ORDER BY id DESC
        """, (target_patient_id,))
        
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
                "translated_summary": row[6],
                "specialty": row[7] if row[7] else "Nespecificat",
                "diagnosis": row[8] if row[8] else "Nespecificat"
            })
            
        return records
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/ehr/translate")
async def translate_record_endpoint(req: RecordTranslateRequest):
    try:
        print(f"🌐 Se generează și se salvează traducerea permanentă pentru ID {req.id}...")
        translated_text = chain_translate.invoke({"text": req.original_text})
        translated_summary = chain_translate.invoke({"text": req.summary})
        
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

def setup_authorized_views(db_cursor, allowed_ids: List[int]):
    # Curățăm vederile vechi dacă există
    db_cursor.execute("DROP VIEW IF EXISTS auth_users")
    db_cursor.execute("DROP VIEW IF EXISTS auth_ehr_records")
    
    # Pentru a preveni erorile SQL, dacă lista e goală punem un ID imposibil (-99)
    ids_str = ",".join(str(i) for i in allowed_ids) if allowed_ids else "-99"
    
    db_cursor.execute(f"""
        CREATE TEMP VIEW auth_users AS 
        SELECT id, full_name, email, role 
        FROM users 
        WHERE id IN ({ids_str})
    """)
    
    db_cursor.execute(f"""
        CREATE TEMP VIEW auth_ehr_records AS 
        SELECT id, patient_id, filename, specialty, diagnosis, summary, created_at, original_text 
        FROM ehr_records 
        WHERE patient_id IN ({ids_str})
    """)

def is_safe_sql(sql_str: str) -> bool:
    sql_clean = sql_str.lower().strip()
    
    # 1. Permitem STRICT query-uri SELECT
    if not sql_clean.startswith("select"):
        return False
        
    # 2. Blocăm query-urile ce încearcă modificări sau scrieri
    unsafe_keywords = ["insert", "update", "delete", "drop", "alter", "create", "replace", "truncate", "grant"]
    for word in unsafe_keywords:
        # Folosim regex boundary (\b) pentru a evita potriviri parțiale în cuvinte valide din română
        if re.search(rf"\b{word}\b", sql_clean):
            return False
            
    # 3. Blocăm comentariile SQL care pot fi folosite pentru evadarea din clauze
    if "--" in sql_str or "/*" in sql_str or "*/" in sql_str:
        return False
        
    # 4. Prevenim execuția de comenzi multiple (SQL chaining) prin punct și virgulă
    if ";" in sql_str:
        parts = [p.strip() for p in sql_str.split(";") if p.strip()]
        if len(parts) > 1:
            return False
            
    return True

@router.post("/chat")
async def chat_endpoint(req: ChatMessage):
    try:
        # 1. Preluare utilizator autorizat
        cursor.execute("SELECT id, role, full_name FROM users WHERE firebase_uid = ?", (req.uid,))
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="Utilizatorul nu a fost găsit în sistem.")
        
        user_id, role, full_name = user
        
        # 2. Determinare listă ID-uri pacienți autorizați
        if role == 'pacient':
            allowed_patient_ids = [user_id]
        elif role == 'medic':
            cursor.execute("SELECT pacient_id FROM medic_pacient WHERE medic_id = ?", (user_id,))
            allowed_patient_ids = [row[0] for row in cursor.fetchall()]
        elif role == 'admin':
            cursor.execute("SELECT id FROM users WHERE role = 'pacient'")
            allowed_patient_ids = [row[0] for row in cursor.fetchall()]
        else:
            allowed_patient_ids = []
            
        if not allowed_patient_ids:
            return {"reply": "Nu aveți acces la datele niciunui pacient în sistem."}
            
        # 3. Filtrare bazată pe Scope-ul selectat
        patient_id_filter = None
        if req.scope == "patient" and req.patient_id is not None:
            if req.patient_id not in allowed_patient_ids:
                raise HTTPException(status_code=403, detail="Acces refuzat: Nu aveți permisiunea de a accesa acest pacient.")
            allowed_patient_ids = [req.patient_id]
            patient_id_filter = req.patient_id
            
        # 3b. Validare selected_ids (verificăm că aparțin pacienților autorizați)
        safe_selected_ids = None
        if req.selected_ids and len(req.selected_ids) > 0:
            placeholders = ','.join('?' * len(req.selected_ids))
            patient_placeholders = ','.join('?' * len(allowed_patient_ids))
            cursor.execute(
                f"SELECT id FROM ehr_records WHERE id IN ({placeholders}) AND patient_id IN ({patient_placeholders})",
                req.selected_ids + allowed_patient_ids
            )
            safe_selected_ids = [row[0] for row in cursor.fetchall()]
            
        # 4. Clasificare Intent (Router)
        # Dacă avem fișe selectate manual, forțăm INTENT_A (RAG contextual)
        if safe_selected_ids:
            intent = "INTENT_A"
            confidence = 1.0
        else:
            # Detect aggregate intent to force SQL
            forced_intent = force_sql_intent_if_aggregate(req.message)
            if forced_intent:
                intent = forced_intent
                confidence = 1.0
            else:
                intent_res = chain_router.invoke({"question": req.message})
                intent = intent_res.intent
                confidence = intent_res.confidence

            if confidence < 0.7:
                intent = "INTENT_A"
            
        # 5. Execuție workflow corespunzător
        if intent == "INTENT_A":
            # Workflow A: Vector RAG (cu sau fără context selectiv)
            reply = query_vector_rag(req.message, allowed_patient_ids, patient_id_filter, safe_selected_ids)
            return {"reply": reply}
            
        else:
            # Workflow B: Text-to-SQL
            chat_conn = sqlite3.connect(DB_PATH)
            chat_cursor = chat_conn.cursor()
            
            # Setup vederi temporare securizate pe conexiunea curentă
            setup_authorized_views(chat_cursor, allowed_patient_ids)
            
            # Generare SQL
            sql_query = chain_sql_gen.invoke({"question": req.message})
            sql_query = sql_query.strip().replace("```sql", "").replace("```", "").strip()
            
            # Validare siguranță SQL
            if not is_safe_sql(sql_query):
                print(f"⚠️ SQL nesigur: '{sql_query}'. Fallback la Vector RAG.")
                chat_conn.close()
                reply = query_vector_rag(req.message, allowed_patient_ids, patient_id_filter)
                return {"reply": reply}
                
            # Execuție cu Try-Catch-Retry (Autocorecție)
            try:
                chat_cursor.execute(sql_query)
                rows = chat_cursor.fetchall()
                columns = [desc[0] for desc in chat_cursor.description]
                db_results = [dict(zip(columns, row)) for row in rows]
            except Exception as sql_err:
                print(f"⚠️ Eroare rulare SQL: {sql_err}. Se încearcă autocorecția...")
                try:
                    corrected_sql = chain_sql_correct.invoke({
                        "question": req.message,
                        "bad_sql": sql_query,
                        "error_msg": str(sql_err)
                    })
                    corrected_sql = corrected_sql.strip().replace("```sql", "").replace("```", "").strip()
                    
                    if not is_safe_sql(corrected_sql):
                        raise ValueError("Unsafe corrected SQL query")
                        
                    chat_cursor.execute(corrected_sql)
                    rows = chat_cursor.fetchall()
                    columns = [desc[0] for desc in chat_cursor.description]
                    db_results = [dict(zip(columns, row)) for row in rows]
                    sql_query = corrected_sql
                except Exception as retry_err:
                    print(f"❌ Autocorecția a eșuat sau interogarea e nesigură: {retry_err}. Fallback la Vector RAG.")
                    chat_conn.close()
                    reply = query_vector_rag(req.message, allowed_patient_ids, patient_id_filter)
                    return {"reply": reply}
            
            # Sinteză răspuns din rezultate baze de date
            db_results_json = json.dumps(db_results, ensure_ascii=False)
            reply = chain_sql_synthesis.invoke({
                "question": req.message,
                "sql_query": sql_query,
                "db_results": db_results_json
            })
            
            chat_conn.close()
            return {"reply": reply}
            
    except Exception as e:
        print(f"❌ Eroare generală în chat_endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))