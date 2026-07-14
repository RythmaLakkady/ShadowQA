import streamlit as st
import time
from core.llm_engine import generate_test_vectors
from core.test_runner import run_tests
from database.db import get_test_sessions, get_test_results
from core.rag_engine import chunk_document, init_vector_db, analyze_error_with_rag
from core.coverage import parse_postman_collection, parse_pytest_script, evaluate_shadow_zones

@st.cache_resource(show_spinner="Indexing API Specification into Vector Store...")
def process_schema_to_vector_db(schema_text: str):
    """Caches the RAG vector store indexing to prevent re-embedding on every UI action."""
    chunks = chunk_document(schema_text)
    retriever = init_vector_db(chunks)
    return retriever

def render_onboarding_hub(backend_api_key):
    st.title("ℹ️ ShadowQA Operational Onboarding")
    st.write("---")
    
    st.markdown("""
    ### What is ShadowQA?
    ShadowQA is an **AI-Driven Automated API Chaos Testing Engine**. Instead of relying on manual QA engineering scripts to uncover boundary errors and validation exploits, ShadowQA leverages High-Throughput LLMs to parse endpoint requirements, construct malicious test vectors, execute live payloads, and audit structural system stability.
    
    ### System Architecture & Data Lifecycle
    1. **Target Parsing:** The engine processes an Endpoint URL and your raw structural text description.
    2. **AI Inference Generation:** The system instructions compel the LLM to output a strict, machine-readable array of automated test vectors across 3 operational threat levels.
    3. **Live Execution:** The Streamlit runtime engine maps sequentially over the payloads, utilizing standard Python networking loops to strike the target.
    4. **Defensive Auditing:** The platform evaluates returning **HTTP Status Codes** to automatically spot vulnerabilities.
    """)
    
    if backend_api_key:
        st.success("✅ **System Connected:** A valid Groq API Key was automatically discovered from your environment setup. The pipeline is fully operational.")
    else:
        st.error("⚠️ **System Offline:** No `GROQ_API_KEY` was found in your environment or your `.env` file. Please configure it in your root directory to execute live testing pipelines.")


def render_chaos_console(backend_api_key):
    st.title("🎯 Chaos Testing Control Panel")
    st.write("---")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        target_url = st.text_input("Target Endpoint URL", value="https://jsonplaceholder.typicode.com/posts")
        http_method = st.selectbox("HTTP Target Method", ["POST", "PUT", "GET"])
    with col2:
        api_desc = st.text_area(
            "API Description / Required JSON Schema Rules", 
            value="Expects a JSON payload containing: 'title' (string), 'body' (string), and 'userId' (integer between 1 and 100)."
        )
        
    if st.button("💥 Initialize AI Generation Matrix", use_container_width=True):
        if not backend_api_key:
            st.info("ℹ️ Running in Demo Mode (No backend environment API key found). Loading cached structural test suite vectors...")
            time.sleep(1)
            st.session_state.generated_tests = [
                {"test_type": "Happy Path", "description": "Standard dataset submission matching data criteria perfectly.", "payload": {"title": "Test Title Valid", "body": "Valid body text contents example.", "userId": 1}},
                {"test_type": "Edge Case", "description": "Empty blank parameters tracking checking mechanism.", "payload": {"title": "", "body": "", "userId": 1}},
                {"test_type": "Edge Case", "description": "Negative boundaries integer handling validation bypass test.", "payload": {"title": "Valid Title", "body": "Valid body text context", "userId": -99}},
                {"test_type": "Chaos Path", "description": "SQL Injection authentication escape threat logic attempt.", "payload": {"title": "admin' OR '1'='1", "body": "malicious string manipulation payload", "userId": 1}}
            ]
            st.success("Successfully loaded 4 structural demo attack vectors!")
        else:
            with st.spinner("Generating automated attack vectors from endpoint schema instructions..."):
                try:
                    tests = generate_test_vectors(target_url, http_method, api_desc, backend_api_key)
                    st.session_state.generated_tests = tests
                    st.success(f"Successfully generated and structured {len(st.session_state.generated_tests)} programmatic attack vectors!")
                except Exception as e:
                    st.error(f"Execution Error during prompt inference orchestration: {str(e)}")

    if st.session_state.generated_tests:
        st.write("---")
        st.subheader("Generated Testing Matrices")
        st.dataframe(st.session_state.generated_tests, use_container_width=True)
        
        if st.button("🚀 Fire Automated Testing Payloads", use_container_width=True):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            runner = run_tests(st.session_state.generated_tests, target_url, http_method, st.session_state.user_id)
            for step in runner:
                if step.get("done"):
                    status_text.text("Testing pipeline execution complete. Writing logs to long-term database storage...")
                    st.success("Metrics compiled successfully!")
                    
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Total Automated Strikes", f"{len(st.session_state.generated_tests)} Vectors")
                    m2.metric("Vulnerability Defect Rate", f"{step['vulnerability_rate']}%", delta=f"{step['failures_count']} Issues Detected", delta_color="inverse")
                    m3.metric("Average Response Latency", f"{step['avg_latency']} ms")
                    
                    st.write(step["executed_results"])
                    
                    # --- AUTO-DEBUG BRIDGE INITIALIZATION ---
                    # If failures were detected, isolate the first critical anomaly and pass it to the RAG analyzer session state
                    if step['failures_count'] > 0:
                        failed_rows = [r for r in step['executed_results'] if r.get('status') == 'FAIL' or r.get('status_code', 200) >= 400]
                        if failed_rows:
                            primary_failure = failed_rows[0]
                            st.session_state.last_execution_error = (
                                f"Method: {http_method}\n"
                                f"Endpoint: {target_url}\n"
                                f"HTTP Status Code Returned: {primary_failure.get('status_code')}\n"
                                f"Injected Payload: {primary_failure.get('payload')}\n"
                                f"Response Content: {primary_failure.get('response_body', 'N/A')}"
                            )
                            st.info("💡 **AI Debugger Bridge Active:** A critical vulnerability error trace was captured. You can switch to the **Root Cause Analyzer** tab to resolve it.")
                else:
                    status_text.text(f"Executing Vector {step['index']+1}/{step['total']}: {step['test'].get('description', '')}")
                    progress_bar.progress((step['index'] + 1) / step['total'])
                    time.sleep(0.1)


def render_root_cause_analyzer(groq_client):
    """Render Module: AI-Powered RAG Error Diagnostics Suite"""
    st.title("🧠 AI Root Cause Analyzer")
    st.write("---")
    st.markdown("Diagnose application failures and runtime errors by cross-referencing live traces against your structural API specifications.")

    uploaded_schema = st.file_uploader(
        "Upload API Specification Template (JSON / YAML)", 
        type=["json", "yaml", "yml"],
        key="rag_schema_uploader"
    )
    
    retriever = None
    if uploaded_schema is not None:
        schema_text = uploaded_schema.read().decode("utf-8")
        retriever = process_schema_to_vector_db(schema_text)
        st.success("📡 API documentation chunks successfully vectorized and loaded into the local database context.")

    # Pull error signatures automatically generated by the Chaos Console tab
    saved_error_context = st.session_state.get("last_execution_error", "")
    error_input = st.text_area(
        "Paste Error Log, Stack Trace, or System Response Context",
        value=saved_error_context,
        height=180,
        placeholder="Example: HTTP/1.1 401 Unauthorized\nExpired JSON Web Token signature format error..."
    )

    if st.button("🔍 Run AI Automated Diagnostics", type="primary", use_container_width=True):
        if not error_input.strip():
            st.error("Operation Aborted: Please supply a structural error trace statement.")
            return

        if not retriever:
            st.warning("⚠️ No API Schema uploaded. Proceeding with generalized AI diagnostics without RAG context.")

        with st.spinner("Executing RAG parsing and querying Groq inference nodes..."):
            try:
                diagnostic_report = analyze_error_with_rag(
                    error_log=error_input,
                    retriever=retriever,
                    groq_client=groq_client
                )
                st.markdown("---")
                st.subheader("📋 Core Diagnostic Findings Report")
                st.markdown(diagnostic_report)
            except Exception as e:
                st.error(f"Internal Diagnostic Subroutine Exception Encountered: {str(e)}")


def render_coverage_analyzer():
    """Render Module: Automated Test Asset Validation & Shadow Zone Coverage Analysis"""
    st.title("🕵️‍♂️ Shadow Zone Coverage Analyzer")
    st.write("---")
    st.markdown("Identify untracked endpoints and unexecuted test permutations by contrasting validation scripts against application operational maps.")

    c1, c2 = st.columns(2)
    with c1:
        st.file_uploader("Upload Core API Schema (JSON/YAML)", type=["json", "yaml", "yml"], key="cov_schema")
    with c2:
        st.file_uploader("Upload Existing Functional Test Scripts (Postman Collections / PyTest files)", type=["json", "py"], key="cov_tests")

    if st.button("📊 Evaluate Structural Test Coverage Matrix", use_container_width=True):
        st.warning("🚧 Coverage pipeline execution modules are currently initializing. Vector processing stubs are configured ready for functional code integration.")


def render_history_audit():
    st.title("📊 Historical Vulnerability Audits")
    st.write("---")
    
    sessions = get_test_sessions(st.session_state.user_id)
    
    if not sessions:
        st.info("No past testing executions logged for this profile configuration yet.")
    else:
        for sess in sessions:
            sess_id, url, ts, v_rate = sess
            with st.expander(f"📍 Session #{sess_id} — Target: {url} | Executed: {ts} | Defect Rate: {v_rate}%"):
                details = get_test_results(sess_id)
                formatted_details = []
                for d in details:
                    formatted_details.append({
                        "Test Classification": d[0],
                        "Injected Payload Buffer": d[1],
                        "HTTP Status Code": d[2],
                        "Network Response Latency (ms)": d[3],
                        "Audit Resolution Status": d[4]
                    })
                st.dataframe(formatted_details, use_container_width=True)

def render_coverage_analyzer(groq_client):
    """Render Module: Automated Test Asset Validation & Shadow Zone Coverage Analysis"""
    st.title("🕵️‍♂️ Shadow Zone Coverage Analyzer")
    st.write("---")
    st.markdown("Identify untracked endpoints and unexecuted test permutations by contrasting your existing validation scripts against application operational maps.")

    c1, c2 = st.columns(2)
    with c1:
        schema_file = st.file_uploader("1. Upload Core API Schema (JSON/YAML)", type=["json", "yaml", "yml"], key="cov_schema")
    with c2:
        test_file = st.file_uploader("2. Upload Existing Test Script (Postman JSON / PyTest)", type=["json", "py"], key="cov_tests")

    if st.button("📊 Evaluate Structural Test Coverage Matrix", use_container_width=True, type="primary"):
        if not schema_file or not test_file:
            st.error("Operation Aborted: Please upload both a Schema and a Test File to perform cross-referencing.")
            return
            
        with st.spinner("Extracting endpoints and calculating semantic coverage gaps..."):
            try:
                # 1. Read files
                schema_text = schema_file.read().decode("utf-8")
                test_text = test_file.read().decode("utf-8")
                file_ext = test_file.name.split('.')[-1].lower()
                
                # 2. Parse test files based on extension
                extracted_tests = []
                if file_ext == "json":
                    extracted_tests = parse_postman_collection(test_text)
                elif file_ext == "py":
                    extracted_tests = parse_pytest_script(test_text)
                
                st.info(f"🔍 Pipeline Extracted **{len(extracted_tests)}** distinct API calls from `{test_file.name}`.")
                
                # 3. Execute LLM Gap Analysis
                report = evaluate_shadow_zones(schema_text, extracted_tests, groq_client)
                
                st.markdown("---")
                st.markdown(report)
                
            except Exception as e:
                st.error(f"Analysis Execution Failed: {str(e)}")
