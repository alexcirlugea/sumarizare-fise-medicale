import re
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq
from lingua import Language, LanguageDetectorBuilder

load_dotenv()

# --- Configurare Detecție Limbă ---
detector = LanguageDetectorBuilder.from_languages(
    Language.ROMANIAN, Language.ENGLISH, Language.FRENCH, Language.GERMAN
).build()

# --- Configurare LLM ---
llm = ChatGroq(
    model="llama-3.3-70b-versatile", 
    temperature=0.1, 
)

# --- Prompts ---
summary_prompt = ChatPromptTemplate.from_template(
    """You are an expert medical specialist. Your task is to analyze the following medical record and extract an accurate, comprehensive clinical summary, exclusively in English.

    INSTRUCTIONS:
    1. Extract all available data to fulfill the categories below.
    2. Handle Anonymization: If specific information (like age or dates) is completely anonymized (e.g., `___`) or missing, state "Not specified in the record" or provide a generic description (e.g., "Adult male"). Do NOT hallucinate data.
    3. Consolidate Medications: Group generic and trade names to avoid redundancy. Ensure all discharge medications and their exact dosages/frequencies are listed.
    4. Avoid Over-generalization: Do NOT over-generalize critical clinical events. You MUST explicitly mention specific mechanisms of injury, active self-harm/suicide plans (e.g., "cut left wrist", "plan to use a knife"), specific vital sign anomalies, or key negative/positive findings.
    5. Formatting Rule: Use NESTED BULLET POINTS for every single section. Break down information into short, easily scannable distinct ideas rather than dense paragraphs.

    MEDICAL RECORD TEXT:
    {text}

    TASK: Generate the structured summary EXACTLY in this Markdown format:

    - **Patient Profile**:
      - [Extract available demographics (e.g., sex, age)]
    - **Reason for Presentation**:
      - [Chief complaint and symptom onset]
      - [Specific mechanism of injury/illness, including precise details of self-harm if applicable]
      - [Context of admission and initial clinical suspicions/ruled-out conditions]
    - **Medical History**:
      - [Past medical history (PMH)]
      - [Past surgical history (PSH)]
      - [Relevant family and social history]
      - [Allergies]
    - **Discharge Diagnosis**:
      - [Primary discharge diagnosis]
      - [Secondary diagnoses]
      - *(IMPORTANT: Do NOT repeat past surgical history here unless the surgery was performed during this specific admission.)*
    - **Treatment and Interventions**:
      - [Acute hospital management (e.g., blood transfusions, IV fluids, acute symptom control), procedures, surgeries, or specialist consultations (note if refused/aborted)]
      - [Discharge medications with exact dosages and frequencies]
    - **Recommendations**:
      - [Discharge disposition (where the patient was sent)]
      - [Specific precautions, red flag warnings, or activity restrictions]
      - [Follow-up appointments and instructions]

    Your response must contain STRICTLY the Markdown list above, with no introductory or concluding text. Replace the bracketed placeholders with actual bullet points based on the text.
    """
)

summary_prompt_ro = ChatPromptTemplate.from_template(
    """Ești un medic specialist expert. Sarcina ta este să analizezi următoarea fișă medicală și să extragi un rezumat clinic precis și cuprinzător, exclusiv în limba română.

    INSTRUCȚIUNI:
    1. Extrage toate datele disponibile pentru a completa categoriile de mai jos.
    2. Gestionarea Anonimizării: Dacă anumite informații (precum vârsta sau datele calendaristice) sunt complet anonimizate (ex. `___`) sau lipsesc, specifică "Nu este specificat în fișă" sau oferă o descriere generică (ex. "Bărbat adult"). NU inventa/halucina date.
    3. Consolidarea Medicației: Grupează denumirile generice și comerciale pentru a evita redundanța. Asigură-te că sunt listate toate medicamentele la externare, împreună cu dozele și frecvența exactă.
    4. Evită Supra-generalizarea: NU generaliza excesiv evenimentele clinice critice. TREBUIE să menționezi explicit mecanismele specifice de vătămare, planurile active de auto-vătămare/suicid (ex. "tăietură la încheietura stângă", "plan de a folosi un cuțit"), anomaliile specifice ale semnelor vitale sau constatările pozitive/negative cheie.
    5. Regulă de Formatare: Folosește LISTE CU MARCATORI IMBRICATE (nested bullet points) pentru absolut fiecare secțiune. Împarte informația în idei scurte, distincte și ușor de citit rapid (scannable), evitând paragrafele dense.

    TEXTUL FIȘEI MEDICALE:
    {text}

    SARCINĂ: Generează rezumatul structurat EXACT în acest format Markdown:

    - **Profilul Pacientului**:
      - [Extrage datele demografice disponibile (ex. sex, vârstă)]
    - **Motivul Prezentării**:
      - [Acuza principală și debutul simptomelor]
      - [Mecanismul specific de vătămare/boală, inclusiv detalii precise despre auto-vătămare, dacă este cazul]
      - [Contextul internării și suspiciunile clinice inițiale / afecțiunile excluse]
    - **Istoric Medical**:
      - [Antecedente personale patologice (boli anterioare)]
      - [Antecedente chirurgicale]
      - [Istoric familial și social relevant]
      - [Alergii]
    - **Diagnosticul la Externare**:
      - [Diagnosticul principal la externare]
      - [Diagnostice secundare]
      - *(IMPORTANT: NU repeta istoricul chirurgical aici decât dacă intervenția a fost efectuată în timpul acestei internări specifice.)*
    - **Tratament și Intervenții**:
      - [Managementul spitalicesc acut (ex. transfuzii de sânge, fluide IV, controlul acut al simptomelor), proceduri, operații sau consulturi de specialitate (menționează dacă au fost refuzate/anulate)]
      - [Medicația la externare cu dozele și frecvențele exacte]
    - **Recomandări**:
      - [Destinația la externare (unde a fost trimis pacientul: acasă, centru de îngrijire, etc.)]
      - [Precauții specifice, semnale de alarmă sau restricții de activitate]
      - [Programări pentru control și instrucțiuni de urmărire]

    Răspunsul tău trebuie să conțină STRICT lista Markdown de mai sus, fără niciun text introductiv sau de încheiere. Înlocuiește textele între paranteze drepte cu puncte de tip bullet bazate pe textul fișei.
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
    """Ești un asistent medical AI avansat și obiectiv. Rolul tău este să răspunzi la întrebările utilizatorului folosind STRICT informațiile din fișele medicale de mai jos.

    REGULI STRICTE DE FUNCȚIONARE:
    1. Bazează-te EXCLUSIV pe textul furnizat. Nu inventa date, diagnostice sau tratamente.
    2. RECONCILIEREA DATELOR: Este perfect normal ca fișele să prezinte afecțiuni diferite, vârste diferite sau să aparțină unor pacienți diferiți (mai ales dacă sunt date de test dintr-un set de date public sau selecții făcute de un medic pentru mai mulți pacienți).
       - Tratează fiecare fișă ca pe un caz clinic independent, în propriul său context.
       - NU semnala discrepanțele dintre fișe ca fiind erori sau confuzii (ex: "vârstele nu se potrivesc").
       - Când extragi informații, citează întotdeauna fișierul sursă și pacientul (ex: "Conform fișei X a pacientului Y...").
    3. RĂSPUNSURI GENERALE: Dacă utilizatorul pune o întrebare vagă (ex: 'Ce poți să-mi spui despre aceste fișe?', 'Fă un rezumat'), NU refuza să răspunzi și NU cere clarificări. Oferă direct un sumar structurat pentru FIECARE fișier din context (Pacient, Diagnostic principal, Detalii cheie).

    FIȘELE MEDICALE ÎNCĂRCATE PÂNĂ ACUM (CONTEXT):
    {context}

    ÎNTREBAREA UTILIZATORULUI:
    {question}
    """
)
# --- Chains ---
chain_summary = summary_prompt | llm | StrOutputParser()
chain_summary_ro = summary_prompt_ro | llm | StrOutputParser()
chain_translate = translate_prompt | llm | StrOutputParser()
chain_chat = chat_prompt | llm | StrOutputParser()

# --- Dicționar de Mapare Specialități Medicale ---
SPECIALTY_MAPPING = {
    # Limba Engleză / Coduri internaționale
    "MEDICINE": "Medicină Internă",
    "MEDICINA": "Medicină Internă",
    "INTERNE": "Medicină Internă",
    "ENT": "Otorinolaringologie",
    "ORL": "Otorinolaringologie",
    "CARDIOLOGY": "Cardiologie",
    "CARDIO": "Cardiologie",
    "NEUROLOGY": "Neurologie",
    "NEURO": "Neurologie",
    "PSYCHIATRY": "Psihiatrie",
    "PSYCH": "Psihiatrie",
    "SURGERY": "Chirurgie Generală",
    "CHIRURGIE": "Chirurgie Generală",
    "PEDIATRICS": "Pediatrie",
    "PEDIATRIE": "Pediatrie",
    "DERMATOLOGY": "Dermatovenerologie",
    "DERMATO": "Dermatovenerologie",
    "ONCOLOGY": "Oncologie Medicală",
    "ONCO": "Oncologie Medicală",
    "ORTHOPEDICS": "Ortopedie și Traumatologie",
    "ORTHO": "Ortopedie și Traumatologie",
    "OBSTETRICS": "Obstetrică-Ginecologie",
    "GYNECOLOGY": "Obstetrică-Ginecologie",
    "GINECO": "Obstetrică-Ginecologie",
    "OPHTHALMOLOGY": "Oftalmologie",
    "OFTALMO": "Oftalmologie",
    "UROLOGY": "Urologie",
    "URO": "Urologie",
    "GASTROENTEROLOGY": "Gastroenterologie",
    "GASTRO": "Gastroenterologie",
    "PULMONOLOGY": "Pneumologie",
    "PNEUMO": "Pneumologie",
    "ENDOCRINOLOGY": "Endocrinologie",
    "ENDOCRINO": "Endocrinologie",
    "DIABETES": "Diabet, Nutriție și Boli Metabolice",
    "DIABET": "Diabet, Nutriție și Boli Metabolice",
    "NEPHROLOGY": "Nefrologie",
    "NEFRO": "Nefrologie",
    "RHEUMATOLOGY": "Reumatologie",
    "REUMATO": "Reumatologie",
    "ALLERGY": "Alergologie și Imunologie Clinică",
    "ALERGOLOGIE": "Alergologie și Imunologie Clinică",
    "INFECTIOUS": "Boli Infecțioase",
    "INFECTIOASE": "Boli Infecțioase",
    "HEMATOLOGY": "Hematologie",
    "HEMATO": "Hematologie",
    "ANESTHESIOLOGY": "Anestezie și Terapie Intensivă",
    "ATI": "Anestezie și Terapie Intensivă",
    "RADIOLOGY": "Radiologie și Imagistică Medicală",
    "RADIOLOGIE": "Radiologie și Imagistică Medicală",
    "EMERGENCY": "Medicină de Urgență",
    "URGENTE": "Medicină de Urgență",
    "UPU": "Medicină de Urgență",
}

# --- Prompts pentru Specialități ---
specialty_translate_prompt = ChatPromptTemplate.from_template(
    """You are a medical localization expert. Translate/map this medical specialty code/term from English to its official Romanian medical specialty name:
    '{raw_specialty}'
    
    Respond with ONLY the official Romanian specialty name (e.g., "Medicină Internă", "Otorinolaringologie", "Cardiologie", "Psihiatrie"). Do not include any other text, explanation, or punctuation.
    """
)

specialty_standardize_prompt = ChatPromptTemplate.from_template(
    """Ești un expert în nomenclatura medicală din România. Standardizează următoarea denumire/prescurtare medicală în denumirea oficială a specialității medicale în limba română:
    '{raw_specialty}'
    
    Răspunde DOAR cu numele oficial al specialității (de exemplu: "Cardiologie", "Neurologie", "Psihiatrie", "Medicină Internă"). Nu include niciun alt text explicativ sau semne de punctuație suplimentare.
    """
)

specialty_extract_doc_prompt = ChatPromptTemplate.from_template(
    """Ești un expert medical. Analizează textul următoarei fișe medicale și identifică specialitatea medicală (secția sau serviciul clinic) căreia îi aparține acest caz.
    
    FIȘA MEDICALĂ:
    {text}
    
    Răspunde DOAR cu denumirea oficială în limba română a specialității medicale identificate (de exemplu: "Cardiologie", "Psihiatrie", "Neurologie", "Medicină Internă"). Nu include introduceri, explicații sau alte cuvinte.
    """
)

# --- Chains pentru Specialități ---
chain_specialty_translate = specialty_translate_prompt | llm | StrOutputParser()
chain_specialty_standardize = specialty_standardize_prompt | llm | StrOutputParser()
chain_specialty_extract_doc = specialty_extract_doc_prompt | llm | StrOutputParser()

# --- Funcții de extracție și standardizare ---
def extract_specialty_raw(text: str, lang_code: str) -> str:
    if lang_code == "ENGLISH":
        match = re.search(r'<SERVICE>\s*([^<]+)', text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    else:
        match = re.search(r'SERVICIU\s*:\s*([^\n\r]+)', text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return ""

def get_standardized_specialty(text: str, lang_code: str) -> str:
    raw = extract_specialty_raw(text, lang_code)
    
    # Dacă nu am găsit tagul în text, apelăm LLM pentru determinarea specialității pe baza întregului document
    if not raw:
        try:
            print("🔍 Nu s-a găsit tag de serviciu, se apelează LLM pentru determinarea specialității...")
            extracted_from_doc = chain_specialty_extract_doc.invoke({"text": text})
            raw = extracted_from_doc.strip()
        except Exception as e:
            print(f"❌ Eroare la extragerea specialității cu LLM: {e}")
            return "Nespecificat"
            
    # Curățăm textul extras
    raw_clean = raw.strip()
    raw_upper = raw_clean.upper()
    
    # 1. Căutăm în CHEILE dicționarului (abrevieri/denumiri standardizate)
    if raw_upper in SPECIALTY_MAPPING:
        return SPECIALTY_MAPPING[raw_upper]
        
    # 2. Verificăm dacă textul extras este deja printre VALORILE dicționarului (caz insensitiv)
    for official_name in SPECIALTY_MAPPING.values():
        if raw_clean.lower() == official_name.lower():
            return official_name
            
    # 3. Fallback la LLM
    try:
        if lang_code == "ENGLISH":
            print(f"🌐 Apel LLM pentru traducere specialitate din engleză: '{raw_clean}'")
            llm_result = chain_specialty_translate.invoke({"raw_specialty": raw_clean})
        else:
            print(f"🌐 Apel LLM pentru standardizare specialitate română: '{raw_clean}'")
            llm_result = chain_specialty_standardize.invoke({"raw_specialty": raw_clean})
            
        result_clean = llm_result.strip().strip('"').strip("'").strip(".")
        
        # Verificare secundară în valori în caz de diferențe de caz/spații
        for official_name in SPECIALTY_MAPPING.values():
            if result_clean.lower() == official_name.lower():
                return official_name
                
        return result_clean if result_clean else "Nespecificat"
    except Exception as e:
        print(f"❌ Eroare în fallback-ul LLM de standardizare: {e}")
        return raw_clean if raw_clean else "Nespecificat"


# --- Prompts pentru Diagnostic ---
diagnosis_translate_prompt = ChatPromptTemplate.from_template(
    """You are a medical translation expert. Translate this discharge diagnosis from English to its standard medical Romanian equivalent:
    '{raw_diagnosis}'
    
    Respond with ONLY the Romanian translation, keeping it concise and clinical (e.g., 'Ascită secundară hipertensiunii portale', 'Ciroză hepatică'). Do not include explanation, introduction, or punctuation.
    """
)

diagnosis_standardize_prompt = ChatPromptTemplate.from_template(
    """Ești un expert medical. Analizează următoarele diagnostice medicale din fișă și extrage/standardizează doar DIAGNOSTICUL PRINCIPAL la externare într-o formă scurtă, clară și corectă:
    '{raw_diagnosis}'
    
    Răspunde DOAR cu denumirea diagnosticului principal (de exemplu: 'Tulburare depresivă majoră', 'Infarct miocardic acut'). Nu include explicații sau text adițional.
    """
)

diagnosis_extract_doc_prompt = ChatPromptTemplate.from_template(
    """Ești un expert medical. Analizează textul următoarei fișe medicale și identifică DIAGNOSTICUL PRINCIPAL la externare (în limba română).
    
    FIȘA MEDICALĂ:
    {text}
    
    Răspunde DOAR cu denumirea oficială a diagnosticului identificat (de exemplu: 'Pneumonie bacteriană', 'Ciroză hepatică'). Nu include introduceri sau alte comentarii.
    """
)

# --- Chains pentru Diagnostic ---
chain_diagnosis_translate = diagnosis_translate_prompt | llm | StrOutputParser()
chain_diagnosis_standardize = diagnosis_standardize_prompt | llm | StrOutputParser()
chain_diagnosis_extract_doc = diagnosis_extract_doc_prompt | llm | StrOutputParser()

# --- Funcții pentru Diagnostic ---
def extract_diagnosis_raw(text: str, lang_code: str) -> str:
    if lang_code == "ENGLISH":
        match = re.search(r'<DISCHARGE DIAGNOSIS>\s*([^<]+)', text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    else:
        # Extragem tot ce e după DIAGNOSTIC: până la următoarea secțiune majoră
        match = re.search(r'DIAGNOSTIC\s*:\s*(.+?)(?=\n\s*(?:STARE LA EXTERNARE|DISPOZIȚIE|RECOMANDĂRI|INSTRUCTIUNI|LABORATOR|STATUS MENTAL|$))', text, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()
        
        match_simple = re.search(r'DIAGNOSTIC\s*:\s*([^\n\r]+)', text, re.IGNORECASE)
        if match_simple:
            return match_simple.group(1).strip()
    return ""

def clean_diagnosis_output(text: str) -> str:
    cleaned = text.strip().strip('"').strip("'").strip(".")
    lines = [line.strip().strip('-').strip('*').strip() for line in cleaned.split('\n') if line.strip()]
    if lines:
        cleaned = lines[0]
        
    # Eliminăm prefixe repetitive
    prefixes = [
        "diagnostic primar:",
        "diagnostic principal:",
        "primary diagnosis:",
        "diagnosis:",
        "primary:",
        "diagnosticul principal:"
    ]
    
    changed = True
    while changed:
        changed = False
        cleaned_lower = cleaned.lower()
        for pref in prefixes:
            if cleaned_lower.startswith(pref):
                cleaned = cleaned[len(pref):].strip()
                changed = True
                break
                
    if cleaned:
        cleaned = cleaned[0].upper() + cleaned[1:]
    return cleaned

def get_standardized_diagnosis(text: str, lang_code: str) -> str:
    raw = extract_diagnosis_raw(text, lang_code)
    
    if not raw:
        try:
            print("🔍 Nu s-a găsit tag de diagnostic, se apelează LLM pentru determinarea diagnosticului...")
            extracted_from_doc = chain_diagnosis_extract_doc.invoke({"text": text})
            return clean_diagnosis_output(extracted_from_doc)
        except Exception as e:
            print(f"❌ Eroare la extragerea diagnosticului cu LLM: {e}")
            return "Nespecificat"
            
    raw_clean = raw.strip()
    
    try:
        if lang_code == "ENGLISH":
            print(f"🌐 Apel LLM pentru traducere diagnostic din engleză: '{raw_clean}'")
            llm_result = chain_diagnosis_translate.invoke({"raw_diagnosis": raw_clean})
        else:
            print(f"🌐 Apel LLM pentru standardizare diagnostic română: '{raw_clean}'")
            llm_result = chain_diagnosis_standardize.invoke({"raw_diagnosis": raw_clean})
            
        return clean_diagnosis_output(llm_result)
    except Exception as e:
        print(f"❌ Eroare în fallback-ul LLM de diagnostic: {e}")
        return clean_diagnosis_output(raw_clean) if raw_clean else "Nespecificat"