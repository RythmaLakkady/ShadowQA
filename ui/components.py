import streamlit as st

def render_sidebar():
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
        
    return nav_selection
