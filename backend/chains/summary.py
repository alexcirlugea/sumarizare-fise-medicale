from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from .llm import llm


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


chain_summary = summary_prompt | llm | StrOutputParser()
chain_summary_ro = summary_prompt_ro | llm | StrOutputParser()
chain_translate = translate_prompt | llm | StrOutputParser()
chain_chat = chat_prompt | llm | StrOutputParser()