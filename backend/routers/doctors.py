from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from database import conn, cursor

router = APIRouter()

class LinkPatientRequest(BaseModel):
    doctor_uid: str
    patient_email: str

@router.post("/api/doctors/link-patient")
async def link_patient(req: LinkPatientRequest):
    try:
        # 1. Găsim medicul în baza de date folosind UID-ul de la Firebase
        cursor.execute("SELECT id, role FROM users WHERE firebase_uid = ?", (req.doctor_uid,))
        doctor = cursor.fetchone()
        
        if not doctor or doctor[1] != 'medic':
            raise HTTPException(status_code=403, detail="Doar un medic logat poate asocia pacienți.")
        doctor_id = doctor[0]

        # 2. Căutăm pacientul după email
        cursor.execute("SELECT id, role, full_name FROM users WHERE email = ?", (req.patient_email,))
        patient = cursor.fetchone()
        
        if not patient:
            raise HTTPException(status_code=404, detail="Nu s-a găsit niciun cont cu acest email.")
        if patient[1] != 'pacient':
            raise HTTPException(status_code=400, detail="Adresa de email specificată nu aparține unui pacient.")
        
        patient_id = patient[0]
        patient_name = patient[2]

        # 3. Verificăm dacă nu cumva sunt deja asociați
        cursor.execute("SELECT * FROM medic_pacient WHERE medic_id = ? AND pacient_id = ?", (doctor_id, patient_id))
        if cursor.fetchone():
            return {"message": f"Pacientul {patient_name} este deja în lista ta."}

        # 4. Inserăm legătura
        cursor.execute("INSERT INTO medic_pacient (medic_id, pacient_id) VALUES (?, ?)", (doctor_id, patient_id))
        conn.commit()

        return {"message": f"Pacientul {patient_name} a fost adăugat cu succes în dosarele tale!"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/doctors/{doctor_uid}/patients")
async def get_my_patients(doctor_uid: str):
    try:
        # Aflăm ID-ul medicului
        cursor.execute("SELECT id FROM users WHERE firebase_uid = ?", (doctor_uid,))
        doctor = cursor.fetchone()
        if not doctor:
            raise HTTPException(status_code=404, detail="Medic inexistent.")
        doctor_id = doctor[0]

        # Luăm doar pacienții asociați cu acest medic
        cursor.execute("""
            SELECT u.id, u.email, u.full_name 
            FROM users u
            JOIN medic_pacient mp ON u.id = mp.pacient_id
            WHERE mp.medic_id = ?
        """, (doctor_id,))
        
        rows = cursor.fetchall()
        patients = [{"id": row[0], "email": row[1], "full_name": row[2]} for row in rows]
        
        return patients

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))