# core/rag_engine.py
import os
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

def chunk_document(schema_text: str):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
        length_function=len,
        separators=["\npaths:", "\ncomponents:", "\n  /", "\n\n", "\n", " ", ""]
    )
    return text_splitter.split_text(schema_text)

def init_vector_db(chunks: list):
    vectorstore = Chroma.from_texts(
        texts=chunks, 
        embedding=embeddings,
        collection_name="shadowqa_schema"
    )
    return vectorstore.as_retriever(search_kwargs={"k": 3})

def analyze_error_with_rag(error_log: str, retriever, groq_client, model_name="llama-3.3-70b-versatile"):
    """
    Queries the vector database for relevant API context and asks Groq to diagnose the root cause.
    """
    # 1. Retrieve the most relevant chunks from the OpenAPI schema matching the error
    if retriever:
        docs = retriever.invoke(error_log)
        context_str = "API Context/Schema:\n" + "\n---\n".join([doc.page_content for doc in docs])
        schema_prompt_addition = " using the provided OpenAPI schema fragments"
    else:
        context_str = "No specific API Schema provided. Use general API design principles to diagnose the issue."
        schema_prompt_addition = ""
    
    # 2. Construct the system prompt injecting the context
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
    
    user_prompt = f"{context_str}\n\nEncountered Error Log:\n{error_log}"
    
    # 3. Call your Groq API engine via chat completions
    response = groq_client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.1  # Low temperature keeps the diagnosis highly factual
    )
    
    return response.choices[0].message.content