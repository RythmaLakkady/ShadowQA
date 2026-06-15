# 🎯 ShadowQA — Universal API Chaos Agent

An AI-driven Automated API Chaos Testing Engine. Instead of relying on manual QA scripts to uncover boundary errors and validation exploits, ShadowQA leverages High-Throughput LLMs to parse endpoint requirements, construct malicious test vectors, execute live payloads, and audit structural system stability.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| App | Streamlit |
| Database | SQLite |
| LLM | Groq (Llama 3.3 70B Versatile) |

## Features

- **Automated AI Generation Matrix**: Provide an API Endpoint URL, Method, and Schema Description. The AI will automatically generate exact structured test vectors split across:
  - **Happy Path**: Clean data expecting 200/201 success codes.
  - **Edge Case**: Boundary testing, negative indexes, missing keys expecting 400.
  - **Chaos Path**: Malicious payloads, SQL injections, and type coercion threats.
- **Secure Authentication Layer**: Built-in user registration and login system.
- **Live Auditing & Execution Engine**: Fires the test vectors sequentially against the target endpoint and tracks network latency, HTTP status codes, and determines vulnerability (e.g., data leaks, unhandled crashes).
- **Historical Vulnerability Audits**: Persistent history tracking using SQLite to see pass/fail rates across sessions.

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

## Project Structure

```
askfirst/
├── app.py            # Self-contained Streamlit application (UI + Logic)
├── requirements.txt  # Dependencies
├── .env.example      # API key template
└── .gitignore
```

## License

MIT
