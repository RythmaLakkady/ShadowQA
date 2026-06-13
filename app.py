"""
app.py — Streamlit frontend for AskFirst.
Run with:  streamlit run app.py
"""

from __future__ import annotations

import requests
import streamlit as st

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

API_BASE = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="AskFirst — AI Chat",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS — premium dark glassmorphism aesthetic
# ---------------------------------------------------------------------------

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* ---- Global ---- */
    html, body, [class*="st-"] {
        font-family: 'Inter', sans-serif;
    }

    .stApp {
        background: linear-gradient(145deg, #0d0d1a 0%, #131325 40%, #0f1b2d 100%);
    }

    /* ---- Sidebar ---- */
    section[data-testid="stSidebar"] {
        background: rgba(15, 15, 35, 0.85);
        backdrop-filter: blur(18px);
        border-right: 1px solid rgba(99, 102, 241, 0.15);
    }

    section[data-testid="stSidebar"] .stButton > button {
        width: 100%;
        border: 1px solid rgba(99, 102, 241, 0.25);
        border-radius: 10px;
        background: rgba(99, 102, 241, 0.08);
        color: #c7c9ff;
        font-weight: 500;
        padding: 0.55rem 1rem;
        margin-bottom: 4px;
        transition: all 0.2s ease;
    }

    section[data-testid="stSidebar"] .stButton > button:hover {
        background: rgba(99, 102, 241, 0.22);
        border-color: rgba(129, 132, 255, 0.5);
        transform: translateX(3px);
    }

    /* ---- Chat messages ---- */
    .stChatMessage {
        background: rgba(20, 20, 45, 0.55) !important;
        backdrop-filter: blur(12px);
        border: 1px solid rgba(99, 102, 241, 0.12);
        border-radius: 14px !important;
        padding: 1rem 1.2rem !important;
        margin-bottom: 0.6rem;
    }

    /* ---- Chat input ---- */
    .stChatInput > div {
        border: 1px solid rgba(99, 102, 241, 0.3) !important;
        border-radius: 14px !important;
        background: rgba(15, 15, 35, 0.6) !important;
    }

    .stChatInput textarea {
        color: #e0e0ff !important;
    }

    /* ---- Welcome card ---- */
    .welcome-card {
        text-align: center;
        padding: 4rem 2rem;
        max-width: 560px;
        margin: 8vh auto;
        background: rgba(20, 20, 50, 0.45);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(99, 102, 241, 0.18);
        border-radius: 20px;
    }

    .welcome-card h1 {
        font-size: 2.4rem;
        font-weight: 700;
        background: linear-gradient(135deg, #818cf8, #a78bfa, #c084fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.4rem;
    }

    .welcome-card p {
        color: #94a3b8;
        font-size: 1.05rem;
        line-height: 1.6;
    }

    /* ---- Active thread highlight ---- */
    .active-thread > button {
        background: rgba(99, 102, 241, 0.3) !important;
        border-color: #818cf8 !important;
        color: #fff !important;
        font-weight: 600 !important;
    }

    /* ---- Spinner ---- */
    .stSpinner > div {
        border-top-color: #818cf8 !important;
    }

    /* ---- Scrollbar ---- */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: rgba(99,102,241,0.3); border-radius: 3px; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def api_get(path: str):
    """GET request to the FastAPI backend."""
    try:
        r = requests.get(f"{API_BASE}{path}", timeout=10)
        r.raise_for_status()
        return r.json()
    except requests.ConnectionError:
        st.error("🔌 Cannot reach the backend. Is `uvicorn main:app` running?")
        st.stop()
    except requests.HTTPError as exc:
        st.error(f"API error: {exc.response.status_code} — {exc.response.text}")
        st.stop()


def api_post(path: str, json: dict | None = None):
    """POST request to the FastAPI backend."""
    try:
        r = requests.post(f"{API_BASE}{path}", json=json, timeout=120)
        r.raise_for_status()
        return r.json()
    except requests.ConnectionError:
        st.error("🔌 Cannot reach the backend. Is `uvicorn main:app` running?")
        st.stop()
    except requests.HTTPError as exc:
        st.error(f"API error: {exc.response.status_code} — {exc.response.text}")
        st.stop()


# ---------------------------------------------------------------------------
# Session state defaults
# ---------------------------------------------------------------------------

if "current_thread_id" not in st.session_state:
    st.session_state.current_thread_id = None


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown("### 🧠 AskFirst")
    st.caption("Universal Memory Chat")
    st.divider()

    # -- New Chat button --
    if st.button("＋  New Chat", use_container_width=True, type="primary"):
        new_thread = api_post("/threads")
        st.session_state.current_thread_id = new_thread["id"]
        st.rerun()

    st.divider()
    st.markdown("##### History")

    threads = api_get("/threads")

    if not threads:
        st.caption("No conversations yet.")
    else:
        for t in threads:
            is_active = st.session_state.current_thread_id == t["id"]
            container_class = "active-thread" if is_active else ""
            with st.container():
                if is_active:
                    st.markdown(
                        f'<div class="active-thread">',
                        unsafe_allow_html=True,
                    )
                if st.button(
                    f"💬  {t['title']}",
                    key=f"thread_{t['id']}",
                    use_container_width=True,
                ):
                    st.session_state.current_thread_id = t["id"]
                    st.rerun()
                if is_active:
                    st.markdown("</div>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Main area
# ---------------------------------------------------------------------------

current_tid = st.session_state.current_thread_id

if current_tid is None:
    # -- Welcome screen --
    st.markdown(
        """
        <div class="welcome-card">
            <h1>AskFirst</h1>
            <p>
                Your AI assistant with <strong>universal memory</strong>.<br/>
                Start a new chat from the sidebar — the AI remembers
                everything across every thread.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    # -- Fetch & render thread messages --
    messages = api_get(f"/threads/{current_tid}/messages")

    for msg in messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # -- Chat input --
    if user_input := st.chat_input("Type your message…"):
        # Immediately show the user bubble
        with st.chat_message("user"):
            st.markdown(user_input)

        # Call backend (shows spinner while waiting)
        with st.chat_message("assistant"):
            with st.spinner("Thinking…"):
                result = api_post(
                    f"/threads/{current_tid}/chat",
                    json={"message": user_input},
                )
            st.markdown(result["reply"])

        # Rerun to refresh full message list from DB
        st.rerun()
