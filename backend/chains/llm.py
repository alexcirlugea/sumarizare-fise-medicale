from dotenv import load_dotenv
from langchain_groq import ChatGroq
from lingua import Language, LanguageDetectorBuilder


load_dotenv()


detector = LanguageDetectorBuilder.from_languages(
    Language.ROMANIAN,
    Language.ENGLISH,
    Language.FRENCH,
    Language.GERMAN,
).build()


llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.1,
)


llm_fast = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0.1,
)