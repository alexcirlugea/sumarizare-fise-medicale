import re

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from .llm import llm


SPECIALTY_MAPPING = {
    "MEDICINE": "Medicina Interna",
    "MEDICINA": "Medicina Interna",
    "INTERNE": "Medicina Interna",
    "ENT": "Otorinolaringologie",
    "ORL": "Otorinolaringologie",
    "CARDIOLOGY": "Cardiologie",
    "CARDIO": "Cardiologie",
    "NEUROLOGY": "Neurologie",
    "NEURO": "Neurologie",
    "PSYCHIATRY": "Psihiatrie",
    "PSYCH": "Psihiatrie",
    "SURGERY": "Chirurgie Generala",
    "CHIRURGIE": "Chirurgie Generala",
    "PEDIATRICS": "Pediatrie",
    "PEDIATRIE": "Pediatrie",
    "DERMATOLOGY": "Dermatovenerologie",
    "DERMATO": "Dermatovenerologie",
    "ONCOLOGY": "Oncologie Medicala",
    "ONCO": "Oncologie Medicala",
    "ORTHOPEDICS": "Ortopedie si Traumatologie",
    "ORTHO": "Ortopedie si Traumatologie",
    "OBSTETRICS": "Obstetrica-Ginecologie",
    "GYNECOLOGY": "Obstetrica-Ginecologie",
    "GINECO": "Obstetrica-Ginecologie",
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
    "DIABETES": "Diabet, Nutritie si Boli Metabolice",
    "DIABET": "Diabet, Nutritie si Boli Metabolice",
    "NEPHROLOGY": "Nefrologie",
    "NEFRO": "Nefrologie",
    "RHEUMATOLOGY": "Reumatologie",
    "REUMATO": "Reumatologie",
    "ALLERGY": "Alergologie si Imunologie Clinica",
    "ALERGOLOGIE": "Alergologie si Imunologie Clinica",
    "INFECTIOUS": "Boli Infectioase",
    "INFECTIOASE": "Boli Infectioase",
    "HEMATOLOGY": "Hematologie",
    "HEMATO": "Hematologie",
    "ANESTHESIOLOGY": "Anestezie si Terapie Intensiva",
    "ATI": "Anestezie si Terapie Intensiva",
    "RADIOLOGY": "Radiologie si Imagistica Medicala",
    "RADIOLOGIE": "Radiologie si Imagistica Medicala",
    "EMERGENCY": "Medicina de Urgenta",
    "URGENTE": "Medicina de Urgenta",
    "UPU": "Medicina de Urgenta",
}


specialty_translate_prompt = ChatPromptTemplate.from_template(
    """You are a medical localization expert. Translate/map this medical specialty code/term from English to its official Romanian medical specialty name:
    '{raw_specialty}'

    Respond with ONLY the official Romanian specialty name. Do not include any other text, explanation, or punctuation.
    """
)

specialty_standardize_prompt = ChatPromptTemplate.from_template(
    """Esti un expert in nomenclatura medicala din Romania. Standardizeaza urmatoarea denumire/prescurtare medicala in denumirea oficiala a specialitatii medicale in limba romana:
    '{raw_specialty}'

    Raspunde DOAR cu numele oficial al specialitatii. Nu include niciun alt text explicativ sau semne de punctuatie suplimentare.
    """
)

specialty_extract_doc_prompt = ChatPromptTemplate.from_template(
    """Esti un expert medical. Analizeaza textul urmatoarei fise medicale si identifica specialitatea medicala, sectia sau serviciul clinic caruia ii apartine acest caz.

    FISA MEDICALA:
    {text}

    Raspunde DOAR cu denumirea oficiala in limba romana a specialitatii medicale identificate. Nu include introduceri, explicatii sau alte cuvinte.
    """
)

chain_specialty_translate = specialty_translate_prompt | llm | StrOutputParser()
chain_specialty_standardize = specialty_standardize_prompt | llm | StrOutputParser()
chain_specialty_extract_doc = specialty_extract_doc_prompt | llm | StrOutputParser()


def extract_specialty_raw(text: str, lang_code: str) -> str:
    if lang_code == "ENGLISH":
        match = re.search(r"<SERVICE>\s*([^<]+)", text, re.IGNORECASE)
        if match:
            return match.group(1).strip()

    match = re.search(r"SERVICIU\s*:\s*([^\n\r]+)", text, re.IGNORECASE)
    if match:
        return match.group(1).strip()

    return ""


def get_standardized_specialty(text: str, lang_code: str) -> str:
    raw = extract_specialty_raw(text, lang_code)

    if not raw:
        try:
            print("Nu s-a gasit tag de serviciu, se apeleaza LLM pentru specialitate...")
            extracted_from_doc = chain_specialty_extract_doc.invoke({"text": text})
            raw = extracted_from_doc.strip()
        except Exception as e:
            print(f"Eroare la extragerea specialitatii cu LLM: {e}")
            return "Nespecificat"

    raw_clean = raw.strip()
    raw_upper = raw_clean.upper()

    if raw_upper in SPECIALTY_MAPPING:
        return SPECIALTY_MAPPING[raw_upper]

    for official_name in SPECIALTY_MAPPING.values():
        if raw_clean.lower() == official_name.lower():
            return official_name

    try:
        if lang_code == "ENGLISH":
            print(f"Apel LLM pentru traducere specialitate din engleza: '{raw_clean}'")
            llm_result = chain_specialty_translate.invoke({"raw_specialty": raw_clean})
        else:
            print(f"Apel LLM pentru standardizare specialitate romana: '{raw_clean}'")
            llm_result = chain_specialty_standardize.invoke({"raw_specialty": raw_clean})

        result_clean = llm_result.strip().strip('"').strip("'").strip(".")

        for official_name in SPECIALTY_MAPPING.values():
            if result_clean.lower() == official_name.lower():
                return official_name

        return result_clean if result_clean else "Nespecificat"
    except Exception as e:
        print(f"Eroare in fallback-ul LLM de standardizare specialitate: {e}")
        return raw_clean if raw_clean else "Nespecificat"


diagnosis_translate_prompt = ChatPromptTemplate.from_template(
    """You are a medical translation expert. Translate this discharge diagnosis from English to its standard medical Romanian equivalent:
'{raw_diagnosis}'

Respond with ONLY the Romanian translation, keeping it concise and clinical. Do not include explanation, introduction, or punctuation.
"""
)

diagnosis_standardize_prompt = ChatPromptTemplate.from_template(
    """Esti un expert medical. Analizeaza urmatoarele diagnostice medicale din fisa si extrage/standardizeaza doar DIAGNOSTICUL PRINCIPAL la externare intr-o forma scurta, clara si corecta:
'{raw_diagnosis}'

Raspunde DOAR cu denumirea diagnosticului principal. Nu include explicatii sau text aditional.
"""
)

diagnosis_extract_doc_prompt = ChatPromptTemplate.from_template(
    """Esti un expert medical. Analizeaza textul urmatoarei fise medicale si identifica DIAGNOSTICUL PRINCIPAL la externare, in limba romana.

FISA MEDICALA:
{text}

Raspunde DOAR cu denumirea oficiala a diagnosticului identificat. Nu include introduceri sau alte comentarii.
"""
)

chain_diagnosis_translate = diagnosis_translate_prompt | llm | StrOutputParser()
chain_diagnosis_standardize = diagnosis_standardize_prompt | llm | StrOutputParser()
chain_diagnosis_extract_doc = diagnosis_extract_doc_prompt | llm | StrOutputParser()


def extract_diagnosis_raw(text: str, lang_code: str) -> str:
    if lang_code == "ENGLISH":
        match = re.search(r"<DISCHARGE DIAGNOSIS>\s*([^<]+)", text, re.IGNORECASE)
        if match:
            return match.group(1).strip()

    match = re.search(
        r"DIAGNOSTIC\s*:\s*(.+?)(?=\n\s*(?:STARE LA EXTERNARE|DISPOZITIE|RECOMANDARI|INSTRUCTIUNI|LABORATOR|STATUS MENTAL|$))",
        text,
        re.IGNORECASE | re.DOTALL,
    )
    if match:
        return match.group(1).strip()

    match_simple = re.search(r"DIAGNOSTIC\s*:\s*([^\n\r]+)", text, re.IGNORECASE)
    if match_simple:
        return match_simple.group(1).strip()

    return ""


def clean_diagnosis_output(text: str) -> str:
    cleaned = text.strip().strip('"').strip("'").strip(".")
    lines = [
        line.strip().strip("-").strip("*").strip()
        for line in cleaned.split("\n")
        if line.strip()
    ]

    if lines:
        cleaned = lines[0]

    prefixes = [
        "diagnostic primar:",
        "diagnostic principal:",
        "primary diagnosis:",
        "diagnosis:",
        "primary:",
        "diagnosticul principal:",
    ]

    changed = True
    while changed:
        changed = False
        cleaned_lower = cleaned.lower()
        for prefix in prefixes:
            if cleaned_lower.startswith(prefix):
                cleaned = cleaned[len(prefix):].strip()
                changed = True
                break

    if cleaned:
        cleaned = cleaned[0].upper() + cleaned[1:]

    return cleaned


def get_standardized_diagnosis(text: str, lang_code: str) -> str:
    raw = extract_diagnosis_raw(text, lang_code)

    if not raw:
        try:
            print("Nu s-a gasit tag de diagnostic, se apeleaza LLM pentru diagnostic...")
            extracted_from_doc = chain_diagnosis_extract_doc.invoke({"text": text})
            return clean_diagnosis_output(extracted_from_doc)
        except Exception as e:
            print(f"Eroare la extragerea diagnosticului cu LLM: {e}")
            return "Nespecificat"

    raw_clean = raw.strip()

    try:
        if lang_code == "ENGLISH":
            print(f"Apel LLM pentru traducere diagnostic din engleza: '{raw_clean}'")
            llm_result = chain_diagnosis_translate.invoke({"raw_diagnosis": raw_clean})
        else:
            print(f"Apel LLM pentru standardizare diagnostic romana: '{raw_clean}'")
            llm_result = chain_diagnosis_standardize.invoke({"raw_diagnosis": raw_clean})

        return clean_diagnosis_output(llm_result)
    except Exception as e:
        print(f"Eroare in fallback-ul LLM de diagnostic: {e}")
        return clean_diagnosis_output(raw_clean) if raw_clean else "Nespecificat"