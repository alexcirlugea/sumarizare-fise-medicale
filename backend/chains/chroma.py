# backend/chains/chroma.py
import os
import json
from typing import List, Dict, Optional
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_groq import ChatGroq

# Fast LLM for classification (if needed elsewhere)
llm_fast = ChatGroq(model="llama-3.1-8b-instant", temperature=0.1)

# Initialize Vector Store
CHROMA_DIR = os.path.join(os.path.dirname(__file__), "..", "ai_service", "chroma_db")
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
vector_store = Chroma(collection_name="ehr_chunks", embedding_function=embeddings, persist_directory=CHROMA_DIR)

# Helper to chunk and embed a document
def chunk_and_embed_document(patient_id: int, record_id: int, specialty: str, filename: str, text: str):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_text(text)
    metadatas = [{"patient_id": patient_id, "record_id": record_id, "specialty": specialty, "filename": filename} for _ in chunks]
    vector_store.add_texts(texts=chunks, metadatas=metadatas)
    print(f"✅ Added {len(chunks)} chunks to ChromaDB for record ID {record_id}.")
