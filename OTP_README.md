# OTP (One-Time Password) Login Feature

## Overview

The Hostel Management System now includes optional OTP authentication for enhanced security. Users can enable OTP to receive 6-digit verification codes via email or SMS when logging in.

**Key Features:**

- ✅ **Optional:** Users choose whether to enable OTP
- ✅ **Multiple Delivery Methods:** Email or SMS
- ✅ **Time-Limited:** Codes expire after 10 minutes
- ✅ **Secure:** OTP codes are hashed before storage
- ✅ **Easy Setup:** One-click enable/disable from profile settings

## User Guide

### Enabling OTP

1. **Login to your account** with email and password
2. **Go to Edit Profile** from your dashboard
3. **Click "OTP Security Settings"** button
4. **Select delivery method** (Email or SMS)
5. **Click "Enable OTP Now"**
6. **Logout and login again** to test the feature

### Logging In with OTP

1. **Enter email and password** at login page
2. **Select preferred method** (Email or SMS) to receive code
3. **Enter the 6-digit code** received in your inbox
4. **Click Verify OTP** to complete login

### Changing OTP Method

1. **Go to OTP Security Settings** from profile
2. **Select new delivery method** (Email or SMS)
3. **Click "Update OTP Method"**

### Disabling OTP

1. **Go to OTP Security Settings** from profile
2. **Click "Disable OTP"** button
3. **Confirm when prompted**
4. OTP will be disabled on next login

## Administrator Guide

### Email Configuration

OTP requires email configuration to send codes. Set these environment variables:

```bash
# Gmail example (recommended for testing)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password  # NOT your regular password
SENDER_EMAIL=noreply@hostelmanagement.com
```

#### Setting up Gmail

1. **Enable 2-Factor Authentication** on your Google Account
2. **Create App Password:**
   - Go to <https://myaccount.google.com/apppasswords>
   - Select "Mail" and "Windows Computer" (or your device)
   - Add the generated 16-character password as `MAIL_PASSWORD`
3. Do NOT use your regular Google password

#### Other Email Providers

**Outlook/Hotmail:**

```mail
MAIL_SERVER=smtp.live.com
MAIL_PORT=587
```

**Yahoo Mail:**

```mail
MAIL_SERVER=smtp.mail.yahoo.com
MAIL_PORT=587
```

**SendGrid:**

```mail
MAIL_SERVER=smtp.sendgrid.net
MAIL_PORT=587
MAIL_USERNAME=apikey
MAIL_PASSWORD=your-sendgrid-api-key
```

### SMS Configuration (Optional)

To enable SMS delivery, set Twilio credentials:

```bash
TWILIO_ACCOUNT_SID=your-account-sid
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_PHONE_NUMBER=+1234567890
```

Get these from: <https://www.twilio.com/console>

**Note:** SMS requires Twilio account and has associated costs.

### Testing OTP

#### Test User Registration

1. Create a test resident account with valid email
2. Go to OTP Settings and enable OTP
3. Logout and login again
4. Verify email is received with correct OTP
5. Verify OTP expires after 10 minutes

#### Troubleshooting

**OTP email not received:**

- Check MAIL_SERVER, MAIL_PORT, MAIL_USERNAME, MAIL_PASSWORD in .env
- Check spam folder
- Verify email configuration with `python manage.py check`

**SMS not working:**

- Verify TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN
- Check phone number format (must include country code: +1234567890)
- Ensure Twilio account has sufficient credits

## Technical Details

### OTP Storage

OTP codes are **hashed before storage** using PBKDF2-SHA256 (same as password hashing). The plain OTP is never stored in the database.

**Database Fields Added to Residents table:**

```python
otp_enabled       Boolean   # Whether OTP is enabled
otp_code          String    # Hashed OTP code
otp_expires_at    DateTime  # When OTP expires
otp_method        String    # 'email' or 'sms'
```

### Login Flow with OTP

```flow
User enters email + password
    ↓
Password validated
    ↓
Is OTP enabled?
    ├─ Yes → Generate OTP → Store hashed OTP + expiry
    │         Send via email/SMS → Redirect to verify page
    │         User enters code → Validate → Set session → Dashboard
    │
    └─ No → Set session directly → Dashboard
```

### File Structure

**New/Modified Files:**

- `models/db.py` - Added OTP fields to Resident model
- `app.py` - Added OTP routes and modified login flow
- `config.py` - Added email/SMS configuration options
- `requirements.txt` - Added Flask-Mail and Twilio
- `.env.example` - Added email/SMS configuration template

**New Utilities:**

- `utils/otp_generator.py` - Generate, hash, validate OTP codes
- `utils/email_sender.py` - Send OTP via email
- `utils/sms_sender.py` - Send OTP via SMS

**New Templates:**

- `send_otp.html` - Choose delivery method
- `verify_otp.html` - Enter OTP code with timer
- `otp_settings.html` - Manage OTP settings

### API Endpoints

**New Routes:**

- `GET /resident/send-otp` - Choose OTP delivery method
- `POST /resident/send-otp` - Send OTP code
- `GET /resident/verify-otp` - Enter OTP code
- `POST /resident/verify-otp` - Verify OTP and complete login
- `POST /resident/resend-otp` - Resend OTP
- `GET /resident/setup-otp` - Manage OTP settings
- `POST /resident/setup-otp` - Enable/disable OTP

### Configuration Options

**In `.env` file:**

```bash
# Email Configuration
MAIL_SERVER=smtp.gmail.com        # SMTP server
MAIL_PORT=587                     # SMTP port
MAIL_USE_TLS=True                 # Use TLS encryption
MAIL_USERNAME=your-email@gmail.com # Email account
MAIL_PASSWORD=your-password        # Email password/token
SENDER_EMAIL=noreply@...          # From address

# SMS Configuration (Optional)
TWILIO_ACCOUNT_SID=...            # Twilio account ID
TWILIO_AUTH_TOKEN=...             # Twilio auth token
TWILIO_PHONE_NUMBER=+1...         # Twilio phone number

# OTP Settings
OTP_LENGTH=6                       # Length of OTP code
OTP_EXPIRY_MINUTES=10             # Minutes until OTP expires
```

## Security Considerations

1. **OTP Codes are Hashed** - Never stored as plain text
2. **Time-Limited** - Expire after 10 minutes
3. **Secure Channel** - Uses HTTPS in production
4. **Email/SMS as Delivery** - User-verified contact methods
5. **Password Still Required** - OTP is second factor, not replacement
6. **Secure Cookies** - Session cookies are HTTPONLY and SECURE

## Best Practices

**DO:**

- Use strong email/SMS provider credentials
- Monitor OTP failures in logs
- Keep email/SMS provider accounts secure
- Test email setup in development first
- Document OTP recovery procedures

 **DON'T:**

- Share OTP codes in unsecured channels
- Use weak email passwords
- Enable OTP without testing
- Store OTP codes in plain text
- Disable security features unnecessarily

## Limitations & Future Enhancements

**Current Limitations:**

- No rate limiting on OTP attempts (can be added in future)
- No backup recovery codes (can be added in future)
- No SMS failover if email fails (would require TOTP)
- Admin users don't have OTP option (can be added in future)

**Potential Enhancements:**

- TOTP (Time-based OTP) with authenticator apps
- Rate limiting to prevent brute force
- Backup recovery codes
- SMS as fallback for email failures
- Admin OTP authentication
- OTP audit logs
- Multi-device session management

## Troubleshooting Guide

### Email Configuration Issues

### Error: "Email configuration not set up"

```solution
Solution: Set MAIL_SERVER, MAIL_USERNAME, MAIL_PASSWORD in .env
```

### Error: "Failed to send OTP"

```list
Check:
1. Email credentials are correct
2. Email account allows app passwords
3. Firewall allows SMTP port (usually 587)
4. Check app logs for detailed error
```

### Emails going to spam

```list
Solution:
1. Add sender email to contacts
2. Use established email provider (Gmail, Outlook)
3. Set SENDER_EMAIL to recognized domain
```

### OTP Verification Issues

#### Error: "OTP has expired"

```error
Cause: 10 minutes passed since OTP was sent
Solution: Click "Resend OTP" to get a new code
```

### Error: "Invalid OTP code"**

```list
Check:
1. Entered code matches received code
2. No extra spaces in code
3. Code hasn't expired (see timer)
4. Correct OTP dialog (might have multiple)
```

### SMS Issues

### SMS not being sent

```list
Check:
1. Twilio credentials configured correctly
2. Phone number format: +1234567890
3. Twilio account has sufficient credits
4. Phone number is valid for country
```

## Support & Documentation

- **Configuration Guide:** See `.env.example`
- **Deployment Guide:** See `DEPLOYMENT.md`
- **Quick Start:** See `QUICKSTART.md`
- **Project Overview:** See `PROJECT_OVERVIEW.md`

## Questions?

If you encounter issues or have questions about OTP:

1. Check this documentation first
2. Review log files for error details
3. Run `python manage.py check-env` to verify configuration
4. Test email/SMS delivery manually if needed

---

**Last Updated:** February 2024
**Version:** 1.0.0
**Status:** Production Ready (with email configuration)
