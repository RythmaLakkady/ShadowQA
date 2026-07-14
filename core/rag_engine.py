# core/rag_engine.py

import streamlit as st
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings


@st.cache_resource(show_spinner="Loading embedding model...")
def get_embeddings():
    """
    Lazily initialize and cache the embedding model.
    This prevents Streamlit startup from blocking during import.
    """
    return HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2"
    )


def chunk_document(schema_text: str):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
        length_function=len,
        separators=[
            "\npaths:",
            "\ncomponents:",
            "\n  /",
            "\n\n",
            "\n",
            " ",
            ""
        ],
    )
    return text_splitter.split_text(schema_text)


def init_vector_db(chunks: list):
    embeddings = get_embeddings()

    vectorstore = Chroma.from_texts(
        texts=chunks,
        embedding=embeddings,
        collection_name="shadowqa_schema",
    )

    return vectorstore.as_retriever(search_kwargs={"k": 3})


def analyze_error_with_rag(
    error_log: str,
    retriever,
    groq_client,
    model_name="llama-3.3-70b-versatile",
):
    """
    Queries the vector database for relevant API context
    and asks Groq to diagnose the root cause.
    """

    if retriever:
        docs = retriever.invoke(error_log)
        context_str = (
            "API Context/Schema:\n"
            + "\n---\n".join(doc.page_content for doc in docs)
        )
        schema_prompt_addition = (
            " using the provided OpenAPI schema fragments"
        )
    else:
        context_str = (
            "No specific API Schema provided. "
            "Use general API design principles to diagnose the issue."
        )
        schema_prompt_addition = ""

    system_prompt = (
        "You are an expert SDE and SDET API debugging assistant.\n"
        f"Your task is to analyze an API error log{schema_prompt_addition}.\n"
        "Provide a structured analysis matching this format exactly:\n\n"
        "❌ API Error: [Error Code/Type]\n\n"
        "Possible Causes:\n"
        "1. [Cause 1]\n"
        "2. [Cause 2]\n\n"
        "Relevant Documentation:\n"
        "[Brief relevant snippet or explanation from the schema]"
    )

    user_prompt = (
        f"{context_str}\n\n"
        f"Encountered Error Log:\n{error_log}"
    )

    response = groq_client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.1,
    )

    return response.choices[0].message.content
