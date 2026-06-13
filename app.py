"""
app.py — AskFirst: Self-contained Streamlit app with universal memory.
Deploy directly on Streamlit Community Cloud.
Run locally:  streamlit run app.py
"""

from __future__ import annotations

import os
from datetime import datetime, timezone

import streamlit as st
from groq import Groq
from sqlalchemy import asc
from sqlalchemy.orm import Session

from database import Message, Thread, SessionLocal, init_db

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="AskFirst — AI Chat",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Init DB on first import
# ---------------------------------------------------------------------------
init_db()

# ---------------------------------------------------------------------------
# Groq client (reads from st.secrets on Cloud, .env locally)
# ---------------------------------------------------------------------------

def _get_groq_key() -> str:
    """Resolve GROQ_API_KEY from Streamlit secrets (cloud) or env var (local)."""
    try:
        return st.secrets["GROQ_API_KEY"]
    except (FileNotFoundError, KeyError):
        from dotenv import load_dotenv
        load_dotenv()
        key = os.getenv("GROQ_API_KEY", "")
        if not key:
            st.error("🔑 GROQ_API_KEY not set. Add it to `.streamlit/secrets.toml` or `.env`.")
            st.stop()
        return key


_client = Groq(api_key=_get_groq_key())
_MODEL = "llama-3.3-70b-versatile"

SYSTEM_INSTRUCTION = (
    "You are a helpful, concise AI assistant called AskFirst. "
    "You have access to the user's ENTIRE conversation history across all threads. "
    "Use this global memory to maintain continuity — if the user told you their name "
    "in a previous thread, remember it. Always be accurate, friendly, and brief."
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
# Data helpers (direct DB calls, no HTTP)
# ---------------------------------------------------------------------------

def create_thread() -> dict:
    """Create a new thread and return its id + title."""
    db: Session = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        thread = Thread(title=f"Thread {now.strftime('%b %d, %H:%M')}", created_at=now)
        db.add(thread)
        db.commit()
        db.refresh(thread)
        return {"id": thread.id, "title": thread.title}
    finally:
        db.close()


def list_threads() -> list[dict]:
    """Return all threads, newest first."""
    db: Session = SessionLocal()
    try:
        rows = db.query(Thread).order_by(Thread.created_at.desc()).all()
        return [{"id": t.id, "title": t.title} for t in rows]
    finally:
        db.close()


def get_thread_messages(thread_id: int) -> list[dict]:
    """Return messages for a specific thread."""
    db: Session = SessionLocal()
    try:
        rows = (
            db.query(Message)
            .filter(Message.thread_id == thread_id)
            .order_by(asc(Message.created_at))
            .all()
        )
        return [{"role": m.role, "content": m.content} for m in rows]
    finally:
        db.close()


def chat(thread_id: int, user_text: str) -> str:
    """
    Save user message, build universal context, call Groq, save reply.
    Returns the assistant's reply text.
    """
    db: Session = SessionLocal()
    try:
        # Persist user message
        db.add(Message(
            thread_id=thread_id,
            role="user",
            content=user_text,
            created_at=datetime.now(timezone.utc),
        ))
        db.commit()

        # Build universal context from ALL threads
        all_msgs = db.query(Message).order_by(asc(Message.created_at)).all()

        groq_messages: list[dict] = [
            {"role": "system", "content": SYSTEM_INSTRUCTION}
        ]
        for msg in all_msgs:
            role = "user" if msg.role == "user" else "assistant"
            groq_messages.append({
                "role": role,
                "content": f"[Thread {msg.thread_id}] {msg.content}",
            })

        # Call Groq
        try:
            response = _client.chat.completions.create(
                model=_MODEL,
                messages=groq_messages,
                temperature=0.7,
                max_tokens=2048,
            )
            reply_text = response.choices[0].message.content.strip()
        except Exception as exc:
            reply_text = f"⚠️ LLM error: {exc}"

        # Persist assistant reply
        db.add(Message(
            thread_id=thread_id,
            role="assistant",
            content=reply_text,
            created_at=datetime.now(timezone.utc),
        ))
        db.commit()

        return reply_text
    finally:
        db.close()


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
        new_thread = create_thread()
        st.session_state.current_thread_id = new_thread["id"]
        st.rerun()

    st.divider()
    st.markdown("##### History")

    threads = list_threads()

    if not threads:
        st.caption("No conversations yet.")
    else:
        for t in threads:
            is_active = st.session_state.current_thread_id == t["id"]
            with st.container():
                if is_active:
                    st.markdown(
                        '<div class="active-thread">',
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
    messages = get_thread_messages(current_tid)

    for msg in messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # -- Chat input --
    if user_input := st.chat_input("Type your message…"):
        # Immediately show the user bubble
        with st.chat_message("user"):
            st.markdown(user_input)

        # Call Groq directly (shows spinner while waiting)
        with st.chat_message("assistant"):
            with st.spinner("Thinking…"):
                reply = chat(current_tid, user_input)
            st.markdown(reply)

        # Rerun to refresh full message list from DB
        st.rerun()
