# Protected Files Summary

This document lists all the file types and patterns that are protected by the `.gitignore` file to prevent accidental commits of sensitive information.

## 🔐 Sensitive Files (Never Committed)

### API Keys & Credentials
- `.env` - Environment variables with API keys
- `.env.*` - All environment variable files (except .env.example)
- `*.key` - Private key files
- `*.pem` - Certificate files
- `*.p12`, `*.pfx` - Certificate bundles
- `api_keys.txt` - Text files with API keys
- `credentials.json` - JSON credential files
- `service-account.json` - Service account credentials
- `secrets/` - Directory containing secrets

### Configuration Files
- `config.ini` - Configuration files
- `config.json` - JSON configuration files
- `src/.env` - Environment files in source directory

### Security Files
- `secrets.txt` - Any secrets text file
- `passwords.txt` - Password files
- `tokens.txt` - Token files
- `private_keys/` - Private key directory
- `ssl_certs/` - SSL certificate directory

## 🗂️ Development Files (Hidden)

### Python Cache
- `__pycache__/` - Python bytecode cache
- `*.py[cod]` - Compiled Python files
- `*.so` - Shared object files

### Virtual Environments
- `.venv/` - Virtual environment directory
- `venv/` - Alternative venv directory
- `ENV/`, `env/` - Environment directories

### IDE Files
- `.vscode/` - VS Code settings
- `.idea/` - PyCharm/IntelliJ settings
- `*.swp`, `*.swo` - Vim swap files

### OS Files
- `.DS_Store` - macOS metadata
- `Thumbs.db` - Windows thumbnails
- `._*` - macOS resource forks

## 📊 Data Files (Hidden)

### Databases
- `*.db`, `*.sqlite`, `*.sqlite3` - Database files
- `data/`, `database/` - Data directories
- `backups/` - Backup directories

### Spreadsheets
- `*.csv`, `*.xlsx`, `*.xls` - Data files

### Large Media Files
- `*.mp4`, `*.avi`, `*.mov` - Video files
- `*.mp3`, `*.wav`, `*.flac` - Audio files
- `*.zip`, `*.tar.gz`, `*.rar` - Archive files

## 🤖 AI Model Files (Hidden)

### Model Cache
- `.cache/` - General cache directory
- `models/` - Model storage directory
- `*.model`, `*.bin` - Model files
- `*.safetensors`, `*.onnx` - Model formats
- `*.pt`, `*.pth`, `*.h5` - PyTorch/TensorFlow models
- `huggingface_cache/` - HuggingFace cache
- `transformers_cache/` - Transformers cache
- `sentence_transformers/` - Sentence transformers cache

## 🧪 Development & Testing (Hidden)

### Temporary Files
- `temp/`, `tmp/` - Temporary directories
- `*.tmp`, `*.temp` - Temporary files
- `test_files/`, `scratch/` - Test directories
- `*_test.py`, `*_temp.py` - Test files

### Logs & Debug
- `*.log` - Log files
- `logs/` - Log directory
- `debug.log`, `error.log` - Debug files
- `profile_*`, `memory_*` - Profiling files

### Generated Content
- `uploads/`, `downloads/` - User content
- `generated/`, `output/`, `results/` - Generated files

## ✅ Safe Files (Committed)

### Templates & Examples
- `.env.example` - Environment template (explicitly allowed)
- `README.md` - Documentation
- `requirements.txt` - Dependencies
- Source code files (without hardcoded secrets)

### Documentation
- `*.md` - Markdown documentation
- `LICENSE` - License file
- `CHANGELOG.md` - Version history

### Configuration Templates
- Template files without actual secrets
- Example configuration files

---

**Remember**: The `.gitignore` file protects you from accidentally committing sensitive information, but always double-check before committing!
