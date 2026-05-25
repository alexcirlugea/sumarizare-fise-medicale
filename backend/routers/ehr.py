from fastapi import APIRouter, File, UploadFile, HTTPException, Form
from typing import List

# Importăm ce avem nevoie din noile noastre fișiere
from database import conn, cursor
from models import ChatMessage, RecordTranslateRequest
from utils import get_file_hash, get_unique_filename, extract_text_from_bytes
from ai_service import detector, chain_summary, chain_summary_ro, chain_translate, chain_chat

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
            
            # Folosim target_id calculat mai sus
            cursor.execute(
                "INSERT INTO ehr_records (patient_id, filename, original_text, summary, file_hash, language, translated_text, translated_summary) VALUES (?, ?, ?, ?, ?, ?, NULL, NULL)", 
                (target_id, unique_filename, text_content, summary, file_hash, lang_code)
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
            SELECT e.id, e.filename, e.original_text, e.summary, e.language, e.translated_text, e.translated_summary, u.full_name
            FROM ehr_records e
            JOIN medic_pacient mp ON e.patient_id = mp.pacient_id
            JOIN users u ON e.patient_id = u.id
            WHERE mp.medic_id = ? 
            ORDER BY e.created_at DESC
        """, (user_db_id,))
    elif user_role == 'admin':
        # Adminul le vede pe toate
        cursor.execute("""
            SELECT e.id, e.filename, e.original_text, e.summary, e.language, e.translated_text, e.translated_summary, u.full_name
            FROM ehr_records e
            JOIN users u ON e.patient_id = u.id
            ORDER BY e.created_at DESC
        """)
    else:
        # Pacientul își vede doar propriile fișe
        cursor.execute("""
            SELECT e.id, e.filename, e.original_text, e.summary, e.language, e.translated_text, e.translated_summary, u.full_name
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
            "patient_name": row[7] # Aducem și numele pacientului către Angular!
        })
    return records

@router.get("/api/ehr/patient/{target_patient_id}")
async def get_patient_records(target_patient_id: int):
    # Această funcție este folosită de Medic pentru a vedea fișele pacientului său
    try:
        cursor.execute("""
            SELECT id, filename, original_text, summary, language, translated_text, translated_summary 
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
                "translated_summary": row[6]
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

@router.post("/chat")
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