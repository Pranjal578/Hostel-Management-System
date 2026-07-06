# 🏠 ROOMMET — Hostel Resident Management SaaS Platform

<p align="center">
  <strong>A production-ready, multi-tenant hostel management platform with QR identity cards, secure payments, real-time chat, and role-based access control.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11-blue?logo=python" alt="Python">
  <img src="https://img.shields.io/badge/Flask-3.1-black?logo=flask" alt="Flask">
  <img src="https://img.shields.io/badge/SQLAlchemy-2.0-orange" alt="SQLAlchemy">
  <img src="https://img.shields.io/badge/License-MIT-green" alt="MIT License">
  <img src="https://img.shields.io/badge/Docker-Ready-blue?logo=docker" alt="Docker">
</p>

---

## Overview

**ROOMMET** is a full-stack SaaS platform built for hostel operators and their residents. It provides a complete digital workflow: from resident onboarding and QR identity cards to rent payment submission and live chat — all behind a secure, role-based access control system.

Built with a **Defense-in-Depth** security architecture and a modern **Glassmorphism + Bento Grid** UI.

---

## ✨ Feature Highlights

### 👥 Three-Role Access System
| Role | Capabilities |
|---|---|
| **SuperAdmin** | Create/manage hostel owners, assign hostels, view all residents globally |
| **HostelOwner** | Manage multiple hostels, approve residents, verify payments, send notices, chat with residents |
| **Resident** | View profile + QR ID, submit rent receipts, read notices, chat with owner |

### 🔐 Security & Cryptography
- **AES-256 Encryption at Rest** — PII fields (phone, address, Aadhar ID) are encrypted transparently in the database via Python `cryptography` Fernet
- **MFA via OTP** — 6-digit time-limited OTP verification (10-min TTL) delivered by Email (SMTP) or SMS (Twilio)
- **Google OAuth 2.0** — Federated sign-in via Authlib (bypasses OTP as high-assurance MFA)
- **Content Security Policy (CSP)** — Strict response headers preventing XSS attacks
- **CSRF Protection** — Flask-WTF CSRF tokens on all POST forms
- **Session Invalidation** — Password change increments `password_version`, invalidating all other active sessions
- **Private Receipt Storage** — Payment screenshots stored outside public directory with randomized UUID filenames, served through an auth-gated endpoint
- **EXIF/GPS Metadata Stripping** — Profile photos and receipt images are sanitized via Pillow before storage
- **Rate Limiting** — Flask-Limiter enforces per-IP request ceilings on sensitive endpoints

### 📱 QR Identity System
- Each resident gets a permanent QR code generated at registration
- QR encodes a public verification URL (`/profile/<id>`)
- Owners can scan QR codes directly from the Residents page using their device camera
- QR codes are auto-regenerated (self-healing) if the file is missing

### 💸 Payment Workflow
- Residents scan hostel UPI payment QR → upload receipt screenshot or PDF
- Receipts are stored securely and served only to authorized owners/admins
- Owners can approve or reject with a typed reason (triggers email notification to resident)
- Full payment history maintained per resident

### 💬 Real-time Chat
- WhatsApp-style threaded message panel between each resident and their hostel owner
- Unread message tracking with auto-read-marking on open
- Polling-based live update

### 🏢 Multi-Hostel Management
- A single HostelOwner account can manage multiple hostels
- Per-hostel capacity tracking, unique join codes, facility tags, and payment QR codes
- Hostel-level public QR codes (encode hostel info for discovery)

### 🔍 Public Hostel Discovery
- Unauthenticated users can browse all listed hostels with search, capacity status, and facilities
- Each hostel card shows a modal with join code and hostel QR code

---

## 🗂 Project Structure

```
hostel_management_system/
├── app/
│   ├── __init__.py              # App factory, blueprint registration, self-healing startup
│   ├── models/
│   │   └── db.py                # SQLAlchemy models with Fernet encryption property wrappers
│   ├── routes/
│   │   ├── auth.py              # Login, OTP, Google OAuth, registration, public profile route
│   │   ├── admin.py             # SuperAdmin: create owners, assign hostels, manage residents
│   │   ├── owner.py             # HostelOwner: residents, payments, notices, chat, hostel settings
│   │   ├── resident.py          # Resident: dashboard, payment upload, notices, chat
│   │   ├── settings.py          # Profile/photo update, password change, MFA toggle
│   │   └── api.py               # Secure JSON APIs: resident details (QR scan), chat messages
│   ├── static/
│   │   ├── css/style.css        # Full glassmorphism + bento grid design system
│   │   ├── js/script.js         # Camera QR scanner, theme toggle, UI interactions
│   │   ├── images/              # Profile photos, logo, default avatar
│   │   ├── qr/                  # Generated resident QR PNGs
│   │   └── uploads/
│   │       └── payment_qrs/     # Hostel payment UPI QR images
│   ├── templates/               # Jinja2 HTML templates (extend base.html)
│   └── utils/
│       ├── encryption.py        # AES-256 Fernet helpers (encrypt/decrypt field)
│       ├── photo_handler.py     # EXIF sanitization, file save/load, base64 dual-storage
│       ├── qr_generator.py      # Resident & hostel QR PNG generation
│       ├── email_sender.py      # SMTP OTP, payment status, payment submitted emails
│       ├── sms_sender.py        # Twilio SMS OTP delivery
│       └── otp_generator.py     # OTP generation, hashing, and validation
├── instance/
│   ├── database.db              # SQLite database (git-ignored; auto-created)
│   └── uploads/payments/        # Private payment receipt files (git-ignored)
├── migrations/                  # Flask-Migrate Alembic migration scripts
├── app.py                       # Application entry point
├── wsgi.py                      # Production WSGI entry point (Gunicorn)
├── config.py                    # DevelopmentConfig / ProductionConfig classes
├── manage.py                    # CLI management commands (init-db, create-admin)
├── requirements.txt             # Python dependency manifest
├── Dockerfile                   # Production Docker image (Python 3.11-slim + Gunicorn)
├── setup.bat                    # Windows one-click local setup bootstrapper
├── setup.sh                     # Linux/Mac one-click local setup bootstrapper
├── .env.example                 # Environment variable template
└── .gitignore
```

---

## ⚡ Quick Start (Local Development)

### Prerequisites
- Python **3.8+**
- `pip`
- A terminal (PowerShell, CMD, bash)

### Step 1 — Clone & Configure Environment

```bash
# Copy the environment template
copy .env.example .env       # Windows
cp .env.example .env         # Linux/Mac
```

Open `.env` and fill in your values. At minimum, generate an encryption key:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Paste the output as your `ENCRYPTION_KEY` in `.env`.

### Step 2 — Run the Setup Script

This creates a virtual environment, installs dependencies, creates required folders, and initializes the database:

```bash
# Windows
setup.bat

# Linux / Mac
chmod +x setup.sh && ./setup.sh
```

### Step 3 — Start the Development Server

```bash
# Activate venv (if not already active after setup)
venv\Scripts\activate         # Windows
source venv/bin/activate      # Linux/Mac

python app.py
```

Open **[http://localhost:5000](http://localhost:5000)**

### Step 4 — Login as SuperAdmin

| Field | Default Value |
|---|---|
| Email | `demo` (or your `ADMIN_USERNAME` in `.env`) |
| Password | `demo` (or your `ADMIN_PASSWORD` in `.env`) |

> ⚠️ **Change admin credentials in `.env` before deploying to production.**

---

## 🔧 Environment Variables Reference

| Variable | Required | Description |
|---|---|---|
| `SECRET_KEY` | ✅ | Flask session signing key (random 32-byte hex) |
| `ENCRYPTION_KEY` | ✅ | AES-256 Fernet key for PII encryption |
| `ADMIN_USERNAME` | ✅ | SuperAdmin login email/username |
| `ADMIN_PASSWORD` | ✅ | SuperAdmin login password |
| `BASE_URL` | ✅ | Public base URL (used in QR codes, e.g. `https://yourdomain.com`) |
| `DATABASE_URL` | ⚡ | PostgreSQL connection URI (auto-injected by cloud providers) |
| `MAIL_SERVER` | ✅ | SMTP server host (e.g. `smtp.gmail.com`) |
| `MAIL_PORT` | ✅ | SMTP port (usually `587`) |
| `MAIL_USERNAME` | ✅ | SMTP login email |
| `MAIL_PASSWORD` | ✅ | SMTP app password |
| `SENDER_EMAIL` | ✅ | From address for sent emails |
| `GOOGLE_CLIENT_ID` | ☑️ | Google OAuth 2.0 Client ID |
| `GOOGLE_CLIENT_SECRET` | ☑️ | Google OAuth 2.0 Client Secret |
| `TWILIO_ACCOUNT_SID` | ☑️ | Twilio SID (for SMS OTP) |
| `TWILIO_AUTH_TOKEN` | ☑️ | Twilio Auth Token |
| `TWILIO_PHONE_NUMBER` | ☑️ | Twilio sender phone number |

> ✅ Required for core features &nbsp;|&nbsp; ☑️ Optional / feature-specific

---

## 🗄 Database Schema (Key Tables)

```
users           → id, email, password_hash, role, otp_enabled, otp_method, password_version
hostels         → id, owner_id, hostel_name, location, hostel_code, capacity, payment_qr_code, hostel_qr_code
residents       → id, user_id, hostel_id, full_name, phone(enc), aadhar(enc), address(enc), room_number, status, profile_image
payments        → id, resident_id, hostel_id, amount, payment_date, transaction_id, screenshot_path, status
notices         → id, hostel_id, title, message, created_at
messages        → id, sender_id, receiver_id, message_content, is_read, created_at
audit_logs      → id, user_id, action, ip_address, created_at
```

Encrypted fields are stored as AES-256 Fernet ciphertext blobs and transparently decrypted via SQLAlchemy `@property` accessors (`phone_decrypted`, `permanent_address_decrypted`, `aadhar_id_decrypted`).

---

## 🛠 Database Migrations (Flask-Migrate)

When you modify models in `app/models/db.py`:

```bash
# Generate a new migration script
flask db migrate -m "describe your schema change"

# Apply it locally
flask db upgrade
```

The app automatically runs `flask db upgrade` on startup — so deployed migrations apply immediately on next restart.

---

## 🐳 Docker Deployment

The included `Dockerfile` uses Python 3.11-slim with Gunicorn bound to port `8080`.

```bash
# Build
docker build -t roommet .

# Run
docker run -p 8080:8080 --env-file .env roommet
```

---

## ☁️ DigitalOcean App Platform Deployment

1. Push your code to a GitHub repository.
2. On DigitalOcean → **Create App** → connect GitHub repo → auto-detects `Dockerfile`.
3. Set HTTP port to **8080**.
4. Add a **PostgreSQL** managed database → `DATABASE_URL` is auto-injected.
5. Add all environment variables from `.env` under **App Settings → Environment Variables**.
6. Deploy — migrations run automatically on startup.

---

## 🔑 User Flows

### Resident
```
Register (with hostel join code) → Pending Approval → Owner Approves & Assigns Room
→ Login → Dashboard (Profile + QR ID) → Submit Monthly Rent Receipt
→ Chat with Owner → View Notices
```

### Hostel Owner
```
Login → Dashboard → Approve/Reject Pending Residents
→ Manage Hostels (join codes, QR, pricing) → Verify/Reject Payment Receipts
→ Send Notices → Chat with Residents → Scan Resident QR for Instant Identity Check
```

### SuperAdmin
```
Login → Create Owner Accounts → Create & Assign Hostels
→ View All Residents Globally → Scan QR codes → System-wide Oversight
```

---

## 📜 License

Distributed under the **MIT License** — free to use, modify, and distribute.

---

## 📬 Contact

For support, issues, or feature requests:
**[pranjalshukla2222@gmail.com](mailto:pranjalshukla2222@gmail.com)**
