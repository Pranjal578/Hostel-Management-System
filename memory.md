# System Memory & Context Knowledge Base
## ROOMMET — Multi-Tenant Hostel SaaS Platform

---

## 1. Project Overview & Context

- **Project Name:** ROOMMET (Hostel Resident Management SaaS Platform)
- **Primary Language & Framework:** Python 3.10+ / Flask / SQLAlchemy / Werkzeug
- **Mobile Stack:** Flutter 3.47+ (Dart) with Dio & Riverpod
- **Current System Status:** Production-Ready, Security-Hardened, Fully Tested
- **Primary SuperAdmin Account:** `pranjalshukla2222@gmail.com` (Role: `SuperAdmin`, 2FA: `Mandatory / Email`)

---

## 2. Key Architectural Invariants & Decisions

1. **Mandatory 2FA Policy:**
   - 2-Factor Authentication is **mandatory for all users** across the platform (`SuperAdmin`, `HostelOwner`, `Resident`, `ShopOwner`).
   - `User.is_otp_enabled()` returns `True` permanently.
   - Login attempts trigger a 6-digit cryptographic HMAC OTP code sent to the user's verified email (or SMS for residents).
2. **Designated SuperAdmin:**
   - User `pranjalshukla2222@gmail.com` is automatically provisioned and guaranteed as `SuperAdmin` on every application startup via `_self_heal_db()` in `app/__init__.py`.
3. **Multi-Tenant Row-Level Security (RLS):**
   - All owner operations must be scoped by `hostel_id.in_(owner_hostel_ids)`.
   - Payment receipts are isolated behind `/secure-receipt/<filename>` with session & JWT ownership verification.
4. **Zero-Plaintext PII Storage:**
   - AES-256 Fernet encryption at rest for phone numbers, residential addresses, and 12-digit Aadhar IDs.
5. **Security Headers & Infrastructure:**
   - HSTS (`Strict-Transport-Security: max-age=31536000; includeSubDomains; preload`).
   - `ProxyFix` middleware active to preserve true client IPs behind reverse proxies.
   - Centralized validation via `app/utils/validators.py` and magic-byte file checks for all image uploads.

---

## 3. Codebase File Map

```
hostel_management_system/
├── PRD.md                       # Product Requirements Document
├── architecture.md              # System Architecture & Data Flows
├── rules.md                     # Engineering & Security Guidelines
├── phases.doc.md                # Phases, Milestones & Changelog
├── design.md                    # 2026 UI/UX Design System Specs
├── memory.md                    # Project Memory & Knowledge Base
├── README.md                    # Main repository overview & quickstart
├── manage.py                    # CLI management tool (backup, init-db, check)
├── config.py                    # Configuration classes (Dev / Prod)
├── app.py / wsgi.py             # Entrypoint scripts
├── backups/                     # Encrypted database backup snapshots
├── app/
│   ├── __init__.py              # Application factory, extensions & security headers
│   ├── models/
│   │   └── db.py                # SQLAlchemy ORM models
│   ├── routes/
│   │   ├── auth.py              # Login, register, 2FA OTP verification, Google OAuth
│   │   ├── admin.py             # SuperAdmin control panel & owner provisioning
│   │   ├── owner.py             # HostelOwner dashboard, tenants, payments, notices
│   │   ├── resident.py          # Resident dashboard, QR card, payment upload
│   │   ├── pharmacy.py          # Local medicine marketplace & ordering
│   │   ├── settings.py          # Account settings, password change, 2FA channel
│   │   ├── mobile_api.py        # REST API endpoints for Flutter mobile app
│   │   └── api.py               # Shared JSON endpoints
│   ├── utils/
│   │   ├── validators.py        # Centralized server-side validation & magic bytes
│   │   ├── encryption.py        # AES-256 Fernet PII encryption
│   │   ├── otp_generator.py     # 6-digit OTP generator & HMAC hashing
│   │   ├── photo_handler.py     # Image upload, validation & EXIF sanitizer
│   │   ├── qr_generator.py      # Dynamic QR generation for hostels & residents
│   │   ├── email_sender.py      # SMTP transactional mailer
│   │   └── sms_sender.py        # Twilio SMS sender
│   ├── static/
│   │   ├── css/style.css        # 2026 Dark Glassmorphism stylesheet
│   │   ├── js/script.js         # Theme toggle, toast, shortcuts, mobile menu
│   │   └── images/              # Logos, default avatars, medicine photos
│   └── templates/               # Jinja2 HTML templates
│       ├── base.html            # Master layout with skip-link, toasts, shortcuts
│       └── ...                  # Role-specific dashboard templates
└── roommet_flutter/             # Flutter mobile client repository
    └── lib/                     # Clean architecture Riverpod + Dio mobile app
```

---

## 4. Key Operational Commands

```bash
# 1. Start the Flask Backend locally:
./.venv/bin/python app.py

# 2. Trigger an automated database backup (SQLite or PostgreSQL):
./.venv/bin/python manage.py backup

# 3. Trigger backup with custom rotation count:
./.venv/bin/python manage.py backup --keep 14

# 4. Run system deployment verification checks:
./.venv/bin/python manage.py check

# 5. Initialize or upgrade database migrations:
./.venv/bin/python manage.py init-db

# 6. Generate a cryptographically secure SECRET_KEY:
./.venv/bin/python manage.py generate-secret
```

---

## 5. Security & Verification History

- **2FA Test:** Verified mandatory OTP challenge on login.
- **SuperAdmin Provisioning:** Confirmed `pranjalshukla2222@gmail.com` holds the `SuperAdmin` role with 2FA enabled.
- **Backup Verification:** Created `backups/20260901_145731.db` (1.5 MB) via `manage.py backup`.
- **Validation Test:** 100% pass on RFC email, 10-digit Indian phone, 12-digit Aadhar, 6-digit pincode, and magic-byte checks in `validators.py`.
- **HTTP Status:** Web application running smoothly on `http://localhost:5000` (Status: 200 OK).
