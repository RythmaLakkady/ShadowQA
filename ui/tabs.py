import streamlit as st
import time
import pandas as pd
import json

from core.llm_engine import generate_test_vectors
from core.test_runner import run_tests
from database.db import get_test_sessions, get_all_test_sessions, get_test_results
from core.rag_engine import (
    chunk_document,
    init_vector_db,
    analyze_error_with_rag,
)
from core.coverage import (
    parse_postman_collection,
    parse_pytest_script,
    evaluate_shadow_zones,
)

def highlight_status(row):
    """Pandas styler function to highlight rows based on test status."""
    # Handle both realtime execution results ('status') and db results ('Result')
    status = str(row.get('status', row.get('Result', '')))
    if status == 'FAIL' or 'VULNERABILITY' in status or 'CRASH' in status:
        return ['background-color: rgba(255, 99, 71, 0.2)'] * len(row)
    elif status == 'PASS' or 'PASS' in status:
        return ['background-color: rgba(144, 238, 144, 0.2)'] * len(row)
    return [''] * len(row)

@st.cache_resource(show_spinner="Indexing API Specification into Vector Store...")
def process_schema_to_vector_db(schema_text: str):
    chunks = chunk_document(schema_text)
    retriever = init_vector_db(chunks)
    return retriever


def render_home_page():
    st.title("🏠 Welcome to ShadowQA")
    st.write("---")
    
    st.markdown("""
    ### What is ShadowQA?
    ShadowQA is an **AI-powered API testing tool**. It acts like an intelligent QA engineer that learns how your API is supposed to work and then automatically generates tests to break it.

    ### Why was it built?
    Writing tests manually is slow and often misses edge cases. We built ShadowQA to automate the tedious parts of API testing. Instead of writing hundreds of lines of Postman or PyTest scripts to check if your API handles missing fields or bad data correctly, you just tell ShadowQA what the API *should* do, and the AI handles the rest. 
    
    ### What can you expect?
    By using this suite, you can expect to:
    1. **Save time:** Generate malicious and happy-path payloads instantly (🎯 Chaos Console).
    2. **Debug faster:** Let AI read your error logs and API schemas to tell you exactly *why* something broke (🧠 Root Cause Analyzer).
    3. **Find blind spots:** Compare your existing test files against your actual API schema to see what endpoints you forgot to test (🕵️‍♂️ Coverage Analyzer).
    
    *Use the sidebar to select your active workspace and choose a tool to get started!*
    """)
    

def render_chaos_console(backend_api_key):
    st.title("🎯 Chaos Testing Control Panel")
    st.markdown("""
    **What this does:** Generates AI-driven malicious test vectors to test boundary conditions and vulnerabilities of your API.
    **How to use:** Enter your target API endpoint, method, and a brief description. Click generate, then fire the payloads.
    """)
    st.write("---")

    col1, col2 = st.columns(2)

    with col1:
        target_url = st.text_input(
            "Target Endpoint URL",
            value="https://jsonplaceholder.typicode.com/posts",
        )
        http_method = st.selectbox(
            "HTTP Target Method",
            ["POST", "PUT", "GET"],
        )

    with col2:
        api_desc = st.text_area(
            "API Description / Required JSON Schema Rules",
            value="Expects a JSON payload containing: title, body and userId."
        )

    if st.button("💥 Initialize AI Generation Matrix", use_container_width=True):
        if not backend_api_key:
            time.sleep(1)
            st.session_state.generated_tests = [
                {
                    "test_type": "Happy Path",
                    "description": "Demo",
                    "payload": {
                        "title": "Demo",
                        "body": "Demo",
                        "userId": 1,
                    },
                }
            ]
            st.success("Loaded demo vectors.")
        else:
            with st.spinner("Generating AI test vectors..."):
                try:
                    tests = generate_test_vectors(
                        target_url,
                        http_method,
                        api_desc,
                        backend_api_key,
                    )
                    st.session_state.generated_tests = tests
                    st.success(f"{len(tests)} test vectors generated.")
                except Exception as e:
                    st.error(str(e))

    if st.session_state.get("generated_tests"):
        st.divider()
        st.subheader("Generated Test Cases")
        st.dataframe(st.session_state.generated_tests, use_container_width=True)

        if st.button("🚀 Fire Automated Testing Payloads", use_container_width=True):
            progress = st.progress(0)
            status = st.empty()
            st.session_state.executed_results = None  
            runner = run_tests(
                st.session_state.generated_tests,
                target_url,
                http_method,
                st.session_state.user_id,
                schema_text=api_desc,
            )

            for step in runner:
                if step.get("done"):
                    st.session_state.executed_results = step
                    status.text("Execution completed.")
                    st.success("Testing finished successfully.")

                    if step["failures_count"] > 0:
                        failed = [r for r in step["executed_results"] if r["status"] == "FAIL"]
                        if failed:
                            first = failed[0]
                            st.session_state.last_execution_error = (
                                f"Method: {http_method}\n"
                                f"Endpoint: {target_url}\n"
                                f"Status Code: {first['status_code']}\n"
                                f"Payload: {first['payload']}\n"
                                f"Response: {first['response_body']}"
                            )
                            st.info("AI Debugger Bridge activated. Check Root Cause Analyzer.")
                else:
                    progress.progress((step["index"] + 1) / step["total"])
                    status.text(f"Running test {step['index']+1}/{step['total']}")
                    time.sleep(0.05)

        if st.session_state.get("executed_results") is not None:
            results = st.session_state.executed_results
            st.divider()
            st.subheader("Execution Results")

            c1, c2, c3 = st.columns(3)
            c1.metric("Vectors", len(st.session_state.generated_tests))
            c2.metric("Vulnerability %", results["vulnerability_rate"])
            c3.metric("Average Latency", f"{results['avg_latency']} ms")

            display_results = pd.DataFrame(results["executed_results"])
            display_results["payload"] = display_results["payload"].astype(str)
            display_results["response_body"] = display_results["response_body"].astype(str)
            
            # Apply Red/Green styling
            styled_df = display_results.style.apply(highlight_status, axis=1)
            
            st.dataframe(styled_df, use_container_width=True)


def render_root_cause_analyzer(groq_client):
    st.title("🧠 AI Root Cause Analyzer")
    st.markdown("""
    **What this does:** Diagnoses application failures by cross-referencing live traces against your API specification.
    **How to use:** Upload your API schema (optional but recommended). Provide an error log or select a failed test from history, then run the diagnostics.
    """)
    st.write("---")

    uploaded_schema = st.file_uploader(
        "Upload API Specification (JSON/YAML)",
        type=["json", "yaml", "yml"],
        key="rag_schema_uploader",
    )

    retriever = None
    if uploaded_schema is not None:
        schema_text = uploaded_schema.read().decode("utf-8")
        retriever = process_schema_to_vector_db(schema_text)
        st.success("📡 API specification indexed successfully.")

    st.subheader("Select from History (Optional)")
    sessions = get_all_test_sessions()
    history_options = {"None": ""}
    
    # Keep track of schema text per history key
    schema_map = {}

    if sessions:
        for session in sessions:
            session_id, url, ts, vulnerability, schema_text = session
            rows = get_test_results(session_id)
            # index 4 is result_status. In DB, it's stored as VULNERABILITY_CRASH (500) etc.
            failed_tests = [r for r in rows if 'VULNERABILITY' in r[4] or 'CRASH' in r[4]] 
            
            for f in failed_tests:
                test_type, payload, status_code, latency, status = f
                key = f"Session #{session_id} - {ts} - {test_type} ({status_code})"
                val = f"Endpoint: {url}\nStatus Code: {status_code}\nPayload: {payload}"
                history_options[key] = val
                if schema_text:
                    schema_map[key] = schema_text

    selected_history = st.selectbox(
        "Auto-fill Error Log from past failures", 
        options=list(history_options.keys())
    )

    # Automatically process the schema from history if it exists
    if selected_history != "None" and selected_history in schema_map:
        history_schema = schema_map[selected_history]
        retriever = process_schema_to_vector_db(history_schema)
        st.success("📡 Historical API specification loaded from database!")

    saved_error_context = st.session_state.get("last_execution_error", "")
    
    # If a history item is selected, prioritize it over the session state
    default_text = history_options[selected_history] if selected_history != "None" else saved_error_context

    error_input = st.text_area(
        "Paste Error Log / Stack Trace",
        value=default_text,
        height=180,
    )

    if st.button("🔍 Run AI Automated Diagnostics", type="primary", use_container_width=True):
        if not error_input.strip():
            st.error("Please provide an error log.")
            return

        if not retriever:
            st.warning("No schema uploaded. Running without RAG context.")

        with st.spinner("Analyzing..."):
            try:
                report = analyze_error_with_rag(
                    error_log=error_input,
                    retriever=retriever,
                    groq_client=groq_client,
                )
                st.divider()
                st.subheader("Diagnostic Report")
                st.markdown(report)
            except Exception as e:
                st.error(str(e))


def render_coverage_analyzer(groq_client):
    st.title("🕵️‍♂️ Shadow Zone Coverage Analyzer")
    st.markdown("""
    **What this does:** Compares the uploaded API schema against existing tests and identifies missing endpoints and edge cases.
    **How to use:** Upload your OpenAPI/Swagger Schema and your existing test suite (Postman or PyTest). Click analyze to generate the coverage report.
    """)
    st.write("---")

    col1, col2 = st.columns(2)

    with col1:
        schema_file = st.file_uploader(
            "1️⃣ Upload OpenAPI / Swagger Schema",
            type=["json", "yaml", "yml"],
            key="coverage_schema",
        )

    with col2:
        test_file = st.file_uploader(
            "2️⃣ Upload Existing Test Suite",
            type=["json", "py"],
            key="coverage_tests",
        )

    if st.button("📊 Analyze Coverage", type="primary", use_container_width=True):
        if schema_file is None:
            st.error("Please upload an API schema.")
            return

        if test_file is None:
            st.error("Please upload a Postman Collection or PyTest file.")
            return

        with st.spinner("Analyzing test coverage..."):
            try:
                schema_text = schema_file.read().decode("utf-8")
                test_text = test_file.read().decode("utf-8")
                extension = test_file.name.split(".")[-1].lower()

                if extension == "json":
                    extracted_tests = parse_postman_collection(test_text)
                elif extension == "py":
                    extracted_tests = parse_pytest_script(test_text)
                else:
                    extracted_tests = []

                st.success(f"Detected {len(extracted_tests)} API requests.")

                report = evaluate_shadow_zones(
                    schema_text=schema_text,
                    extracted_tests=extracted_tests,
                    groq_client=groq_client,
                )

                st.divider()
                st.subheader("Coverage Analysis")
                st.markdown(report)

            except Exception as e:
                st.error(f"Coverage analysis failed:\n\n{e}")

def render_history_audit():
    st.title("📊 Historical Vulnerability Audits")
    st.markdown("""
    **What this does:** Shows a complete audit log of all testing sessions you have executed in this workspace.
    **How to use:** Expand any session below to view all tested payloads, latencies, and success/failure results.
    """)
    st.write("---")

    sessions = get_test_sessions(st.session_state.user_id)

    if not sessions:
        st.info("No previous testing sessions found in this workspace.")
        return

    for session in sessions:
        session_id, url, ts, vulnerability, schema_text = session
        with st.expander(f"Session #{session_id} | {url} | {ts}"):
            rows = get_test_results(session_id)
            table = []
            for row in rows:
                table.append(
                    {
                        "Test Type": row[0],
                        "Payload": row[1],
                        "Status Code": row[2],
                        "Latency (ms)": row[3],
                        "Result": row[4],
                    }
                )
            
            df = pd.DataFrame(table)
            styled_df = df.style.apply(highlight_status, axis=1)
            st.dataframe(styled_df, use_container_width=True)
