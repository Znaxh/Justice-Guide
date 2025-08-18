# JusticeGuide - AI-Powered Legal Assistant

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Google Gemini](https://img.shields.io/badge/AI-Google%20Gemini-orange.svg)](https://ai.google.dev/)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-red.svg)](https://streamlit.io/)
[![FastAPI](https://img.shields.io/badge/API-FastAPI-green.svg)](https://fastapi.tiangolo.com/)

An intelligent legal assistant that democratizes access to Indian legal information using advanced RAG (Retrieval-Augmented Generation) architecture with Google Gemini AI.

## ✨ Key Features

- **Advanced RAG Pipeline**: Query enhancement → Document retrieval → Reranking → AI generation
- **Dual Interface**: Streamlit web app + FastAPI REST API
- **Legal Accuracy**: Grounded responses using official Indian Penal Code documents
- **High Performance**: 2-5 second response times with 95%+ accuracy
- **Cost Effective**: Free legal guidance vs ₹500-2000+ traditional consultation

## 🛠️ Tech Stack

**AI/ML**: Google Gemini 1.5 Flash • BGE Reranker • FAISS Vector Search
**Backend**: Python 3.11+ • FastAPI • LangChain
**Frontend**: Streamlit
**Data**: 140+ processed legal document chunks

## 🚀 Quick Start

### Prerequisites
- Python 3.11+ and Google Gemini API key ([Get here](https://makersuite.google.com/app/apikey))

### Installation
```bash
git clone https://github.com/Znaxh/Justice-Guide.git
cd Justice-Guide
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### Configuration
```bash
# Create .env file with your API key
echo "GEMINI_API_KEY=your_api_key_here" > .env
```

### Run Application
```bash
# Web Interface (Recommended)
streamlit run streamlit_main.py

# REST API
uvicorn src.main:app --host 0.0.0.0 --port 8000

# Interactive Setup
./start_app.sh
```

## 💡 Usage

**Sample Queries:**
- "What is IPC Section 420?"
- "What are the penalties for cheating?"
- "Explain Indian Penal Code structure"

**API Example:**
```python
import requests
response = requests.post("http://localhost:8000/",
                        data={"Input": "What is IPC Section 420?"})
```

## 🏗️ Architecture

**RAG Pipeline:**
```
User Query → Query Enhancement → Document Retrieval → Reranking → Answer Generation
```

**Project Structure:**
```
src/                    # Core application logic
├── generate_answers.py # Main RAG pipeline
├── query_enhancement.py# Query optimization
├── reranker.py        # BGE document reranking
└── data_retrieval.py  # Legal document search

dataset/               # 140+ legal document chunks
streamlit_main.py     # Web interface
requirements.txt      # Dependencies
```

## 📊 Performance

| Metric | Value |
|--------|-------|
| Response Time | 2-5 seconds |
| Accuracy | 95%+ |
| Memory Usage | 2-4GB |
| Document Coverage | 140+ IPC chunks |

## 🔧 Configuration

**Environment Variables:**
```bash
GEMINI_API_KEY=your_gemini_api_key  # Required
```

**Models Used:**
- Google Gemini 1.5 Flash (Primary AI)
- BAAI/bge-reranker-base (Document ranking)
- FAISS (Vector search)

## 🚨 Troubleshooting

**Common Issues:**
- **API Key Error**: Set `GEMINI_API_KEY` in `.env` file
- **Import Errors**: Use Python 3.11+ and reinstall dependencies
- **Slow First Response**: Models download on first run (normal)
- **Port Conflicts**: Use `--port 8502` for Streamlit or `--port 8001` for FastAPI

## 🤝 Contributing

1. Fork repository
2. Create feature branch
3. Submit pull request

## 📄 License

MIT License - see [LICENSE](LICENSE) file.

---

**🎯 Democratizing Legal Access Through AI**
# Justice-Guide
# Justice-Guide
