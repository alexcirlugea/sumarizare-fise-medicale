from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings, OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
import os
import sys

INDEX_TXT_PATH = os.path.join(os.path.dirname(__file__), "faiss_index") # Indexul din TXT
INDEX_PDF_PATH = os.path.join(os.path.dirname(__file__), "faiss_index_pdf") # Indexul din PDF
OLLAMA_MODEL = "llama3.1:8b" 
OLLAMA_BASE_URL = "http://localhost:11434"

# Incărcarea și Unirea IndexuriloE

print("1. Loading embeddings and merging FAISS indexes...")
embeddings = OllamaEmbeddings(
    model="nomic-embed-text",  
    base_url=OLLAMA_BASE_URL
)

def load_and_verify_index(path, name, embeddings):
    try:
        store = FAISS.load_local(
            path, embeddings, allow_dangerous_deserialization=True
        )

        print(f"Indexul '{name}' a fost incarcat cu succes de la: {path}")
        return store
    except Exception as e:
        print(f"EROARE CRITICĂ la incarcarea indexului '{name}' de la {path}.")
        print(f"Eroare detaliată: {e}")
        sys.exit(1)

# Incarca indexul din TXT
vectorstore_txt = load_and_verify_index(INDEX_TXT_PATH, "TXT Index", embeddings)

# Incarca indexul din PDF
vectorstore_pdf = load_and_verify_index(INDEX_PDF_PATH, "PDF Index", embeddings)

# UNESTE CELE DOUA INDEXURI
try:
    vectorstore_txt.merge_from(vectorstore_pdf)  
    vectorstore_combined = vectorstore_txt  
    print("Unirea indexurilor a reusit.")
except Exception as e:
    print(f"EROARE la unirea indexurilor: {e}")
    sys.exit(1)


retriever = vectorstore_combined.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 6} 
)


prompt = ChatPromptTemplate.from_messages([
    ("system", "Ești un specialist în extragerea datelor medicale din MAI MULTE fișe medicale. "
                "Respectă cu strictețe următoarele reguli:\n"
                "1. Folosește EXCLUSIV informațiile din secțiunea 'Context' pentru a răspunde.\n"
                "2. Specifică ÎNTOTDEAUNA despre ce pacient vorbești (nume complet sau identificator clar).\n"
                "3. Extrage și prezintă informațiile relevante: nume pacient, vârstă, diagnostic, simptome, istoric medical, tratament actual, medicație, alergii.\n"
                "4. Când compari sau menționezi mai mulți pacienți, separă clar informațiile pentru fiecare.\n"
                "5. Fii concis și profesionist - răspunde direct, fără introduceri sau concluzii generice.\n"
                "6. Dacă informația solicitată NU există în Context, răspunde clar: 'Această informație nu este disponibilă în fișele medicale.'\n"
                "7. Nu inventa, nu presupune, nu extrapola - doar date exacte din Context.\n"
                "8. Dacă întrebarea nu indică în mod clar la care pacient sau la care fișă se referă, solicită explicit o clarificare înainte de a răspunde."),
    ("human", "Context: {context}\n\nÎntrebare: {question}")
])



print(f"2. Initializing Ollama LLM ({OLLAMA_MODEL})...")
llm = OllamaLLM(
    model=OLLAMA_MODEL,  
    base_url=OLLAMA_BASE_URL,
    temperature=0, 
)

rag_chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)


print("\n--- Chatbot Medical pornit ---")
print("Tastează 'exit' sau 'quit' pentru a parasi chat-ul.")
print("---------------------------------")

while True:
    user_input = input("Intrebarea ta: ")
    if user_input.lower() in ["exit", "quit"]:
        print("Chat-ul a fost inchis. La revedere!")
        break
    
    if user_input.strip() == "":
        continue

    print("\n[Raspuns]:")
    for chunk in rag_chain.stream(user_input):
        print(chunk, end="", flush=True)
    print("\n---------------------------------")