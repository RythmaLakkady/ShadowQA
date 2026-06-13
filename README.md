# 🧠 AskFirst — AI Chat with Universal Memory

A multi-threaded AI chat application where each conversation thread is visually isolated, but the AI maintains **universal memory across all threads**.

> Tell the AI your name in Thread 1 → Start Thread 2 (blank UI) → The AI still remembers your name.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI + Uvicorn |
| Database | SQLite + SQLAlchemy |
| Frontend | Streamlit |
| LLM | Groq (Llama 3.3 70B) |

## How It Works

- **UI & Storage Isolation**: Messages are stored per-thread. The UI only displays messages belonging to the selected thread.
- **Universal LLM Context**: When generating a response, the backend fetches **all messages from all threads**, constructs a chronological global context, and sends it to the LLM — giving the AI perfect cross-thread memory.

## Setup

### 1. Clone & Install

```bash
git clone https://github.com/<your-username>/askfirst.git
cd askfirst
pip install -r requirements.txt
```

### 2. Configure API Key

```bash
cp .env.example .env
# Edit .env and add your Groq API key
```

Get a free API key at [console.groq.com](https://console.groq.com).

### 3. Run

Start the backend:
```bash
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Start the frontend (in a second terminal):
```bash
python -m streamlit run app.py
```

Open **http://localhost:8501** in your browser.

## Project Structure

```
askfirst/
├── main.py           # FastAPI backend (4 endpoints + Groq LLM)
├── database.py       # SQLAlchemy models (Thread, Message)
├── app.py            # Streamlit frontend (dark glassmorphism UI)
├── requirements.txt  # Pinned dependencies
├── .env.example      # API key template
└── .gitignore
```

## License

MIT
