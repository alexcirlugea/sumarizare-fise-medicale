# backend/chains/router.py
import json
from pydantic import BaseModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from .llm import llm_fast

# Keyword detection for aggregate queries (Romanian and English)
AGGREGATE_KEYWORDS = [
    "câte", "câţi", "cât", "de câţi", "de câte", "număr", "cât de des",
    "frecvență", "total", "sumă", "media", "medie", "maxim", "minim",
    "count", "sum", "average", "max", "min",
    "cel mai frecvent", "cel mai des", "diagnostic cel mai frecvent", "diagnostic predominant",
    "cel mai comun", "cât de des", "câte înregistrări", "câte fișe", "cât de des apare"
]

def force_sql_intent_if_aggregate(message: str) -> str | None:
    lowered = message.lower()
    for kw in AGGREGATE_KEYWORDS:
        if kw in lowered:
            return "INTENT_B"
    return None

class RouterResponse(BaseModel):
    intent: str
    confidence: float

router_prompt = ChatPromptTemplate.from_template(
    """Ești un router de clasificare a întrebărilor utilizatorilor pentru un asistent medical.
Trebuie să clasifici întrebarea utilizatorului în una din următoarele categorii:

- INTENT_A (RAG / Căutare Semantică): Întrebări clinice specifice despre istoricul medical al unui pacient, simptome, tratamente, recomandări din fișe, sau interpretări de analize. Ex: \"Ce simptome a avut pacientul?\", \"Ce tratament i s-a recomandat?\", \"Sintetizează istoricul lui\".
- INTENT_B (Text-to-SQL / Analitic): Întrebări care necesită agregări, numărători, statistici globale sau liste de fișiere/pacienți care îndeplinesc anumite condiții structurate. Ex: \"Câți pacienți au diagnosticul de diabet?\", \"Câte fișe medicale avem în sistem?\", \"Afișează pacienții asociați cu Cardiologia\".

Răspunde STRICT în format JSON, cu următoarele chei:
- "intent": "INTENT_A" sau "INTENT_B"
- "confidence": scor float între 0.0 și 1.0 reprezentând certitudinea clasificării.

Exemplu de răspuns valid:
{{"intent": "INTENT_B", "confidence": 0.95}}

ÎNTREBARE: {question}
RĂSPUNS JSON:
"""
)

chain_router_raw = router_prompt | llm_fast | StrOutputParser()

class RouterWrapper:
    def invoke(self, inputs: dict) -> RouterResponse:
        try:
            raw = chain_router_raw.invoke(inputs).strip()
            if raw.startswith("```"):
                raw = raw.replace("```json", "").replace("```", "").strip()
            data = json.loads(raw)
            return RouterResponse(
                intent=data.get("intent", "INTENT_A"),
                confidence=data.get("confidence", 0.5)
            )
        except Exception as e:
            print(f"❌ Eroare la parsarea intentului: {e}")
            return RouterResponse(intent="INTENT_A", confidence=1.0)

chain_router = RouterWrapper()
