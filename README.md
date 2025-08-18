# JusticeGuide - AI Legal Assistant

An intelligent legal assistant powered by Google Gemini AI that provides accurate answers to questions about Indian law, specifically the Indian Penal Code (IPC).

## Features

- AI-powered responses using Google Gemini 1.5 Flash
- Advanced document search and ranking system
- Automatic query enhancement for better results
- Dual interface: Web UI (Streamlit) and REST API (FastAPI)
- Comprehensive Indian Penal Code knowledge base
- Real-time processing with efficient document reranking

## Technology Stack

- AI Model: Google Gemini 1.5 Flash
- Backend: Python 3.11+, FastAPI
- Frontend: Streamlit
- Document Processing: LangChain, FlagEmbedding
- Search & Ranking: FAISS, BGE Reranker
- Data Format: PDF processing with PyPDF2

## Prerequisites

- Python 3.11 or higher
- Google Gemini API key
- 4GB+ RAM for ML models

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd JusticeGuide
```

2. Set up virtual environment:
```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure API key:
Create a `.env` file in the project root:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

## Usage

### Streamlit Web Application
```bash
streamlit run streamlit_main.py
```
Access at: http://localhost:8501

### FastAPI REST API
```bash
uvicorn src.main:app --host 0.0.0.0 --port 8000
```
Access at: http://localhost:8000

### API Example
```python
import requests

response = requests.post(
    "http://localhost:8000/",
    data={"Input": "What is IPC Section 420?"}
)
print(response.text)
```

### Sample Queries
- "What is the Indian Penal Code?"
- "What are the different sections in IPC?"
- "What is IPC Section 420?"
- "What is the punishment for cheating under IPC?"

## Project Structure

```
JusticeGuide/
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
└── requirements.txt           # Python dependencies
```

## Configuration

### Environment Variables
| Variable | Description | Required |
|----------|-------------|----------|
| `GEMINI_API_KEY` | Google Gemini API key | Yes |

### AI Models
- Primary AI: Google Gemini 1.5 Flash
- Reranker: BAAI/bge-reranker-base
- Embeddings: BAAI/llm-embedder

## How It Works

1. Query Processing: User input is enhanced using Gemini AI
2. Document Retrieval: Relevant legal documents are fetched using FAISS
3. Reranking: Documents are reordered by relevance using BGE reranker
4. Answer Generation: Gemini AI generates comprehensive answers
5. Response Delivery: Results are presented via web interface or API

## Testing

Test the application:
```bash
export GEMINI_API_KEY="your_api_key"
python -c "from src.generate_answers import generate_answer; print(generate_answer('What is IPC?'))"
```

## Troubleshooting

**"No Gemini API key found"**
- Ensure `GEMINI_API_KEY` is set in `.env` file
- Verify the API key is valid and active

**Import errors**
- Confirm Python 3.11+ is being used
- Reinstall dependencies: `pip install -r requirements.txt`

**Slow first response**
- ML models download on first run (normal behavior)
- Subsequent responses will be faster

**Port already in use**
- Change port: `streamlit run streamlit_main.py --server.port 8502`
- Or: `uvicorn src.main:app --port 8001`

## Performance

- Response Time: 2-5 seconds (after model loading)
- Memory Usage: ~2-4GB (including ML models)
- Concurrent Users: Supports multiple simultaneous requests
- Accuracy: High accuracy for Indian legal queries

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
