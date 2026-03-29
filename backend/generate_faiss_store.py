from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os

loader = TextLoader(os.path.join(os.path.dirname(__file__), "fisa_medicala.txt"), encoding="utf-8")
docs = loader.load()

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    length_function=len,
)
splits = text_splitter.split_documents(docs)

print("Creating embeddings with Ollama...")
embeddings = OllamaEmbeddings(
    model="nomic-embed-text",
    base_url="http://localhost:11434"
)
vectorstore = FAISS.from_documents(splits, embeddings)
vectorstore.save_local(os.path.join(os.path.dirname(__file__), "faiss_index"))
