import streamlit as st
import os
from dotenv import load_dotenv
from groq import Groq

# Import our newly modularized components
from database.db import init_db, get_or_create_user
from ui.tabs import (
    render_home_page,
    render_chaos_console,
    render_root_cause_analyzer,
    render_coverage_analyzer,
    render_history_audit,
)

# 1. Page Configuration (Must be the absolute first Streamlit command)
st.set_page_config(page_title="ShadowQA Suite", page_icon="🕵️", layout="wide")

# 2. Environment & Database Initialization
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Run db initialization on every script run (outside of cache) to ensure schema migrations apply on hot-reload
init_db()  

@st.cache_resource
def initialize_system():
    return Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

groq_client = initialize_system()

# 3. Session State Management (The memory bridge between tabs)
if "generated_tests" not in st.session_state:
    st.session_state.generated_tests = []

if "executed_results" not in st.session_state:
    st.session_state.executed_results = None

if "last_execution_error" not in st.session_state:
    st.session_state.last_execution_error = ""

# 4. Main Application Routing
# Sidebar Navigation
with st.sidebar:
    st.image("https://img.icons8.com/color/48/000000/ninja.png", width=30)
    st.markdown("### ShadowQA Control")
    st.caption("System active and monitoring.")
    st.write("---")
    
    raw_workspace = st.text_input(
        "Active Operator Workspace", 
        value="Default Operator",
        max_chars=50
    )
    
    # Sanitize input: allow only alphanumeric, spaces, and underscores
    import re
    workspace_name = re.sub(r'[^a-zA-Z0-9 _-]', '', raw_workspace)
    if not workspace_name.strip():
        workspace_name = "Default Operator"
        
    st.session_state.user_id = get_or_create_user(workspace_name)
        
    st.markdown("---")
    view = st.radio("Navigation Matrix", [
        "🏠 Home / Overview",
        "🎯 Chaos Console",
        "🧠 Root Cause Analyzer",
        "🕵️‍♂️ Coverage Analyzer",
        "📊 History & Audits"
    ])

# View Router (Injects the UI components we built earlier)
if view == "🏠 Home / Overview":
    render_home_page()
elif view == "🎯 Chaos Console":
    render_chaos_console(GROQ_API_KEY)
elif view == "🧠 Root Cause Analyzer":
    render_root_cause_analyzer(groq_client)
elif view == "🕵️‍♂️ Coverage Analyzer":
    render_coverage_analyzer(groq_client)
elif view == "📊 History & Audits":
    render_history_audit()
