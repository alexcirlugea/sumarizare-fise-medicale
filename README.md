# Medical Summary & RAG Service

## Prezentare generală

Acest repository implementează un **serviciu de rezumat și căutare augmentată (RAG) a fișelor medicale** folosind **FastAPI** și **LangChain**. Backend‑ul furnizează endpoint‑uri pentru:
- Încărcarea fișierelor `.txt` și `.pdf` ale fișelor medicale.
- Rezumat și traducere automată (română ↔ engleză).
- Extracție și standardizare a specialităților și diagnosticului.
- Căutare semantică în fișele încărcate cu ajutorul unui vector store Chroma.
- Rutare a intenției (RAG vs. Text‑to‑SQL) alimentată de un LLM rapid.
- Chat medical cu rutare automată între căutare semantică RAG și întrebări analitice Text‑to‑SQL.

Codul este **modularizat**: toată logica legată de LLM se găsește în `backend/chains/` (configurare LLM, rezumare, meta‑date, utilitare Chroma, router și lanțuri SQL). Router‑ele FastAPI orchestrează aceste componente reutilizabile.

---

## Diagrama arhitecturii

```
frontend (Angular)  <-- HTTP -->  FastAPI (backend)
    |
    ├─ routers/ehr.py (upload, rezumat, traducere)
    ├─ chains/
    │    ├─ llm.py               # LLM & detector limbă
    │    ├─ summary.py           # Prompturi & lanțuri de rezumare
    │    ├─ metadata.py          # Helper‑uri pentru specialități/diagnostice
    │    ├─ chroma.py            # Vector store & utilitare RAG
    │    ├─ router.py            # Clasificare intenție
    │    └─ sql.py               # Generare Text‑to‑SQL & corecție
    ├─ database.py            # Persistență SQLite
    └─ (frontend Angular) medical-summary-app/  # autentificare, upload, listare, traducere, chat
```

---

## Cerințe preliminare

- **Python 3.12+** (recomandat 3.13).
- **Node.js 18+** & **npm** pentru interfața Angular (opțională).
- **Cheie API Groq** – necesară pentru LLM. Înregistrează‑te la https://groq.com/ și obține `GROQ_API_KEY`.

---

## Instalare

```bash
# 1. Clonează repository‑ul
git clone https://github.com/AlexCirlugea/sumarizare-fise-medicale.git
cd summarizare-fise-medicale

# 2. Crează un mediu virtual (recomandat)
python -m venv .venv
.\\.venv\\Scripts\\activate   # Windows
# source .venv/bin/activate       # macOS/Linux

# 3. Instalează dependențele backend‑ului
pip install -r backend/requirements.txt
```

### Interfață Angular (opțional)

```bash
cd medical-summary-app
npm install
npm start   # sau: ng serve
```

Aplicația va fi disponibilă la `http://localhost:4200`.

---

## Configurare (variabile de mediu)

Creează un fișier **`.env`** în folderul `backend/`:

```dotenv
GROQ_API_KEY=cheia_ta_groq_aici
```

Aceste variabile sunt încărcate cu `python‑dotenv`.

---

## Rulare locală a serviciului backend

```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

- API‑ul este accesibil la `http://localhost:8000`.
- Documentația Swagger UI se găsește la `http://localhost:8000/docs`.
- Documentația Redoc la `http://localhost:8000/redoc`.

---

## Exemple de flux de lucru

1. **Încarcă un PDF sau un fișier .txt** prin endpoint‑ul `/upload-summary` (folosind Swagger UI sau `curl`).
2. Fișierul este hash‑at, stocat și textul său este extras.
3. Lanțul de rezumare **generează rezumatul în funcție de limba detectată și permite traducerea ulterioară**.
4. Textul este fragmentat, încorporat și indexat în ChromaDB local (`backend/chroma_db`).
5. Ulterior poți interoga serviciul prin:
    - `/chat` – interfață de chat care decide automat dacă să folosească RAG sau Text‑to‑SQL.

---

## Date sensibile

Nu include în repository:
- `backend/.env`
- `backend/ehr_database.db`
- `backend/chroma_db/`
- fișiere medicale reale sau date personale.

---

## Contribuții

1. Fork-uiește repository‑ul.
2. Creează o ramură pentru funcționalitatea ta:
   ```bash
   git checkout -b feature/my-feature
   ```
3. Realizează modificările și asigură‑te că aplicația funcționează.
4. Folosește **conventional commits** pentru mesaje (ex.: `feat: adaugă endpoint nou`, `fix: corectează calea import`).
5. Trimite un Pull Request.

---
