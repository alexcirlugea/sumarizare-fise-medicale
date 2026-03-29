from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os

pdf_file_path = os.path.join(os.path.dirname(__file__), "fisa_medicala.pdf")

if not os.path.exists(pdf_file_path):
    print(f"Eroare: Fișierul PDF nu a fost găsit la calea: {pdf_file_path}")
    


print(f"Incarcarea documentului din {pdf_file_path}...")
loader = PyPDFLoader(pdf_file_path)
docs = loader.load() 

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    length_function=len,
)
splits = text_splitter.split_documents(docs)
print(f"Documentul a fost împărțit în {len(splits)} fragmente.")

print("Crearea de embeddings cu Ollama...")
embeddings = OllamaEmbeddings(
    model="nomic-embed-text",  
    base_url="http://localhost:11434"
)

vectorstore = FAISS.from_documents(splits, embeddings)

index_path = os.path.join(os.path.dirname(__file__), "faiss_index_pdf") 
vectorstore.save_local(index_path)
print(f"Indexul FAISS a fost salvat local la: {index_path}")