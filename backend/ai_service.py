# Compatibility shim for legacy imports.
# New code should import directly from backend/chains modules.

from chains.llm import detector, llm, llm_fast

from chains.summary import (
    summary_prompt,
    summary_prompt_ro,
    translate_prompt,
    chat_prompt,
    chain_summary,
    chain_summary_ro,
    chain_translate,
    chain_chat,
)

from chains.metadata import (
    SPECIALTY_MAPPING,
    specialty_translate_prompt,
    specialty_standardize_prompt,
    specialty_extract_doc_prompt,
    chain_specialty_translate,
    chain_specialty_standardize,
    chain_specialty_extract_doc,
    extract_specialty_raw,
    get_standardized_specialty,
    diagnosis_translate_prompt,
    diagnosis_standardize_prompt,
    diagnosis_extract_doc_prompt,
    chain_diagnosis_translate,
    chain_diagnosis_standardize,
    chain_diagnosis_extract_doc,
    extract_diagnosis_raw,
    clean_diagnosis_output,
    get_standardized_diagnosis,
)

from chains.chroma import (
    CHROMA_DIR,
    embeddings,
    vector_store,
    chunk_and_embed_document,
    query_vector_rag,
)

from chains.router import (
    AGGREGATE_KEYWORDS,
    force_sql_intent_if_aggregate,
    RouterResponse,
    chain_router,
)

from chains.sql import (
    sql_generation_prompt,
    chain_sql_gen,
    sql_correction_prompt,
    chain_sql_correct,
    sql_synthesis_prompt,
    chain_sql_synthesis,
)