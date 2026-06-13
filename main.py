"""
main.py — FastAPI backend with thread-isolated storage + universal LLM context.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone

from groq import Groq

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import asc
from sqlalchemy.orm import Session

from database import Message, Thread, get_db, init_db

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
if not GROQ_API_KEY:
    raise RuntimeError(
        "GROQ_API_KEY is not set. Copy .env.example → .env and add your key."
    )

_client = Groq(api_key=GROQ_API_KEY)
_MODEL = "llama-3.3-70b-versatile"

SYSTEM_INSTRUCTION = (
    "You are a helpful, concise AI assistant called AskFirst. "
    "You have access to the user's ENTIRE conversation history across all threads. "
    "Use this global memory to maintain continuity — if the user told you their name "
    "in a previous thread, remember it. Always be accurate, friendly, and brief."
)

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(title="AskFirst", version="1.0.0")


@app.on_event("startup")
def on_startup() -> None:
    init_db()


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    message: str


class ThreadOut(BaseModel):
    id: int
    title: str
    created_at: datetime

    class Config:
        from_attributes = True


class MessageOut(BaseModel):
    id: int
    thread_id: int
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class ChatResponse(BaseModel):
    reply: str


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.post("/threads", response_model=ThreadOut, status_code=201)
def create_thread(db: Session = Depends(get_db)) -> Thread:
    """Create a new conversation thread."""
    now = datetime.now(timezone.utc)
    title = f"Thread {now.strftime('%b %d, %H:%M')}"
    thread = Thread(title=title, created_at=now)
    db.add(thread)
    db.commit()
    db.refresh(thread)
    return thread


@app.get("/threads", response_model=list[ThreadOut])
def list_threads(db: Session = Depends(get_db)) -> list[Thread]:
    """Return all threads, newest first."""
    return (
        db.query(Thread)
        .order_by(Thread.created_at.desc())
        .all()
    )


@app.get("/threads/{thread_id}/messages", response_model=list[MessageOut])
def get_thread_messages(thread_id: int, db: Session = Depends(get_db)) -> list[Message]:
    """Return messages strictly for the given thread (isolated view)."""
    thread = db.query(Thread).filter(Thread.id == thread_id).first()
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found.")
    return (
        db.query(Message)
        .filter(Message.thread_id == thread_id)
        .order_by(asc(Message.created_at))
        .all()
    )


@app.post("/threads/{thread_id}/chat", response_model=ChatResponse)
def chat(thread_id: int, body: ChatRequest, db: Session = Depends(get_db)) -> dict:
    """
    1. Save user message under thread_id.
    2. Fetch ALL messages across ALL threads (universal memory).
    3. Build prompt and call Groq.
    4. Save assistant reply under thread_id.
    """
    # --- Validate thread ---
    thread = db.query(Thread).filter(Thread.id == thread_id).first()
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found.")

    # --- Persist user message ---
    user_msg = Message(
        thread_id=thread_id,
        role="user",
        content=body.message,
        created_at=datetime.now(timezone.utc),
    )
    db.add(user_msg)
    db.commit()

    # --- Build universal context from ALL threads ---
    all_messages: list[Message] = (
        db.query(Message)
        .order_by(asc(Message.created_at))
        .all()
    )

    # Build chat messages list for the Groq API
    groq_messages: list[dict] = [{"role": "system", "content": SYSTEM_INSTRUCTION}]

    for msg in all_messages:
        role = "user" if msg.role == "user" else "assistant"
        thread_label = f"[Thread {msg.thread_id}]"
        groq_messages.append({
            "role": role,
            "content": f"{thread_label} {msg.content}",
        })

    # --- Call Groq ---
    try:
        response = _client.chat.completions.create(
            model=_MODEL,
            messages=groq_messages,
            temperature=0.7,
            max_tokens=2048,
        )
        reply_text = response.choices[0].message.content.strip()
    except Exception as exc:
        # Save a graceful error reply so the thread isn't left hanging
        error_reply = f"⚠️ LLM error: {exc}"
        error_msg = Message(
            thread_id=thread_id,
            role="assistant",
            content=error_reply,
            created_at=datetime.now(timezone.utc),
        )
        db.add(error_msg)
        db.commit()
        raise HTTPException(status_code=502, detail=str(exc))

    # --- Persist assistant reply ---
    assistant_msg = Message(
        thread_id=thread_id,
        role="assistant",
        content=reply_text,
        created_at=datetime.now(timezone.utc),
    )
    db.add(assistant_msg)
    db.commit()

    return {"reply": reply_text}

