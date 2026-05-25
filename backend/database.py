import os
import sqlite3

# Calea către baza de date
DB_PATH = os.path.join(os.path.dirname(__file__), "ehr_database.db")

# Conexiunea globală
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cursor = conn.cursor()

def init_db():
    """Funcție care se rulează la pornirea aplicației pentru a asigura tabelele."""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            firebase_uid TEXT UNIQUE,
            email TEXT UNIQUE,
            full_name TEXT,
            role TEXT CHECK(role IN ('admin', 'medic', 'pacient')) NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS medic_pacient (
            medic_id INTEGER,
            pacient_id INTEGER,
            PRIMARY KEY (medic_id, pacient_id),
            FOREIGN KEY (medic_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (pacient_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ehr_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER,
            filename TEXT,
            original_text TEXT,
            summary TEXT,
            file_hash TEXT,
            language TEXT,
            translated_text TEXT,
            translated_summary TEXT,
            specialty TEXT,
            diagnosis TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    conn.commit()
    print("✅ Baza de date a fost inițializată cu succes.")