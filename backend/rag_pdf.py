from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings, OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

print("Creating embeddings with Ollama...")
embeddings = OllamaEmbeddings(
    model="nomic-embed-text",  
    base_url="http://localhost:11434"
)
vectorstore = FAISS.load_local(
    "faiss_index_pdf",
    embeddings,
    allow_dangerous_deserialization=True  
)
retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 4}  
)

prompt = ChatPromptTemplate.from_messages([
    ("system", "Ești un asistent medical care analizează fișe medicale. "
               "Folosește doar informațiile din contextul furnizat pentru a răspunde. "
               "Extrage infromatiile relevante: nume, varsta, diagnostic, istoric, tratament, medicatie etc."
               "Dacă informația nu există în context, spune-o clar."),
    ("human", "Context: {context}\n\nÎntrebare: {question}")
])

print("Initializing Ollama LLM...")
llm = OllamaLLM(
    model="llama3.1:8b",  
    base_url="http://localhost:11434",
    temperature=0,
)

rag_chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

query = "Rezumă această fișă medicală în 2-3 fraze."
print(f"\nQuery: {query}\n")
print("Generating response...")

# answer = rag_chain.invoke(query)
# print("\nRăspuns RAG:", answer)

print("\n--- Streaming response ---")
for chunk in rag_chain.stream(query):
    print(chunk, end="", flush=True)
print()
