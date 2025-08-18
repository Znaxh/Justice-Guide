#!/bin/bash

# AskLawyers Startup Script with Gemini Integration

echo "🚀 Starting AskLawyers with Gemini API..."
echo "=========================================="

# Check if API key is provided
if [ -z "$GEMINI_API_KEY" ]; then
    echo "❌ Error: GEMINI_API_KEY environment variable is not set!"
    echo ""
    echo "Please set your Gemini API key:"
    echo "export GEMINI_API_KEY='your_api_key_here'"
    echo ""
    echo "Or run with API key:"
    echo "./start_app.sh your_api_key_here"
    echo ""
    exit 1
fi

# If API key is provided as argument, use it
if [ ! -z "$1" ]; then
    export GEMINI_API_KEY="$1"
    echo "✅ Using API key from command line argument"
else
    echo "✅ Using API key from environment variable"
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source .venv/bin/activate

# Check if dependencies are installed
echo "🔍 Checking dependencies..."
python -c "import google.generativeai" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "📥 Installing dependencies..."
    uv pip install -r requirements.txt
fi

# Test the integration
echo "🧪 Testing Gemini integration..."
python -c "
from src.generate_answers import generate_answer
result = generate_answer('test')
if 'Error: Gemini API key not configured' in result:
    print('❌ API key test failed')
    exit(1)
else:
    print('✅ API key test passed')
"

if [ $? -ne 0 ]; then
    echo "❌ API key validation failed. Please check your key."
    exit 1
fi

echo ""
echo "🎉 Setup complete! Choose an option:"
echo "1. Streamlit App (recommended)"
echo "2. FastAPI App"
echo "3. Both apps"
echo ""
read -p "Enter your choice (1/2/3): " choice

case $choice in
    1)
        echo "🚀 Starting Streamlit app..."
        streamlit run streamlit_main.py
        ;;
    2)
        echo "🚀 Starting FastAPI app..."
        uvicorn src.main:app --host 0.0.0.0 --port 8000
        ;;
    3)
        echo "🚀 Starting both apps..."
        echo "Streamlit: http://localhost:8501"
        echo "FastAPI: http://localhost:8000"
        streamlit run streamlit_main.py &
        uvicorn src.main:app --host 0.0.0.0 --port 8000
        ;;
    *)
        echo "❌ Invalid choice. Please run the script again."
        exit 1
        ;;
esac
