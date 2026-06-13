# 🧠 AskFirst — AI Chat with Universal Memory

A multi-threaded AI chat application where each conversation thread is visually isolated, but the AI maintains **universal memory across all threads**.

> Tell the AI your name in Thread 1 → Start Thread 2 (blank UI) → The AI still remembers your name.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| App | Streamlit |
| Database | SQLite + SQLAlchemy |
| LLM | Groq (Llama 3.3 70B) |

## How It Works

- **UI & Storage Isolation**: Messages are stored per-thread. The UI only displays messages belonging to the selected thread.
- **Universal LLM Context**: When generating a response, the app fetches **all messages from all threads**, constructs a chronological global context, and sends it to the LLM — giving the AI perfect cross-thread memory.

## Setup

### 1. Clone & Install

```bash
git clone https://github.com/RythmaLakkady/minichatbot.git
cd minichatbot
pip install -r requirements.txt
```

### 2. Configure API Key

```bash
cp .env.example .env
# Edit .env and add your Groq API key
```

Get a free API key at [console.groq.com](https://console.groq.com).

### 3. Run

```bash
streamlit run app.py
```

Open **http://localhost:8501** in your browser.

## Deploy on Streamlit Community Cloud

1. Push this repo to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io) and connect your repo.
3. Set the main file to `app.py`.
4. Add your `GROQ_API_KEY` under **Advanced settings → Secrets**:
   ```toml
   GROQ_API_KEY = "gsk_your_key_here"
   ```
5. Deploy!

## Project Structure

```
askfirst/
├── app.py            # Self-contained Streamlit app (UI + DB + LLM)
├── database.py       # SQLAlchemy models (Thread, Message)
├── requirements.txt  # Dependencies
├── .env.example      # API key template
└── .gitignore
```

## License

MIT
