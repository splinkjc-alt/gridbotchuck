# GridBot Pro - Security Guide

This document provides guidance on securing your GridBot Pro installation to protect against unauthorized access, modification, and copying.

## 🔐 Security Features

### 1. API Authentication

The REST API server is protected with token-based authentication. All protected endpoints require a valid API token.

#### How It Works

- When the bot starts, it generates a unique API token
- The token is stored securely in `~/.gridbot/api_token` (read/write only for owner)
- All API requests (except health check and static files) require the token

#### Using the API Token

Add the token to your requests using one of these methods:

**Authorization Header (Recommended):**
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8080/api/bot/status
```

**X-API-Key Header:**
```bash
curl -H "X-API-Key: YOUR_TOKEN" http://localhost:8080/api/bot/status
```

**Query Parameter (for WebSocket):**
```bash
ws://localhost:8080/api/ws?token=YOUR_TOKEN
```

#### Custom Token

Set a custom token using the environment variable:
```bash
export GRIDBOT_API_TOKEN="your-secure-token-here"
```

### 2. License Management

GridBot Pro includes a license management system for commercial distribution:

- **Hardware-bound licenses**: Licenses are tied to specific machines
- **Expiration validation**: Licenses have configurable expiration dates
- **Feature gating**: Different license tiers unlock different features
- **HMAC signature verification**: Prevents license tampering

#### License Tiers

| Feature | Trial | Beta | Basic | Pro | Enterprise |
|---------|-------|------|-------|-----|------------|
| Max Pairs | 1 | 3 | 2 | 5 | Unlimited |
| Max Grids | 5 | 15 | 10 | 20 | Unlimited |
| Market Scanner | ❌ | ✅ | ✅ | ✅ | ✅ |
| Multi-pair | ❌ | ✅ | ❌ | ✅ | ✅ |
| Notifications | ❌ | ✅ | ✅ | ✅ | ✅ |

### 3. Credential Security

#### Environment Variables

Store all sensitive credentials in environment variables (`.env` file):

```bash
# Exchange credentials - NEVER commit to git!
EXCHANGE_API_KEY=your_api_key
EXCHANGE_SECRET_KEY=your_secret_key

# License secret for generating licenses
GRIDBOT_LICENSE_SECRET=your_license_secret

# Custom API token for REST API
GRIDBOT_API_TOKEN=your_api_token

# Notification services
APPRISE_NOTIFICATION_URLS=tgram://...
```

#### Best Practices

1. **Never commit secrets to Git**
   - `.env` file is already in `.gitignore`
   - Use `.env.example` as a template

2. **Use read-only API keys when possible**
   - For backtesting and paper trading, you only need read access
   - Only use full-access keys for live trading

3. **Rotate credentials regularly**
   - Change API keys periodically
   - Regenerate API tokens if compromised

## 🛡️ Protecting Against Unauthorized Access

### Local Network

The API server binds to `127.0.0.1` by default (localhost only). This means:
- Only processes on the same machine can access the API
- No external network access is possible

If you need remote access:
1. Use a reverse proxy (nginx/caddy) with HTTPS
2. Implement IP whitelisting
3. Use a VPN for secure remote access

### File Permissions

Sensitive files should have restricted permissions:

```bash
# API token file (created automatically)
chmod 600 ~/.gridbot/api_token

# Environment file
chmod 600 .env

# License file
chmod 600 license.key
```

## 🔒 Protecting Against Code Modification

### 1. Code Integrity Checks

The license manager includes HMAC signature verification:
- License keys are signed with a secret
- Modified licenses are detected and rejected
- Machine ID binding prevents key sharing

### 2. Obfuscation (Optional)

For commercial distribution, consider using code obfuscation:

```bash
# Using PyArmor (commercial tool)
pip install pyarmor
pyarmor pack -x " --exclude tests" main.py

# Using Nuitka (compiles to binary)
pip install nuitka
python -m nuitka --standalone --onefile main.py
```

### 3. Source Control

- Use Git to track all changes
- Set up branch protection rules
- Require code reviews for PRs
- Use signed commits

## 🚫 Protecting Against Copying

### 1. Hardware-Bound Licensing

Licenses are bound to:
- Hostname
- Machine type
- Processor info
- MAC address (when available)

This prevents license key sharing between machines.

### 2. Generating Licenses

Only you (the owner) should have access to license generation:

```python
# Example: Generate a license for a customer
from core.licensing.license_manager import LicenseManager

manager = LicenseManager()

# Get customer's machine ID first
# They can run: python -c "from core.licensing.license_manager import LicenseManager; print(LicenseManager()._get_machine_id())"

license_key = manager.generate_license_key(
    license_type="pro",
    customer_email="customer@example.com",
    machine_id="customer_machine_id_here",
    expiry_days=365
)
print(license_key)
```

### 3. Environment Variable Protection

Set the license secret via environment variable:

```bash
export GRIDBOT_LICENSE_SECRET="your-very-secure-secret-key"
```

**Never hardcode this secret in the source code!**

## 📊 Security Monitoring

### Audit Logging

The bot logs security-relevant events:
- API authentication failures
- License validation attempts
- Unauthorized access attempts

Check logs for suspicious activity:
```bash
grep -i "unauthorized\|invalid\|failed" logs/*.log
```

### Health Monitoring

Monitor the bot's health endpoint (no auth required):
```bash
curl http://localhost:8080/api/health
```

## 🔧 Security Checklist

Before deploying:

- [ ] Set `GRIDBOT_LICENSE_SECRET` environment variable
- [ ] Generate and distribute licenses securely
- [ ] Verify `.env` is in `.gitignore`
- [ ] Set proper file permissions (600 for sensitive files)
- [ ] Review API token and store securely
- [ ] Enable logging to file for audit trail
- [ ] Test authentication is working
- [ ] Consider code obfuscation for commercial distribution

## 📞 Reporting Security Issues

If you discover a security vulnerability:
1. **Do not** create a public issue
2. Email the maintainers directly
3. Provide details about the vulnerability
4. Allow time for a fix before disclosure

## 🔄 Keeping Secure

- Keep dependencies updated (`pip install --upgrade`)
- Monitor security advisories for ccxt, aiohttp, etc.
- Regularly rotate API keys and tokens
- Review access logs periodically
- Test license validation regularly
