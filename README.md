# 🎯 ShadowQA — Universal API Chaos Agent

An AI-driven **Automated API Chaos Testing Engine** with **RAG-powered vulnerability analysis** and **intelligent coverage mapping**. ShadowQA leverages High-Throughput LLMs to parse API endpoints and generate comprehensive test vectors that uncover boundary errors, validation exploits, and security vulnerabilities—all without manual QA scripts.

## ✨ Key Features

### 🎪 **Automated AI Generation Matrix**
Provide an API Endpoint URL, Method, and Schema Description. The AI will automatically generate exact structured test vectors split across:
- **Happy Path**: Clean data expecting 200/201 success codes
- **Edge Case**: Boundary testing, negative indexes, missing keys expecting 400
- **Chaos Path**: Malicious payloads, SQL injections, and type coercion threats

### 🧠 **Root Cause Analyzer (RAG-Powered)**
Leverages Retrieval-Augmented Generation (RAG) with ChromaDB to:
- Analyze failure patterns from historical test runs
- Generate insightful explanations for vulnerabilities
- Identify root causes of API crashes and data leaks
- Reference similar past vulnerabilities for context

### 🕵️‍♂️ **Coverage Analyzer**
Intelligent analysis of API endpoint testing coverage:
- Tracks which endpoints have been tested
- Measures test completeness across endpoints
- Recommends high-priority areas for additional testing
- Visualizes coverage gaps

### 🔐 **Secure Authentication Layer**
Built-in user registration and login system with SHA-256 password hashing.

### 📊 **Live Auditing & Execution Engine**
Fires the test vectors sequentially against the target endpoint and tracks:
- Network latency
- HTTP status codes
- Vulnerability detection (data leaks, crashes, unhandled errors)

### 📈 **Historical Vulnerability Audits**
Persistent history tracking using SQLite to see:
- Pass/fail rates across sessions
- Vulnerability trends over time
- Detailed test execution logs

## 🏗️ Architecture

### **Modular Structure** (v2.0+)
```
ShadowQA/
├── app.py                  # Main Streamlit application entry point
├── core/                   # Core business logic
│   ├── llm_engine.py      # LLM prompt engineering & API integration
│   ├── rag_engine.py      # RAG-based vulnerability analysis
│   ├── test_runner.py     # Test execution orchestration
│   └── coverage.py        # Coverage analysis logic
├── database/              # Data persistence layer
│   └── db.py              # SQLite ORM & query functions
├── ui/                    # User interface layer
│   ├── tabs.py            # Tab renderers (5 main views)
│   ├── components.py      # Reusable UI components
│   └── auth.py            # Authentication UI (optional)
├── requirements.txt       # Python dependencies
├── .env.example          # API key template
└── .gitignore
```

### **Tech Stack**

| Layer | Technology |
|-------|-----------|
| **UI** | Streamlit 1.41.1 |
| **Backend** | Python 3.8+ |
| **LLM** | Groq API (Llama 3.3 70B) |
| **RAG** | LangChain + ChromaDB + Sentence-Transformers |
| **Database** | SQLite3 |
| **HTTP Client** | httpx 0.27.0 |

## 📋 Setup & Installation

### 1. Clone & Install

```bash
git clone https://github.com/RythmaLakkady/ShadowQA.git
cd ShadowQA
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

## 🎮 Usage Guide

### **View 1: Onboarding Hub** (ℹ️)
- Introduction to ShadowQA architecture
- System connectivity status
- Workflow overview

### **View 2: Chaos Console** (🎯)
1. Enter target API endpoint URL
2. Select HTTP method (POST, PUT, GET)
3. Describe API schema in natural language
4. Click "Initialize AI Generation Matrix" to generate 15 test vectors
5. Click "Fire Automated Testing Payloads" to execute tests
6. View results with latency metrics and vulnerability detection

### **View 3: Root Cause Analyzer** (🧠)
- Select a past test session
- Analyze failure patterns using RAG
- Get AI-powered explanations of vulnerabilities
- Reference similar past incidents

### **View 4: Coverage Analyzer** (🕵️‍♂️)
- View testing coverage across endpoints
- Identify gaps in test coverage
- Get recommendations for priority testing areas
- Track coverage trends

### **View 5: History & Audits** (📊)
- Browse all past test sessions
- Expand sessions to view detailed results
- Track vulnerability rate trends
- Export historical data for analysis

## 🔧 Extending ShadowQA

### Add a New LLM Provider
Edit `core/llm_engine.py`:
```python
def generate_test_vectors(endpoint_url, method, schema_desc, provider="groq"):
    if provider == "openai":
        # Add OpenAI integration here
        pass
    elif provider == "anthropic":
        # Add Anthropic integration here
        pass
```

### Add Custom Test Templates
Modify the system prompt in `core/llm_engine.py` to include your custom test patterns.

### Enhance Vulnerability Detection
Update the status code logic in `core/test_runner.py` to add new detection rules:
```python
if status_code == 403:
    result_status = "VULNERABILITY_UNAUTHORIZED_ACCESS"
```

### Add New Analysis Views
Create a new function in `ui/tabs.py`:
```python
def render_my_new_view(groq_client):
    st.title("My New Analysis")
    # Add your UI here
```

Then register it in `app.py` navigation.

## 📦 Dependencies

```
streamlit==1.41.1           # Web UI framework
groq==0.4.2                 # Groq API client
python-dotenv==1.0.1        # Environment variable management
httpx==0.27.0               # HTTP client library
langchain==0.1.16           # RAG & LLM orchestration
langchain-community==0.0.34 # Community integrations
sentence-transformers==2.7.0 # Embedding models
chromadb==0.4.24            # Vector database for RAG
```

## 📝 Recent Updates (v2.0)

✅ **Modular Architecture** - Separated concerns into core, database, and UI layers  
✅ **RAG Integration** - ChromaDB-powered vulnerability analysis  
✅ **Coverage Analyzer** - Intelligent endpoint coverage mapping  
✅ **LangChain Integration** - Enterprise-grade LLM orchestration  
✅ **Improved Dependencies** - Upgraded to latest stable versions  
✅ **Enhanced Documentation** - Comprehensive README and code comments

## 🐛 Known Limitations

- Single sequential test execution (no concurrency yet)
- Status code-based vulnerability detection only (no response body parsing)
- Groq-only LLM support (multi-LLM coming soon)
- No request/response body logging
- SQLite only (no PostgreSQL/MongoDB support yet)

## 🚀 Roadmap

- [ ] Async/concurrent test execution
- [ ] Advanced response analysis (body parsing, regex matching)
- [ ] Multi-LLM provider support (OpenAI, Anthropic, Local)
- [ ] Webhook notifications (Slack, Teams, Discord)
- [ ] PDF/Excel export for reports
- [ ] Docker containerization
- [ ] CI/CD integration (GitHub Actions, GitLab CI)
- [ ] Distributed test execution

## 📄 License

MIT

## 👤 Author

[RythmaLakkady](https://github.com/RythmaLakkady)

---

**For questions or issues, please open a GitHub issue or contact the maintainers.**
