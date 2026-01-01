# Security Policy

## Reporting Security Vulnerabilities

**Please do not report security vulnerabilities through public GitHub issues.**

If you discover a security vulnerability in GridBot Chuck, please report it to us privately:

1. **Email**: Send details to the repository maintainer (check GitHub profile)
2. **Include**:
   - Description of the vulnerability
   - Steps to reproduce the issue
   - Potential impact
   - Suggested fix (if any)

We will respond within 48 hours and work with you to understand and address the issue.

## Security Best Practices for Users

### API Keys & Secrets

**Critical Security Rules:**

- ❌ **NEVER** commit `.env` files to version control
- ❌ **NEVER** share API keys publicly or in screenshots
- ❌ **NEVER** use API keys with withdrawal permissions
- ✅ **ALWAYS** use `.env` file for secrets (already in `.gitignore`)
- ✅ **ALWAYS** use exchange API keys with minimal permissions (trading only)
- ✅ **ALWAYS** enable IP whitelisting on your exchange accounts
- ✅ **ALWAYS** enable 2FA on all exchange accounts

### API Key Configuration

1. **Create `.env` file** (copy from `.env.example`):
   ```bash
   cp .env.example .env
   ```

2. **Set secure API key for bot dashboard**:
   ```env
   GRIDBOT_API_KEY=your-secure-random-key-here
   ```
   Generate a secure key:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

3. **Configure exchange API keys**:
   ```env
   EXCHANGE_API_KEY=your_exchange_key
   EXCHANGE_SECRET_KEY=your_exchange_secret
   ```

### Network Security

**Dashboard Access:**

- The web dashboard runs on `http://localhost:8080` by default
- **Only accessible from your local machine** by default
- To allow remote access, configure `ALLOWED_ORIGINS`:
  ```env
  ALLOWED_ORIGINS=http://your-ip:8080,http://localhost:8080
  ```
- **WARNING**: Remote access exposes your bot to network attacks
- Use VPN or SSH tunnel for secure remote access instead

**API Security:**

- All API endpoints (except `/api/health`) require authentication
- Include API key in requests:
  - Header: `Authorization: Bearer <your-api-key>`
  - Or query param: `?api_key=<your-api-key>`

### File Permissions

Protect sensitive files on Linux/Mac:
```bash
chmod 600 .env
chmod 600 data/*.db
```

### Database Security

- Database files (`*.db`) are excluded from git
- Contains trade history and order data
- Backup regularly but keep backups secure
- Never share database files publicly

## Security Features

### Authentication & Authorization

- **API Key Authentication**: All API endpoints require valid API key
- **Constant-Time Comparison**: Prevents timing attacks on API key verification
- **Auto-Generated Keys**: Temporary keys generated if not configured

### Input Validation

- **SQL Injection Protection**: Parameterized queries for all database operations
- **Path Traversal Protection**: File path validation prevents directory traversal
- **Trading Pair Validation**: Strict format validation (e.g., BTC/USD)
- **Numeric Validation**: Type checking and range validation for all numbers

### Rate Limiting

- **60 requests per minute** per IP address (default)
- **10 request burst** allowance
- **Automatic cooldown** with retry-after headers
- **IP-based tracking** to prevent abuse

### Web Security

- **Content Security Policy (CSP)**: Prevents XSS attacks
- **X-Frame-Options**: Prevents clickjacking
- **X-Content-Type-Options**: Prevents MIME sniffing
- **CORS Restrictions**: Only allowed origins can access API
- **Input Sanitization**: All user inputs sanitized before use

### Dependency Security

- **Regular Updates**: Dependencies updated regularly
- **Security Scanning**: Run `pip-audit` to check for vulnerabilities:
  ```bash
  pip install pip-audit
  pip-audit
  ```

## Secure Deployment Checklist

Before running in production:

- [ ] Set strong `GRIDBOT_API_KEY` in `.env`
- [ ] Configure `ALLOWED_ORIGINS` if allowing remote access
- [ ] Enable exchange API IP whitelisting
- [ ] Use trading-only API keys (no withdrawal permissions)
- [ ] Enable 2FA on all exchange accounts
- [ ] Start with paper trading mode to test
- [ ] Set up file permissions (`chmod 600 .env`)
- [ ] Configure firewall to block external access to port 8080
- [ ] Review and test with small capital first
- [ ] Set up monitoring and alerts
- [ ] Backup database regularly

## Secure Coding Practices (For Contributors)

When contributing to GridBot Chuck:

1. **Never hardcode secrets** - Use environment variables
2. **Validate all inputs** - Use `InputValidator` class
3. **Use parameterized queries** - Never string interpolation in SQL
4. **Sanitize file paths** - Use `validate_path()` for file operations
5. **Add security tests** - Test authentication, validation, rate limiting
6. **Follow principle of least privilege** - Minimal permissions everywhere
7. **Log security events** - Authentication failures, rate limit hits
8. **Keep dependencies updated** - Regular security patches

## Vulnerability Disclosure Policy

We follow responsible disclosure:

1. **Report**: Submit vulnerability privately
2. **Acknowledgment**: We acknowledge within 48 hours
3. **Assessment**: We assess severity and impact
4. **Fix**: We develop and test a fix
5. **Release**: We release a patch and security advisory
6. **Credit**: We credit the reporter (if desired)

**Timeline**:
- Critical issues: Fixed within 7 days
- High severity: Fixed within 14 days
- Medium/Low: Fixed within 30 days

## Known Security Considerations

### Paper Trading Mode

- **Not a sandbox**: Uses live exchange APIs for price data
- **Local simulation**: Orders simulated locally, not on exchange
- **Still requires API keys**: But no real money at risk

### Rate Limiting

- **IP-based**: Can be bypassed with rotating IPs
- **Local only**: Not designed for high-traffic public deployment
- **Intended for personal use**: Single user access expected

### Database

- **SQLite**: Not designed for concurrent multi-user access
- **Local only**: No network encryption (file-based)
- **Backup**: No automatic backup - user responsibility

## Security Updates

Stay informed about security updates:

- Watch this repository for security advisories
- Check `CHANGELOG.md` for security fixes
- Update to latest version regularly:
  ```bash
  git pull
  pip install -r requirements.txt --upgrade
  ```

## Contact

For security concerns:
- Open a security advisory on GitHub (private)
- Contact repository maintainer directly

**Do not disclose security issues publicly until a fix is available.**

---

*Last Updated: January 2026*
*This security policy applies to GridBot Chuck v0.1.0 and later.*
