# Changelog

## [2.0.0] - 2024-12-19

### 🚀 Major Changes
- **BREAKING**: Migrated from OpenAI to Google Gemini API
- **BREAKING**: Removed all AWS dependencies (Kendra, Secrets Manager, S3)
- **BREAKING**: Upgraded Python requirement to 3.11+

### ✅ Added
- Google Gemini 1.5 Flash integration
- Professional README.md with comprehensive documentation
- MIT License
- Comprehensive .gitignore
- Interactive startup script (`start_app.sh`)
- Environment variable configuration via .env file
- Automatic .env file loading with python-dotenv

### ❌ Removed
- OpenAI API dependencies
- AWS boto3 and related services
- Docker configuration files
- Unnecessary utility files
- Cache directories and temporary files
- Development/testing scripts

### 🔧 Improved
- Simplified installation process
- Better error handling and fallbacks
- Cleaner project structure
- Enhanced documentation
- Professional code organization

### 📁 Final Project Structure
```
AskLawyers-Advance-RAG-LLM-Project/
├── src/                    # Core application code
├── templates/              # FastAPI web templates
├── static/                 # CSS and static assets
├── dataset/                # Legal documents
├── streamlit_main.py       # Streamlit application
├── requirements.txt        # Python dependencies
├── start_app.sh           # Interactive startup script
├── README.md              # Professional documentation
├── LICENSE                # MIT License
├── CHANGELOG.md           # This file
└── .gitignore             # Git ignore rules
```

### 🎯 Benefits
- **Cost Reduction**: No AWS charges
- **Simplified Setup**: Only requires Gemini API key
- **Local Development**: No cloud dependencies
- **Better Performance**: Faster response times with Gemini
- **Professional Structure**: Clean, maintainable codebase

### 🔄 Migration Notes
- Users need to obtain a Google Gemini API key
- Environment variables are now loaded from .env file
- All functionality preserved with improved performance
- Documentation updated with clear setup instructions
