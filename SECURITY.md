# Security Policy

## 🔒 Protecting Sensitive Information

This project handles sensitive information including API keys and potentially confidential legal documents. Please follow these security guidelines:

### 🚨 Never Commit These Files

- `.env` - Contains your actual API keys
- `secrets.txt` - Any file containing passwords or tokens
- `*.pem` - Private key files
- `*.key` - Certificate or key files
- `config.json` - Configuration files with sensitive data
- `credentials.json` - Authentication credentials

### ✅ Safe to Commit

- `.env.example` - Template file without actual secrets
- `README.md` - Documentation
- Source code files (without hardcoded secrets)
- `requirements.txt` - Dependencies list

### 🔐 API Key Security

1. **Never hardcode API keys** in source code
2. **Use environment variables** via `.env` file
3. **Rotate API keys regularly**
4. **Limit API key permissions** to minimum required
5. **Monitor API key usage** for unusual activity

### 📁 File Protection

The `.gitignore` file is configured to protect:

- Environment variables (`.env*`)
- API keys and secrets (`*.key`, `secrets.txt`)
- Private certificates (`*.pem`, `*.p12`)
- Database files (`*.db`, `*.sqlite`)
- Temporary files (`temp/`, `*.tmp`)
- Model cache and downloads
- User uploads and generated content

### 🛡️ Best Practices

1. **Environment Setup**:
   ```bash
   cp .env.example .env
   # Edit .env with your actual API key
   # Never commit .env to git
   ```

2. **Check Before Committing**:
   ```bash
   git status
   # Ensure no sensitive files are staged
   ```

3. **Remove Accidentally Committed Secrets**:
   ```bash
   # If you accidentally commit secrets, remove them immediately
   git rm --cached .env
   git commit -m "Remove accidentally committed secrets"
   # Then rotate the compromised API keys
   ```

### 🚨 Incident Response

If you accidentally commit sensitive information:

1. **Immediately rotate** all exposed API keys
2. **Remove the sensitive data** from git history
3. **Force push** the cleaned history (if safe to do so)
4. **Notify team members** if working in a team

### 📞 Reporting Security Issues

If you discover a security vulnerability, please:

1. **Do not** create a public issue
2. **Email** the maintainers directly
3. **Provide** detailed information about the vulnerability
4. **Allow** reasonable time for response before disclosure

### 🔍 Security Checklist

Before deploying or sharing:

- [ ] No API keys in source code
- [ ] `.env` file is not committed
- [ ] All secrets are in environment variables
- [ ] `.gitignore` is properly configured
- [ ] No sensitive data in logs
- [ ] API keys have minimal required permissions

---

**Remember: Security is everyone's responsibility!** 🛡️
