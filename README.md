# AskLawyers - AI-Powered Legal Assistant

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Google Gemini](https://img.shields.io/badge/AI-Google%20Gemini-orange.svg)](https://ai.google.dev/)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-red.svg)](https://streamlit.io/)
[![FastAPI](https://img.shields.io/badge/API-FastAPI-green.svg)](https://fastapi.tiangolo.com/)

An intelligent legal assistant powered by Google Gemini AI that provides accurate answers to questions about Indian law, specifically the Indian Penal Code (IPC).

## 🚀 Features

- **AI-Powered Responses**: Leverages Google Gemini 1.5 Flash for intelligent legal analysis
- **Document Retrieval**: Advanced document search and ranking system
- **Query Enhancement**: Automatically improves user queries for better results
- **Dual Interface**: Both web UI (Streamlit) and REST API (FastAPI) available
- **Legal Knowledge Base**: Comprehensive coverage of Indian Penal Code sections
- **Real-time Processing**: Fast response times with efficient document reranking

## 🛠️ Technology Stack

- **AI Model**: Google Gemini 1.5 Flash
- **Backend**: Python 3.11+, FastAPI
- **Frontend**: Streamlit
- **Document Processing**: LangChain, FlagEmbedding
- **Search & Ranking**: FAISS, BGE Reranker
- **Data Format**: PDF processing with PyPDF2

## 📋 Prerequisites

- Python 3.11 or higher
- Google Gemini API key ([Get one here](https://makersuite.google.com/app/apikey))
- 4GB+ RAM (for ML models)

## 🔧 Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd AskLawyers-Advance-RAG-LLM-Project
```

### 2. Set Up Virtual Environment
```bash
# Using uv (recommended)
uv venv --python 3.11
source .venv/bin/activate

# Or using standard venv
python3.11 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
# Using uv (faster)
uv pip install -r requirements.txt

# Or using pip
pip install -r requirements.txt
```

### 4. Configure API Key
Create a `.env` file in the project root:
```bash
cp .env.example .env
```

Edit `.env` and add your Gemini API key:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

## 🚀 Quick Start

### Option 1: Streamlit Web App (Recommended)
```bash
streamlit run streamlit_main.py
```
Access at: http://localhost:8501

### Option 2: FastAPI REST API
```bash
uvicorn src.main:app --host 0.0.0.0 --port 8000
```
Access at: http://localhost:8000

### Option 3: Interactive Startup Script
```bash
./start_app.sh
```

## 📖 Usage Examples

### Web Interface
1. Open the Streamlit app at http://localhost:8501
2. Select from example questions or enter your own
3. Click "Submit" to get AI-powered legal answers

### API Usage
```python
import requests

response = requests.post(
    "http://localhost:8000/",
    data={"Input": "What is IPC Section 420?"}
)
print(response.text)
```

### Sample Questions
- "What is the Indian Penal Code?"
- "What is IPC Section 420?"
- "What are the main sections in IPC?"
- "What is the punishment for cheating under IPC?"

## 📁 Project Structure

```
AskLawyers-Advance-RAG-LLM-Project/
├── src/
│   ├── main.py                 # FastAPI application
│   ├── generate_answers.py     # AI answer generation
│   ├── query_enhancement.py    # Query optimization
│   ├── data_retrieval.py       # Document retrieval
│   ├── reranker.py            # Document reranking
│   └── prompt_templates.py     # AI prompts
├── templates/
│   ├── index.html             # FastAPI web interface
│   └── script.js              # Frontend JavaScript
├── static/
│   └── styles.css             # CSS styling
├── dataset/
│   └── Indian Penal Code Book (2).pdf  # Legal documents
├── streamlit_main.py          # Streamlit application
├── requirements.txt           # Python dependencies
├── start_app.sh              # Startup script
└── README.md                 # This file
```

## ⚙️ Configuration

### Environment Variables
| Variable | Description | Required |
|----------|-------------|----------|
| `GEMINI_API_KEY` | Google Gemini API key | Yes |

### Model Configuration
The application uses the following AI models:
- **Primary AI**: Google Gemini 1.5 Flash
- **Reranker**: BAAI/bge-reranker-base
- **Embeddings**: BAAI/llm-embedder

## 🔍 How It Works

1. **Query Processing**: User input is enhanced using Gemini AI
2. **Document Retrieval**: Relevant legal documents are fetched
3. **Reranking**: Documents are reordered by relevance using BGE reranker
4. **Answer Generation**: Gemini AI generates comprehensive answers
5. **Response Delivery**: Results are presented via web interface or API

## 🧪 Testing

Test the application with sample queries:
```bash
# Test with environment variable
export GEMINI_API_KEY="your_api_key"
python -c "from src.generate_answers import generate_answer; print(generate_answer('What is IPC?'))"
```

## 🚨 Troubleshooting

### Common Issues

**"No Gemini API key found"**
- Ensure `GEMINI_API_KEY` is set in `.env` file
- Verify the API key is valid and active

**Import errors**
- Confirm Python 3.11+ is being used
- Reinstall dependencies: `uv pip install -r requirements.txt`

**Slow first response**
- ML models download on first run (normal behavior)
- Subsequent responses will be faster

**Port already in use**
- Change port: `streamlit run streamlit_main.py --server.port 8502`
- Or: `uvicorn src.main:app --port 8001`

## 📊 Performance

- **Response Time**: 2-5 seconds (after model loading)
- **Memory Usage**: ~2-4GB (including ML models)
- **Concurrent Users**: Supports multiple simultaneous requests
- **Accuracy**: High accuracy for Indian legal queries

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Google Gemini AI for powerful language processing
- LangChain for document processing framework
- FlagEmbedding for advanced text embeddings
- Streamlit and FastAPI for excellent web frameworks

## 📞 Support

For support and questions:
- Create an issue on GitHub
- Check the troubleshooting section above
- Review the configuration documentation

---

**Made with ❤️ for the legal community**
# Justice-Guide
# Justice-Guide
