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
    """You are a medical specialist. Your task is to analyze the following medical record and extract an accurate clinical summary, exclusively in English.
    
    MEDICAL RECORD TEXT:
    {text}
    
    TASK: Generate the structured summary EXACTLY in this Markdown format:
    - **Reason for Presentation**: 
    - **Medical History**: 
    - **Discharge Diagnosis**: 
    - **Treatment and Interventions**: 
    - **Recommendations**: 
    
    Your response must contain STRICTLY this summary.
    """
)

summary_prompt_ro = ChatPromptTemplate.from_template(
    """Ești un specialist medical. Sarcina ta este să analizezi următoarea fișă medicală și să extragi un rezumat clinic precis, exclusiv în limba ROMÂNĂ.
    
    TEXT FIȘĂ MEDICALĂ:
    {text}
    
    SARCINĂ: Generează rezumatul structurat EXACT în acest format Markdown:
    - **Motivul Prezentării**: 
    - **Istoric Medical**: 
    - **Diagnostic la Externare**: 
    - **Tratament și Intervenții**: 
    - **Recomandări**: 
    
    Răspunsul tău trebuie să conțină STRICT acest rezumat.
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
    """Ești un asistent medical inteligent și un traducător medical expert. Răspunde la întrebarea utilizatorului folosind STRICT informațiile din fișele medicale de mai jos. 
    Dacă răspunsul nu se află în fișe, spune clar că nu ai aceste informații. Nu inventa.

    FIȘELE MEDICALE ÎNCĂRCATE PÂNĂ ACUM:
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