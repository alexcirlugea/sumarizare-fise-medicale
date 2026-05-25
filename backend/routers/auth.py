from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from database import conn, cursor

router = APIRouter()

# Structura datelor pe care le primim de la Angular
class UserSyncRequest(BaseModel):
    uid: str
    email: str
    full_name: str

@router.post("/api/auth/sync")
async def sync_user(user: UserSyncRequest):
    try:
        # Verificăm dacă utilizatorul există deja
        cursor.execute("SELECT id, role FROM users WHERE firebase_uid = ?", (user.uid,))
        existing_user = cursor.fetchone()

        if existing_user:
            return {"message": "Utilizator existent", "role": existing_user[1]}
        
        # Dacă este cont nou, îl introducem în baza de date cu rolul implicit de 'pacient'
        cursor.execute(
            "INSERT INTO users (firebase_uid, email, full_name, role) VALUES (?, ?, ?, 'pacient')",
            (user.uid, user.email, user.full_name)
        )
        conn.commit()
        return {"message": "Utilizator nou creat", "role": "pacient"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

# DTO pentru actualizarea rolului
class RoleUpdateRequest(BaseModel):
    role: str

@router.get("/api/auth/users")
async def get_all_users():
    try:
        cursor.execute("SELECT id, email, full_name, role FROM users ORDER BY id DESC")
        rows = cursor.fetchall()
        users = []
        for row in rows:
            users.append({
                "id": row[0],
                "email": row[1],
                "full_name": row[2],
                "role": row[3]
            })
        return users
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/api/auth/users/{user_id}/role")
async def update_user_role(user_id: int, req: RoleUpdateRequest):
    try:
        if req.role not in ['admin', 'medic', 'pacient']:
            raise HTTPException(status_code=400, detail="Rol invalid")
            
        cursor.execute("UPDATE users SET role = ? WHERE id = ?", (req.role, user_id))
        conn.commit()
        return {"message": "Rol actualizat cu succes"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.delete("/api/auth/users/{user_id}")
async def delete_user(user_id: int):
    try:
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        return {"message": "Utilizator șters cu succes"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))