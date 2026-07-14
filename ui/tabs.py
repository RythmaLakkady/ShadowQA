import streamlit as st
import time

from core.llm_engine import generate_test_vectors
from core.test_runner import run_tests
from database.db import get_test_sessions, get_test_results
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


@st.cache_resource(show_spinner="Indexing API Specification into Vector Store...")
def process_schema_to_vector_db(schema_text: str):
    chunks = chunk_document(schema_text)
    retriever = init_vector_db(chunks)
    return retriever


def render_onboarding_hub(backend_api_key):
    st.title("ℹ️ ShadowQA Operational Onboarding")
    st.write("---")

    st.markdown("""
### What is ShadowQA?

ShadowQA is an **AI-Driven Automated API Chaos Testing Engine**.

Instead of relying on manual QA engineering scripts to uncover
boundary errors and validation exploits, ShadowQA leverages
High-Throughput LLMs to parse endpoint requirements,
construct malicious test vectors,
execute live payloads,
and audit structural system stability.

### System Architecture & Data Lifecycle

1. **Target Parsing**
2. **AI Inference Generation**
3. **Live Execution**
4. **Defensive Auditing**
""")

    if backend_api_key:
        st.success(
            "✅ System Connected. Groq API key detected."
        )
    else:
        st.error(
            "⚠️ No GROQ_API_KEY detected."
        )


def render_chaos_console(backend_api_key):

    st.title("🎯 Chaos Testing Control Panel")
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

    if st.button(
        "💥 Initialize AI Generation Matrix",
        use_container_width=True,
    ):

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

                    st.success(
                        f"{len(tests)} test vectors generated."
                    )

                except Exception as e:

                    st.error(str(e))

    if st.session_state.get("generated_tests"):

        st.divider()

        st.subheader("Generated Test Cases")

        st.dataframe(
            st.session_state.generated_tests,
            use_container_width=True,
        )

        if st.button(
            "🚀 Fire Automated Testing Payloads",
            use_container_width=True,
        ):

            progress = st.progress(0)

            status = st.empty()

            st.session_state.executed_results = None  
            runner = run_tests(
                st.session_state.generated_tests,
                target_url,
                http_method,
                st.session_state.user_id,
            )

            for step in runner:

                if step.get("done"):

                    st.session_state.executed_results = step

                    status.text("Execution completed.")

                    st.success("Testing finished successfully.")

                    if step["failures_count"] > 0:

                        failed = [
                            r
                            for r in step["executed_results"]
                            if r["status"] == "FAIL"
                        ]

                        if failed:

                            first = failed[0]

                            st.session_state.last_execution_error = (
                                f"Method: {http_method}\n"
                                f"Endpoint: {target_url}\n"
                                f"Status Code: {first['status_code']}\n"
                                f"Payload: {first['payload']}\n"
                                f"Response: {first['response_body']}"
                            )

                            st.info(
                                "AI Debugger Bridge activated."
                            )

                else:

                    progress.progress(
                        (step["index"] + 1) / step["total"]
                    )

                    status.text(
                        f"Running test {step['index']+1}/{step['total']}"
                    )

                    time.sleep(0.05)

        if st.session_state.get("executed_results") is not None:

            results = st.session_state.executed_results

            st.divider()

            st.subheader("Execution Results")

            c1, c2, c3 = st.columns(3)

            c1.metric(
                "Vectors",
                len(st.session_state.generated_tests),
            )

            c2.metric(
                "Vulnerability %",
                results["vulnerability_rate"],
            )

            c3.metric(
                "Average Latency",
                f"{results['avg_latency']} ms",
            )

            st.dataframe(
                results["executed_results"],
                use_container_width=True,
            )

def render_root_cause_analyzer(groq_client):
    st.title("🧠 AI Root Cause Analyzer")
    st.write("---")

    st.markdown(
        "Diagnose application failures and runtime errors by "
        "cross-referencing live traces against your API specification."
    )

    uploaded_schema = st.file_uploader(
        "Upload API Specification (JSON/YAML)",
        type=["json", "yaml", "yml"],
        key="rag_schema_uploader",
    )

    retriever = None

    if uploaded_schema is not None:
        schema_text = uploaded_schema.read().decode("utf-8")
        retriever = process_schema_to_vector_db(schema_text)

        st.success(
            "📡 API specification indexed successfully."
        )

    saved_error_context = st.session_state.get(
        "last_execution_error",
        "",
    )

    error_input = st.text_area(
        "Paste Error Log / Stack Trace",
        value=saved_error_context,
        height=180,
    )

    if st.button(
        "🔍 Run AI Automated Diagnostics",
        type="primary",
        use_container_width=True,
    ):

        if not error_input.strip():
            st.error("Please provide an error log.")
            return

        if not retriever:
            st.warning(
                "No schema uploaded. Running without RAG context."
            )

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


def render_history_audit():

    st.title("📊 Historical Vulnerability Audits")

    st.write("---")

    sessions = get_test_sessions(
        st.session_state.user_id
    )

    if not sessions:

        st.info(
            "No previous testing sessions found."
        )

        return

    for session in sessions:

        session_id, url, ts, vulnerability = session

        with st.expander(
            f"Session #{session_id} | {url} | {ts}"
        ):

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

            st.dataframe(
                table,
                use_container_width=True,
            )


def render_coverage_analyzer(groq_client):
    """
    Shadow Zone Coverage Analyzer
    Compares the uploaded API schema against existing tests and
    identifies missing endpoints and test cases.
    """

    st.title("🕵️‍♂️ Shadow Zone Coverage Analyzer")
    st.write("---")

    st.markdown(
        """
Upload your API Schema and your existing test suite.

ShadowQA will:

- Extract tested endpoints
- Compare them against the API schema
- Identify uncovered endpoints
- Highlight missing edge cases
- Estimate overall API test coverage
"""
    )

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

    if st.button(
        "📊 Analyze Coverage",
        type="primary",
        use_container_width=True,
    ):

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

                st.success(
                    f"Detected {len(extracted_tests)} API requests."
                )

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




