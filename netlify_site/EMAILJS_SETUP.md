# EmailJS Setup Guide - GridBot Chuck

## Quick Setup (5 minutes)

Follow these steps to enable automated confirmation emails for beta signups.

---

## Step 1: Create EmailJS Account

1. Go to: **https://www.emailjs.com/**
2. Click **Sign Up** (top right)
3. Sign up with your Gmail: **gridbotchuck@gmail.com**
4. Verify your email
5. Login to dashboard

---

## Step 2: Connect Your Gmail

1. In EmailJS dashboard, click **Email Services**
2. Click **Add New Service**
3. Select **Gmail**
4. Click **Connect Account**
5. Select **gridbotchuck@gmail.com**
6. Allow EmailJS to send emails
7. Copy your **Service ID** (looks like: `service_abc123`)
8. Click **Create Service**

---

## Step 3: Create Email Template

1. Click **Email Templates** in sidebar
2. Click **Create New Template**
3. **Template Name**: `Beta Signup Confirmation`
4. **Template ID**: Copy this (looks like: `template_xyz789`)

### Email Template Content

**Subject:**
```
Welcome to GridBot Chuck Beta! 🚀 Your Access Key Inside
```

**Body (HTML):**
```html
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background: #0f172a; color: #f1f5f9; border-radius: 12px;">
  <div style="text-align: center; margin-bottom: 30px;">
    <h1 style="color: #3b82f6; margin: 0;">🎉 Welcome to GridBot Chuck Beta!</h1>
  </div>

  <p style="font-size: 16px; line-height: 1.6;">Hi {{to_name}},</p>

  <p style="font-size: 16px; line-height: 1.6;">
    Thanks for signing up for the GridBot Chuck beta! You're all set to start automated grid trading.
  </p>

  <div style="background: #1e293b; padding: 20px; border-radius: 8px; margin: 20px 0;">
    <p style="margin: 0 0 10px 0; font-weight: bold; color: #3b82f6;">Your Beta Access Key:</p>
    <code style="display: block; background: #334155; padding: 15px; border-radius: 6px; font-size: 18px; letter-spacing: 1px; color: #10b981; font-weight: bold;">{{beta_key}}</code>
    <p style="margin: 10px 0 0 0; font-size: 14px; color: #94a3b8;">💾 Save this key - you'll need it to activate the bot!</p>
  </div>

  <div style="text-align: center; margin: 30px 0;">
    <a href="{{download_link}}" style="display: inline-block; background: #3b82f6; color: white; padding: 15px 40px; border-radius: 8px; text-decoration: none; font-weight: bold; font-size: 16px;">
      📥 Download GridBot Chuck
    </a>
  </div>

  <h3 style="color: #3b82f6; margin-top: 30px;">Getting Started:</h3>
  <ol style="line-height: 1.8; padding-left: 20px;">
    <li>Download the bot using the button above</li>
    <li>Install Python 3.11+ if you don't have it</li>
    <li>Run: <code style="background: #334155; padding: 2px 6px; border-radius: 3px;">pip install -r requirements.txt</code></li>
    <li>Configure your exchange API keys in <code style="background: #334155; padding: 2px 6px; border-radius: 3px;">.env</code></li>
    <li>Use your beta key to activate: <code style="background: #334155; padding: 2px 6px; border-radius: 3px;">python beta_manager.py activate {{beta_key}}</code></li>
    <li>Start trading: <code style="background: #334155; padding: 2px 6px; border-radius: 3px;">python main.py --config config/config_small_capital_multi_pair.json</code></li>
  </ol>

  <h3 style="color: #3b82f6; margin-top: 30px;">Beta Details:</h3>
  <ul style="line-height: 1.8; padding-left: 20px;">
    <li>✅ Full Pro features unlocked</li>
    <li>⏱️ 14-day beta access</li>
    <li>💰 50% launch discount for beta testers</li>
    <li>🎁 Free updates during beta</li>
    <li>📧 Direct support from developers</li>
  </ul>

  <div style="background: #1e293b; padding: 15px; border-radius: 8px; margin: 30px 0; border-left: 4px solid #3b82f6;">
    <p style="margin: 0; font-size: 14px;">
      <strong>💡 Pro Tip:</strong> Start with paper trading mode to test the bot without risking real money!
    </p>
  </div>

  <hr style="border: none; border-top: 1px solid #334155; margin: 30px 0;">

  <p style="font-size: 14px; color: #94a3b8;">
    Questions? Reply to this email or contact us at <a href="mailto:{{reply_to}}" style="color: #3b82f6;">{{reply_to}}</a>
  </p>

  <p style="font-size: 14px; color: #94a3b8;">
    Happy Trading!<br>
    <strong style="color: #f1f5f9;">The GridBot Chuck Team</strong>
  </p>

  <p style="font-size: 12px; color: #64748b; margin-top: 30px; text-align: center;">
    © 2025 GridBot Chuck. All rights reserved.<br>
    Trading cryptocurrencies involves risk. Only invest what you can afford to lose.
  </p>
</div>
```

**Variables Used:**
- `{{to_name}}` - User's name (from email)
- `{{to_email}}` - User's email
- `{{beta_key}}` - Generated beta key
- `{{download_link}}` - GitHub releases link
- `{{reply_to}}` - Your support email

Click **Save**.

---

## Step 4: Get Your Public Key

1. Click **Account** in sidebar
2. Click **General**
3. Find **Public Key** section
4. Copy your public key (looks like: `user_abc123xyz`)

---

## Step 5: Update Your Website

Now you need to add your keys to the website:

### Option A: Edit Directly (If you have the file open)

In `netlify_site/index.html`, replace these placeholders:

```javascript
// Line ~1300: Replace YOUR_PUBLIC_KEY
emailjs.init('YOUR_PUBLIC_KEY');
// Change to:
emailjs.init('user_YOUR_ACTUAL_KEY_HERE');

// Line ~1349-1350: Replace SERVICE_ID and TEMPLATE_ID
await emailjs.send(
  'YOUR_SERVICE_ID',  // Replace with your Service ID
  'YOUR_TEMPLATE_ID', // Replace with your Template ID
```

### Option B: I'll Do It For You

Just tell me your 3 keys and I'll update the file:
1. **Public Key**: (from Account → General)
2. **Service ID**: (from Email Services)
3. **Template ID**: (from Email Templates)

---

## Step 6: Test It!

1. Push changes to GitHub (or I'll do it for you)
2. Wait 30 seconds for Netlify to deploy
3. Go to https://gridbotchuck.app/
4. Sign up with a test email
5. Check your inbox! 📧

---

## Free Tier Limits

EmailJS Free Plan:
- ✅ **200 emails per month** (plenty for beta signups)
- ✅ **Unlimited templates**
- ✅ **No credit card required**
- ✅ **Gmail integration included**

If you need more than 200/month, upgrade to paid plan ($7/month for 1,000 emails).

---

## Troubleshooting

### Emails Not Sending?

1. **Check spam folder** - First emails sometimes go to spam
2. **Verify Gmail connection** - EmailJS → Email Services → Check status
3. **Check browser console** - Look for error messages (F12 key)
4. **Test template** - EmailJS → Email Templates → Test Template

### Error: "Public key invalid"?

- Make sure you copied the **Public Key** (not API Key)
- Format: `user_abc123xyz`
- Found in: Account → General

### Error: "Service not found"?

- Make sure Service ID matches exactly
- Format: `service_abc123`
- Found in: Email Services → Your Gmail service

---

## Next Steps

After setup:
1. ✅ Test with your own email
2. ✅ Test with a friend's email
3. ✅ Share your site!
4. ✅ Monitor signups in Netlify dashboard

---

## Support

Need help? I'm here! Just ask and I'll:
- Update the HTML file with your keys
- Troubleshoot any issues
- Customize the email template
- Add more features

**Ready to add your keys?** Give me the 3 IDs and I'll update everything for you!
