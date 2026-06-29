import os
from typing import List, Optional

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from .summary import chain_chat


CHROMA_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "chroma_db")
)

embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

vector_store = Chroma(
    collection_name="ehr_chunks",
    embedding_function=embeddings,
    persist_directory=CHROMA_DIR,
)


def chunk_and_embed_document(patient_id: int, record_id: int, specialty: str, filename: str, text: str):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_text(text)

    metadatas = [
        {
            "patient_id": patient_id,
            "record_id": record_id,
            "specialty": specialty,
            "filename": filename,
        }
        for _ in chunks
    ]

    vector_store.add_texts(texts=chunks, metadatas=metadatas)
    print(f"Added {len(chunks)} chunks to ChromaDB for record ID {record_id}.")


def query_vector_rag(
    question: str,
    allowed_patient_ids: List[int],
    patient_id_filter: Optional[int] = None,
    selected_record_ids: Optional[List[int]] = None,
) -> str:
    if selected_record_ids:
        if len(selected_record_ids) == 1:
            metadata_filter = {"record_id": selected_record_ids[0]}
        else:
            metadata_filter = {"record_id": {"$in": selected_record_ids}}
    elif patient_id_filter is not None:
        metadata_filter = {"patient_id": patient_id_filter}
    else:
        if len(allowed_patient_ids) == 1:
            metadata_filter = {"patient_id": allowed_patient_ids[0]}
        else:
            metadata_filter = {"patient_id": {"$in": allowed_patient_ids}}

    docs = vector_store.similarity_search(question, k=8, filter=metadata_filter)

    context_parts = []
    for doc in docs:
        filename = doc.metadata.get("filename", "Nespecificat")
        specialty = doc.metadata.get("specialty", "Nespecificat")
        context_parts.append(
            f"[Fisier: {filename} | Specialitate: {specialty}]\n{doc.page_content}\n"
        )

    combined_context = (
        "\n---\n".join(context_parts)
        if context_parts
        else "Nu s-au gasit fragmente medicale relevante."
    )

    return chain_chat.invoke(
        {
            "context": combined_context,
            "question": question,
        }
    )