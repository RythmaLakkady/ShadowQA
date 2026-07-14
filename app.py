import streamlit as st
import os
from dotenv import load_dotenv
from groq import Groq

st.set_page_config(page_title="Test")   # MUST BE FIRST

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
st.write(GROQ_API_KEY is not None)

from database.db import *
from core.llm_engine import generate_test_vectors
from core.test_runner import run_tests
from core.coverage import (
    parse_postman_collection,
    parse_pytest_script,
    evaluate_shadow_zones,
)
from core.rag_engine import (
    chunk_document,
    init_vector_db,
    analyze_error_with_rag,
)

st.success("Everything imported successfully")



# import streamlit as st
# import os
# from dotenv import load_dotenv
# from groq import Groq

# # Import our newly modularized components
# from database.db import init_db, authenticate_user, register_user
# from ui.tabs import (
#     render_onboarding_hub,
#     render_chaos_console,
#     render_root_cause_analyzer,
#     render_coverage_analyzer,
#     render_history_audit
# )

# # 1. Page Configuration (Must be the absolute first Streamlit command)
# st.set_page_config(page_title="ShadowQA Suite", page_icon="🕵️", layout="wide")

# # 2. Environment & Database Initialization
# load_dotenv()
# GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# @st.cache_resource
# def initialize_system():
#     init_db()  # Creates the SQLite file and tables if they don't exist
#     return Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# groq_client = initialize_system()

# # 3. Session State Management (The memory bridge between tabs)
# if "user_id" not in st.session_state:
#     st.session_state.user_id = None
# if "generated_tests" not in st.session_state:
#     st.session_state.generated_tests = []
# if "last_execution_error" not in st.session_state:
#     st.session_state.last_execution_error = ""

# # 4. Authentication Barrier (Acts as your ui/auth.py component)
# def render_auth():
#     st.title("🔐 ShadowQA Security Gateway")
#     st.write("---")
    
#     col1, col2, col3 = st.columns([1, 2, 1])
#     with col2:
#         tab1, tab2 = st.tabs(["Operator Login", "Request Clearance (Register)"])
        
#         with tab1:
#             l_user = st.text_input("Username", key="login_user")
#             l_pass = st.text_input("Password", type="password", key="login_pass")
#             if st.button("Authenticate", use_container_width=True):
#                 user_id = authenticate_user(l_user, l_pass)
#                 if user_id:
#                     st.session_state.user_id = user_id
#                     st.rerun()
#                 else:
#                     st.error("Invalid credentials. Access denied.")
                    
#         with tab2:
#             r_user = st.text_input("New Username", key="reg_user")
#             r_pass = st.text_input("New Password", type="password", key="reg_pass")
#             if st.button("Register Identity", use_container_width=True):
#                 if r_user and r_pass:
#                     if register_user(r_user, r_pass):
#                         st.success("Identity registered! You may now switch to the Login tab.")
#                     else:
#                         st.error("Username already exists in the system registry.")
#                 else:
#                     st.warning("Please provide both a username and password.")

# # 5. Main Application Routing
# if st.session_state.user_id is None:
#     render_auth()
# else:
#     # Sidebar Navigation
#     with st.sidebar:
#         st.header("🕵️ ShadowQA Control")
#         st.caption(f"Active Operator ID: {st.session_state.user_id}")
#         if st.button("Log Out", use_container_width=True):
#             st.session_state.user_id = None
#             st.rerun()
            
#         st.markdown("---")
#         view = st.radio("Navigation Matrix", [
#             "ℹ️ Onboarding Hub",
#             "🎯 Chaos Console",
#             "🧠 Root Cause Analyzer",
#             "🕵️‍♂️ Coverage Analyzer",
#             "📊 History & Audits"
#         ])

#     # View Router (Injects the UI components we built earlier)
#     if view == "ℹ️ Onboarding Hub":
#         render_onboarding_hub(GROQ_API_KEY)
#     elif view == "🎯 Chaos Console":
#         render_chaos_console(GROQ_API_KEY)
#     elif view == "🧠 Root Cause Analyzer":
#         render_root_cause_analyzer(groq_client)
#     elif view == "🕵️‍♂️ Coverage Analyzer":
#         render_coverage_analyzer(groq_client) 
#     elif view == "📊 History & Audits":
#         render_history_audit()

