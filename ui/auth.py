import streamlit as st
from database.db import authenticate_user, register_user

def render_auth_layer():
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
