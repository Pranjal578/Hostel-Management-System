# Secure Multi-Hostel Resident Management SaaS Platform

A premium, highly secure, and professional web-based Hostel Resident Management SaaS Platform. It provides a robust role-based access control system (SuperAdmin, HostelOwner, and Resident), dynamic QR-linked profiles, and secure multi-factor authentication (OTP via email or SMS).

Designed with a **"Defense in Depth"** security model and a modern **Mobile-First Bento Grid** user interface.

---

## Features & Interface Aesthetics

1. **Mobile-First + Bento Grid Responsive Design**
   * **Liquid Glassmorphism:** Subtle low-blur glass layouts (`4–8px`) on mobile viewports for smooth scrolling performance, progressively scaling up to deep refraction (`16–24px`) on desktop viewports.
   * **Bento Grid Layout:** Fully responsive grid styling using CSS Grid that stacks seamlessly into `1fr` on mobile and scales to an enhanced 12-column grid structure on tablet and desktop screens.
   * **Touch Target Optimization:** Guaranteed touch target dimensions (at least `44px`) across all interactive controls (buttons, links, inputs) for enhanced mobile usability.
   * **Clean Tap States:** Touchscreen-specific media features (`@media (hover: none)`) disable sticky button hover transforms on mobile.

2. **Security & Cryptography (Defense in Depth)**
   * **AES-256 Encryption at Rest:** Personally Identifiable Information (PII) such as phone numbers, permanent addresses, and Aadhar IDs are encrypted transparently in the SQLite database using Python's standard `cryptography` Fernet library.
   * **MFA Verification Gateways:** Secondary verification via SMS (powered by Twilio) or Email (via SMTP relay) with a 10-minute validity TTL.
   * **Google OAuth 2.0:** Integrated Google Sign-In via Authlib for federated identity verification.
   * **Content Security Policy (CSP):** Rigorous response headers restricting load scopes for script, style, and API resources to prevent Cross-Site Scripting (XSS) attacks.
   * **Private Payment Receipt Store:** Uploaded receipts are saved outside the public static directory inside the private `instance/` folder with randomized UUID filenames, served through a secure check-auth endpoint.
   * **Media Sanitization:** Profile photos and payment receipt uploads are passed through `Pillow` to strip location metadata (EXIF/GPS logs).
   * **Session Expiry & Revocation:** Auto-session invalidation across other active devices when a user's password changes, using a tracked `password_version`.

---

## Project Structure

```structure
hostel_management_system/
├── app/
│   ├── models/
│   │   └── db.py               # Database schema and Fernet encryption wrapper properties
│   ├── routes/
│   │   ├── admin.py            # SuperAdmin operations (creating owners & establishing hostels)
│   │   ├── owner.py            # Hostel Owner functions (verifying receipts, dynamic QR, settings)
│   │   ├── resident.py         # Resident portals (rent payment proof upload, profile access)
│   │   ├── settings.py         # Tabbed profile settings and MFA toggle settings
│   │   ├── auth.py             # Credentials gateways, Google OAuth client, OTP flows
│   │   └── api.py              # Scoped secure APIs for scanning resident QR cards
│   ├── static/
│   │   ├── css/style.css       # Premium responsive glassmorphic style system
│   │   └── js/script.js        # Camera scanner interface logic
│   ├── templates/              # HTML views (extends base.html viewport meta headers)
│   └── utils/
│       ├── encryption.py       # AES-256 cryptography helpers
│       ├── photo_handler.py    # Metadata sanitization and private file UUID handler
│       ├── qr_generator.py     # Dynamic profiles QR generator
│       ├── email_sender.py     # SMTP verification mail handler
│       └── sms_sender.py       # Twilio API SMS handler
├── instance/
│   ├── database.db             # Local SQLite database
│   └── uploads/payments/       # Secure offline receipt files
├── app.py                      # App factory runner
├── config.py                   # Environment configuration class definitions
├── requirements.txt            # System dependencies manifest
├── setup.bat / setup.sh        # Deployment bootstrappers
└── .env / .env.example         # System credentials and encryption key configurations
```

---

## Quick Start Guide

### Prerequisites

* Python 3.8 or higher installed on your system.
* A basic terminal environment (cmd, PowerShell, bash).

### Step 1: Initialize Local Environment Settings

1. Create a copy of `.env.example` named `.env`:
   * **Windows**: `copy .env.example .env`
   * **Linux/Mac**: `cp .env.example .env`
2. Open `.env` and fill in your integration variables:
   * Generate an `ENCRYPTION_KEY` using python:

     ```bash
     python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
     ```

   * Configure SMTP credentials, Twilio API tokens, and Google OAuth Client Secrets.

### Step 2: Run Setup Bootstrapper

Execute the automated script to configure virtual environments, setup directory storage, and generate database schemas:

* **Windows Command Prompt:**

  ```cmd
  setup.bat
  ```

* **Linux/Mac Bash Terminal:**

  ```bash
  chmod +x setup.sh
  ./setup.sh
  ```

### Step 3: Run the Development Server

1. Activate your virtual environment:
   * **Windows:** `venv\Scripts\activate`
   * **Linux/Mac:** `source venv/bin/activate`
2. Start Flask:

   ```bash
   python app.py
   ```

3. Open your browser and head to: **`http://localhost:5000`**

### Step 4: Login with Default SuperAdmin credentials

Use the default administrator account to establish the first hostel and manager accounts:

* **Username/Email:** `demo` (or custom `ADMIN_USERNAME` configured in `.env`)
* **Password:** `demo` (or custom `ADMIN_PASSWORD` configured in `.env`)

---

## Support & License

Distributed under the **MIT License**. For support, issues, or configuration queries, email: **<pranjalshukla2222@gmail.com>**.
