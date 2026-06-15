import streamlit as st
import sqlite3
import hashlib
import json
import time
import requests
import os
from datetime import datetime

# ==========================================
# 1. DATABASE INITIALIZATION & CORE FUNCTIONS
# ==========================================
DB_FILE = "shadowqa.db"

def init_db():
    """Initializes the SQLite database tables if they do not exist."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    
    # Test Sessions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS test_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            target_url TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            vulnerability_rate REAL NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    
    # Test Results table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS test_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            test_type TEXT NOT NULL,
            payload TEXT NOT NULL,
            status_code INTEGER,
            response_time_ms REAL,
            result_status TEXT NOT NULL,
            FOREIGN KEY(session_id) REFERENCES test_sessions(id)
        )
    """)
    conn.commit()
    conn.close()

def hash_password(password):
    """Simple, clean SHA-256 password hashing to avoid heavy external binary dependencies."""
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username, password):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hash_password(password)))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def authenticate_user(username, password):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = ? AND password = ?", (username, hash_password(password)))
    user = cursor.fetchone()
    conn.close()
    return user[0] if user else None

def load_env_key():
    """Locates the Groq API key checking system environment variables, local .env files, or Streamlit secrets."""
    if os.getenv("GROQ_API_KEY"):
        return os.getenv("GROQ_API_KEY").strip()
    if os.path.exists(".env"):
        with open(".env", "r") as f:
            for line in f:
                if line.startswith("GROQ_API_KEY"):
                    parts = line.strip().split("=", 1)
                    if len(parts) == 2:
                        return parts[1].strip("'\" ")
    try:
        return st.secrets.get("GROQ_API_KEY", "").strip()
    except Exception:
        return ""

# Initialize DB on Startup
init_db()

# ==========================================
# 2. STREAMLIT APP CONFIG & STATE
# ==========================================
st.set_page_config(page_title="ShadowQA - Universal Chaos Agent", layout="wide", initial_sidebar_state="expanded")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "username" not in st.session_state:
    st.session_state.username = None
if "generated_tests" not in st.session_state:
    st.session_state.generated_tests = None

# Automatically parse key from workspace environment config
BACKEND_API_KEY = load_env_key()

# ==========================================
# 3. AUTHENTICATION INTERFACE (GUARD LAYER)
# ==========================================
if not st.session_state.logged_in:
    st.title("🎯 ShadowQA — Universal API Chaos Agent")
    st.subheader("Automated AI Boundary & Security Vulnerability Testing Framework")
    
    auth_tab, reg_tab = st.tabs(["🔒 Secure Login", "📝 Create Account"])
    
    with auth_tab:
        login_user = st.text_input("Username", key="login_user_input")
        login_pass = st.text_input("Password", type="password", key="login_pass_input")
        if st.button("Sign In", use_container_width=True):
            uid = authenticate_user(login_user, login_pass)
            if uid:
                st.session_state.logged_in = True
                st.session_state.user_id = uid
                st.session_state.username = login_user
                st.success(f"Welcome back, {login_user}!")
                st.rerun()
            else:
                st.error("Invalid credentials. Please verify your username and password.")
                
    with reg_tab:
        reg_user = st.text_input("Choose Username", key="reg_user_input")
        reg_pass = st.text_input("Choose Password", type="password", key="reg_pass_input")
        if st.button("Register", use_container_width=True):
            if reg_user and reg_pass:
                if register_user(reg_user, reg_pass):
                    st.success("Account created successfully! Proceed to log in.")
                else:
                    st.error("Username already exists. Choose another one.")
            else:
                st.warning("All input fields are completely required.")
    st.stop()

# ==========================================
# 4. APPLICATION LAYOUT & NAVIGATION
# ==========================================
st.sidebar.title(f"👤 Active: {st.session_state.username}")
nav_selection = st.sidebar.radio(
    "Navigation System",
    ["ℹ️ Onboarding Hub", "🎯 Chaos Console", "📊 History & Audits"]
)

if st.sidebar.button("Log Out Execution", use_container_width=True):
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.username = None
    st.rerun()

# ==========================================
# VIEW A: INFO & ONBOARDING HUB
# ==========================================
if nav_selection == "ℹ️ Onboarding Hub":
    st.title("ℹ️ ShadowQA Operational Onboarding")
    st.write("---")
    
    st.markdown("""
    ### What is ShadowQA?
    ShadowQA is an **AI-Driven Automated API Chaos Testing Engine**. Instead of relying on manual QA engineering scripts to uncover boundary errors and validation exploits, ShadowQA leverages High-Throughput LLMs to parse endpoint requirements, construct malicious test vectors, execute live payloads, and audit structural system stability.
    
    ### System Architecture & Data Lifecycle
    1. **Target Parsing:** The engine processes an Endpoint URL and your raw structural text description.
    2. **AI Inference Generation:** The system instructions compel the LLM to output a strict, machine-readable array of exactly 15 test vectors across 3 operational threat levels.
    3. **Live Execution:** The Streamlit runtime engine maps sequentially over the payloads, utilizing standard Python networking loops to strike the target.
    4. **Defensive Auditing:** The platform evaluates returning **HTTP Status Codes** to automatically spot vulnerabilities.
    """)
    
    if BACKEND_API_KEY:
        st.success("✅ **System Connected:** A valid Groq API Key was automatically discovered from your environment setup. The pipeline is fully operational.")
    else:
        st.error("⚠️ **System Offline:** No `GROQ_API_KEY` was found in your environment or your `.env` file. Please configure it in your root directory to execute live testing pipelines.")

# ==========================================
# VIEW B: CHAOS TESTING CONSOLE
# ==========================================
elif nav_selection == "🎯 Chaos Console":
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
        if not BACKEND_API_KEY:
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
                system_prompt = """You are a highly analytical Senior SDET and Penetration Testing AI Agent.
                Your task is to analyze the user's API description and output exactly 15 diverse testing payloads.
                
                You must split the payloads equally into exactly 3 categories:
                1. 'Happy Path': Perfectly clean data matching structural layout specifications exactly. Expects 200/201.
                2. 'Edge Case': High/low boundaries, negative indices, extreme string data lengths, missing keys. Expects 400.
                3. 'Chaos Path': Malicious payloads, basic SQL injections, array breakouts, type coercion threats.
                
                CRITICAL: You must return a valid JSON object containing a single key called "test_cases" which holds the array of payloads. Do not include any markdown or explanation text.
                Format structural pattern perfectly as:
                {
                  "test_cases": [
                    {"test_type": "Happy Path", "description": "Short reasoning", "payload": {"key": "value"}},
                    {"test_type": "Edge Case", "description": "Short reasoning", "payload": {"key": "value"}}
                  ]
                }
                """
                
                user_prompt = f"Target Endpoint URL: {target_url}\nMethod: {http_method}\nSchema Rules: {api_desc}"
                
                try:
                    headers = {
                        "Authorization": f"Bearer {BACKEND_API_KEY}",
                        "Content-Type": "application/json"
                    }
                    payload_data = {
                        "model": "llama-3.3-70b-versatile",
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "temperature": 0.2,
                        "response_format": {"type": "json_object"}
                    }
                    response = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload_data, headers=headers)
                    
                    if response.status_code == 200:
                        raw_content = response.json()['choices'][0]['message']['content']
                        parsed_json = json.loads(raw_content)
                        st.session_state.generated_tests = parsed_json.get("test_cases", [])
                        st.success(f"Successfully generated and structured {len(st.session_state.generated_tests)} programmatic attack vectors!")
                    else:
                        st.error(f"Inference Failure: Groq API returned Status Code {response.status_code}. Details: {response.text}")
                except Exception as e:
                    st.error(f"Execution Error during prompt inference orchestration: {str(e)}")

    # Display and Run Phase
    if st.session_state.generated_tests:
        st.write("---")
        st.subheader("Generated Testing Matrices")
        st.dataframe(st.session_state.generated_tests, use_container_width=True)
        
        if st.button("🚀 Fire Automated Testing Payloads", use_container_width=True):
            total_vectors = len(st.session_state.generated_tests)
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            executed_results = []
            failures_count = 0
            
            for index, test in enumerate(st.session_state.generated_tests):
                status_text.text(f"Executing Vector {index+1}/{total_vectors}: {test['description']}")
                
                start_time = time.time()
                status_code = None
                res_time = 0
                result_status = "UNKNOWN"
                
                try:
                    if http_method == "POST":
                        res = requests.post(target_url, json=test['payload'], timeout=5)
                    elif http_method == "PUT":
                        res = requests.put(target_url, json=test['payload'], timeout=5)
                    else: # GET
                        res = requests.get(target_url, json=test['payload'], timeout=5)
                        
                    status_code = res.status_code
                    res_time = (time.time() - start_time) * 1000
                    
                    # Audit vulnerabilities based on status code return structures
                    if test['test_type'] == "Happy Path" and status_code in [200, 201]:
                        result_status = "PASS"
                    elif test['test_type'] == "Edge Case" and status_code in [400, 422]:
                        result_status = "PASS"
                    elif status_code == 500:
                        result_status = "VULNERABILITY_CRASH (500)"
                        failures_count += 1
                    elif test['test_type'] in ["Edge Case", "Chaos Path"] and status_code in [200, 201]:
                        result_status = "VULNERABILITY_LEAK (Accepted Unsanitized Data)"
                        failures_count += 1
                    else:
                        result_status = "PASS (Handled Gracefully)"
                        
                except requests.exceptions.RequestException:
                    res_time = (time.time() - start_time) * 1000
                    status_code = 0
                    result_status = "CONNECTION_REFUSED_CRASH"
                    failures_count += 1
                    
                executed_results.append({
                    "test_type": test['test_type'],
                    "payload": json.dumps(test['payload']),
                    "status_code": status_code,
                    "response_time_ms": round(res_time, 2),
                    "result_status": result_status
                })
                
                progress_bar.progress((index + 1) / total_vectors)
                time.sleep(0.1)
                
            status_text.text("Testing pipeline execution complete. Writing logs to long-term database storage...")
            
            # Save metrics to SQLite
            vulnerability_rate = round((failures_count / total_vectors) * 100, 2)
            timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO test_sessions (user_id, target_url, timestamp, vulnerability_rate) VALUES (?, ?, ?, ?)",
                (st.session_state.user_id, target_url, timestamp_str, vulnerability_rate)
            )
            session_id = cursor.lastrowid
            
            for res in executed_results:
                cursor.execute("""
                    INSERT INTO test_results (session_id, test_type, payload, status_code, response_time_ms, result_status)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (session_id, res['test_type'], res['payload'], res['status_code'], res['response_time_ms'], res['result_status']))
                
            conn.commit()
            conn.close()
            
            st.success("Metrics compiled successfully!")
            
            # Dashboard Metrics Presentation
            m1, m2, m3 = st.columns(3)
            m1.metric("Total Automated Strikes", f"{total_vectors} Vectors")
            m2.metric("Vulnerability Defect Rate", f"{vulnerability_rate}%", delta=f"{failures_count} Issues Detected", delta_color="inverse")
            avg_latency = round(sum(r['response_time_ms'] for r in executed_results) / total_vectors, 2)
            m3.metric("Average Response Latency", f"{avg_latency} ms")
            
            st.dataframe(executed_results, use_container_width=True)

# ==========================================
# VIEW C: HISTORY & AUDITS
# ==========================================
elif nav_selection == "📊 History & Audits":
    st.title("📊 Historical Vulnerability Audits")
    st.write("---")
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, target_url, timestamp, vulnerability_rate FROM test_sessions WHERE user_id = ? ORDER BY id DESC", (st.session_state.user_id,))
    sessions = cursor.fetchall()
    conn.close()
    
    if not sessions:
        st.info("No past testing executions logged for this profile configuration yet.")
    else:
        for sess in sessions:
            sess_id, url, ts, v_rate = sess
            with st.expander(f"📍 Session #{sess_id} — Target: {url} | Executed: {ts} | Defect Rate: {v_rate}%"):
                
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                cursor.execute("SELECT test_type, payload, status_code, response_time_ms, result_status FROM test_results WHERE session_id = ?", (sess_id,))
                details = cursor.fetchall()
                conn.close()
                
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