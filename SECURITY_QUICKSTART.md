# Security Quick Start Guide

## 🔒 Essential Security Setup (5 Minutes)

### Step 1: Protect Your API Keys

**Create your `.env` file:**
```bash
cp .env.example .env
chmod 600 .env  # Linux/Mac only
```

**Generate a secure API key for bot dashboard:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Edit `.env` and add your keys:**
```env
# Bot Dashboard API Key (required)
GRIDBOT_API_KEY=your-generated-key-here

# Exchange API Keys
EXCHANGE_API_KEY=your_exchange_key
EXCHANGE_SECRET_KEY=your_exchange_secret
```

### Step 2: Exchange Security

**⚠️ CRITICAL: On your exchange account:**

1. **API Permissions**: Trading ONLY
   - ✅ Enable: View balances, Place orders, Cancel orders
   - ❌ Disable: Withdraw funds, Transfer funds

2. **IP Whitelisting**: Add your IP address
   - Log in to exchange → API Settings → IP Whitelist
   - Add your current IP (find at: https://whatismyipaddress.com)

3. **Two-Factor Authentication (2FA)**: Must be enabled
   - Use Google Authenticator or Authy
   - Never share 2FA codes

### Step 3: Test Safely

**Always start with paper trading:**
```json
// In config/config.json
{
  "exchange": {
    "trading_mode": "paper_trading"  // ← Start here!
  }
}
```

**Test checklist:**
- [ ] Paper trading works correctly
- [ ] Bot starts and stops properly
- [ ] Dashboard accessible at http://localhost:8080
- [ ] API key authentication works
- [ ] No errors in logs

**Only after testing:** Change to `"live"` and start with small capital.

---

## 🚨 Critical Security Rules

### NEVER Do These:

❌ **NEVER** commit `.env` file to GitHub  
❌ **NEVER** share API keys (screenshots, chat, email)  
❌ **NEVER** use API keys with withdrawal permissions  
❌ **NEVER** run bot with admin/root privileges  
❌ **NEVER** expose port 8080 to the internet directly

### ALWAYS Do These:

✅ **ALWAYS** use unique, strong API keys  
✅ **ALWAYS** enable 2FA on exchange accounts  
✅ **ALWAYS** use IP whitelisting on exchanges  
✅ **ALWAYS** test with paper trading first  
✅ **ALWAYS** keep software updated

---

## 🌐 Dashboard Security

### Default Setup (Secure)
- Dashboard runs on: `http://localhost:8080`
- **Only accessible from your computer**
- No external access possible

### Remote Access (Advanced)
If you need remote access:

1. **Use SSH Tunnel (Recommended):**
   ```bash
   ssh -L 8080:localhost:8080 user@your-server
   ```
   Then access: `http://localhost:8080` on your local machine

2. **Or Configure CORS (Less Secure):**
   ```env
   ALLOWED_ORIGINS=http://your-ip:8080,http://localhost:8080
   ```
   
   ⚠️ **Warning**: Exposes bot to network attacks. Use firewall!

### API Authentication

All API endpoints require authentication:

**In browser/JavaScript:**
```javascript
fetch('/api/bot/status', {
  headers: {
    'Authorization': 'Bearer your-api-key-here'
  }
})
```

**Or use query parameter:**
```
http://localhost:8080/api/bot/status?api_key=your-api-key-here
```

---

## 🛡️ What We Protect Against

### ✅ Implemented Protections

**SQL Injection**
- All database queries use parameterized statements
- No user input in SQL strings

**API Abuse**
- Rate limiting: 60 requests/minute per IP
- Burst protection: 10 requests
- Authentication required for all control endpoints

**Cross-Site Scripting (XSS)**
- Content Security Policy (CSP) headers
- Input sanitization
- Output encoding

**Clickjacking**
- X-Frame-Options: DENY header
- Frame ancestors policy

**MIME Sniffing**
- X-Content-Type-Options: nosniff

**Path Traversal**
- File path validation
- Base directory restriction

**Timing Attacks**
- Constant-time API key comparison
- Secure password hashing

**CORS Abuse**
- Whitelist-based origin control
- Credentials required

---

## 📊 Security Features

### Authentication
- **API Key**: Required for all control endpoints
- **Auto-Generation**: Secure keys generated if not configured
- **Environment Variables**: Keys never in code

### Rate Limiting
- **60 requests/minute** per IP address
- **10 request burst** allowance
- **Automatic retry-after** headers

### Input Validation
- Trading pairs: Strict format (BTC/USD)
- Numbers: Type and range checking
- File paths: Traversal protection
- Strings: Length and character validation

### Database Security
- Parameterized queries (no SQL injection)
- Data encryption at rest (file permissions)
- Regular backups recommended

---

## 🔍 Security Checklist

Before going live with real money:

### Configuration
- [ ] Strong `GRIDBOT_API_KEY` set in `.env`
- [ ] `.env` file has restricted permissions (600)
- [ ] Exchange API keys use minimal permissions (trading only)
- [ ] IP whitelisting enabled on exchange
- [ ] 2FA enabled on exchange account

### Network
- [ ] Firewall blocks external access to port 8080
- [ ] Using SSH tunnel for remote access (if needed)
- [ ] HTTPS configured (if exposing to network)

### Testing
- [ ] Paper trading tested successfully
- [ ] Small capital test with real money
- [ ] Stop loss and take profit working
- [ ] Emergency stop button tested

### Monitoring
- [ ] Log monitoring configured
- [ ] Error alerts set up
- [ ] Regular backup schedule
- [ ] Database backups encrypted

---

## 🆘 Emergency Procedures

### If API Keys Compromised

1. **Immediately**: Delete API keys on exchange
2. **Check**: Review recent trades for unauthorized activity
3. **Generate**: New API keys with different permissions
4. **Update**: `.env` file with new keys
5. **Enable**: Additional exchange security (IP whitelist, 2FA)

### If Bot Behaves Unexpectedly

1. **Stop**: Click STOP button in dashboard or:
   ```bash
   pkill -f "python.*main.py"
   ```

2. **Check**: Recent trades in exchange
3. **Review**: Bot logs for errors
4. **Verify**: Configuration settings
5. **Test**: With paper trading before resuming

### If Dashboard Compromised

1. **Stop**: API server immediately
2. **Change**: `GRIDBOT_API_KEY` in `.env`
3. **Restart**: Bot with new key
4. **Review**: Access logs
5. **Enable**: Additional firewall rules

---

## 📞 Getting Help

**Security Issues:**
- Open GitHub Security Advisory (private)
- Email repository maintainer

**General Support:**
- GitHub Issues
- GitHub Discussions
- Discord (coming soon)

**DO NOT share:**
- API keys
- `.env` file contents
- Database files
- Transaction details

---

## 📚 Additional Resources

**Full Security Documentation:**
- [SECURITY.md](../SECURITY.md) - Complete security policy
- [README.md](../README.md) - General documentation
- [BUILD_GUIDE.md](../BUILD_GUIDE.md) - Installation guide

**Exchange Security Guides:**
- [Kraken API Security](https://support.kraken.com/hc/en-us/articles/360000919966)
- [Coinbase API Security](https://help.coinbase.com/en/exchange/managing-my-account/how-to-create-an-api-key)
- [Alpaca API Security](https://alpaca.markets/docs/trading/getting-started/)

---

**Remember: Security is not a one-time setup, it's an ongoing practice. Stay vigilant!**
