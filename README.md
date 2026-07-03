# Secure Multi-Hostel Resident Management SaaS Platform

A modern, highly secure, and professional web-based Hostel Resident Management SaaS Platform. It provides a robust role-based access system (SuperAdmin, HostelOwner, and Resident), dynamic QR-linked profiles, and secure multi-factor authentication (OTP via email or SMS).

Designed with a **"Defense in Depth"** security model suitable for professional enterprise environments.

---

## 🔒 Security & Architecture (Defense in Depth)

The system is designed with multiple security layers to protect resident data, payments, and system access:

1. **Authentication & Identity Verification**
   * **OAuth 2.0 / OpenID Connect:** Integrated with **Google Sign-In** via Authlib to authenticate users securely using trusted external providers.
   * **Multi-Factor Authentication (OTP):** Optional 2FA delivering 6-digit verification codes using **Twilio (for SMS)** or **SMTP Relays (like SendGrid for Email)** with cryptographically hashed storage in the database and a 10-minute validity TTL.
   * **Re-Authentication Flow:** High-sensitivity actions (updating emails, password changes, or MFA toggles) require re-entering the current password.
   * **Session Expiry & Invalidation:** On password changes, a `password_version` token is updated to invalidate other active sessions immediately.

2. **Data Security & Privacy**
   * **AES-128/256 Encryption at Rest:** Personally Identifiable Information (PII) like `phone_number`, `permanent_address`, and `aadhar_id` are encrypted in the database using the standard AES-based Fernet algorithm (via `cryptography` library) transparently through model property getters and setters.
   * **Password Hashing:** Stored securely using Werkzeug's state-of-the-art password hashing functions.
   * **Data Exposure Prevention:** Sensitive identifiers are masked (e.g. Aadhar card masked to `XXXX-XXXX-1234` and phone numbers masked to `+1***5678`).

3. **Application & File Security**
   * **Rate Limiting:** Enforces strict limit intervals (e.g., 5 requests per minute on `/login` and `/verify-otp`) using `Flask-Limiter` to protect against brute-force and credential-stuffing attacks.
   * **Content Security Policy (CSP):** Rigorous response headers restricting where script, styling, connect, and media assets can load from, mitigating Cross-Site Scripting (XSS) and data injection.
   * **Secure File Delivery:** Payment receipt attachments are renamed using random UUIDs and saved in the private `instance/` folder outside the public web root. Access is restricted using a custom endpoint (`/secure-receipt/<filename>`) that checks user session permissions.
   * **Media Sanitization:** Resident profiles and payment screenshot uploads are processed using `Pillow` to strip all EXIF/GPS device metadata to prevent location leaks.
   * **Immutable Audit Logging:** Keeps persistent logs of all authentication, settings modifications, profile changes, and admin decisions (e.g., payment approvals/rejections) matching usernames, action types, and IP addresses.

---

## 🚀 Quick Start Guide

### Prerequisites
* Python 3.8 or higher installed on your system.
* A basic terminal environment (cmd, PowerShell, bash).

### Step 1: Clone and Set Up Environment Variables
1. Copy `.env.example` to create your local environment file:
   ```cmd
   copy .env.example .env
   ```
2. Open `.env` and configure your settings:
   * Generate an `ENCRYPTION_KEY` using python:
     ```bash
     python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
     ```
   * Set up your Twilio credentials, Google Client Client IDs, and Mail Server settings.

### Step 2: Automatic Installation (Recommended)

#### For Windows:
```cmd
setup.bat
```

#### For Linux/Mac:
```bash
chmod +x setup.sh
./setup.sh
```

*The setup scripts check Python, install required dependencies in a virtual environment (`venv`), verify media directory structures, and generate the SQLite database schema automatically.*

### Step 3: Run the Application
1. Activate the virtual environment (if not already active):
   * **Windows:** `venv\Scripts\activate.bat`
   * **Linux/Mac:** `source venv/bin/activate`
2. Launch the Flask development server:
   ```bash
   python app.py
   ```
3. Open your browser and navigate to: **`http://localhost:5000`**

### Step 4: Login with Default Credentials
To access the system, you can use the default Admin account:
* **Username/Email:** `demo`
* **Password:** `demo`

---

## 📂 Project Structure

```structure
hostel_management_system/
├── app/
│   ├── models/
│   │   └── db.py               # Database schemas (User, Resident, Hostel, Payment, AuditLog)
│   ├── routes/
│   │   ├── admin.py            # SuperAdmin operations
│   │   ├── owner.py            # Hostel Owner functions (QR upload, verify payments)
│   │   ├── resident.py         # Resident dashboard and payment submissions
│   │   ├── settings.py         # Tabbed profile, security, and MFA settings
│   │   ├── auth.py             # Login, Google OAuth callback, OTP verification
│   │   └── api.py              # Scoped secure APIs for scanning dynamic QR profiles
│   ├── static/
│   │   ├── css/style.css       # Premium glassmorphic interface styles
│   │   └── js/script.js        # Dynamic front-end behaviors and scripts
│   ├── templates/              # HTML views (with progressive disclosure tabs & dialogs)
│   └── utils/
│       ├── encryption.py       # AES cryptography getters/setters helper
│       ├── photo_handler.py    # Pillow metadata sanitizer & UUID photo saver
│       ├── qr_generator.py     # Dynamic profiles QR generator
│       ├── email_sender.py     # SMTP verification and notification sender
│       └── sms_sender.py       # Twilio API SMS handler
├── instance/
│   ├── database.db             # In-process SQLite database storage
│   └── uploads/payments/       # Secure folder for payment receipts (outside web root)
├── app.py                      # Application factory entrypoint
├── config.py                   # Configuration environment parser
├── requirements.txt            # Project dependencies
├── setup.bat / setup.sh        # Platform-specific automation bootstrapper
└── .env / .env.example         # System credentials and encryption key definitions
```

---

## 🛡️ License
Distributed under the **MIT License**. See `LICENSE` for more information.

---

## 📧 Support
For issues, configuration queries, or integration help, please reach out to **pranjalshukla2222@gmail.com**.
