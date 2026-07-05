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
│   ├── database.db             # Local SQLite database (git-ignored)
│   └── uploads/payments/       # Secure offline receipt files
├── app.py                      # App factory runner
├── config.py                   # Environment configuration class definitions
├── requirements.txt            # System dependencies manifest
├── Dockerfile                  # Production containerization setup
├── setup.bat / setup.sh        # Local development bootstrappers
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

3. Open your browser and head to: [http://localhost:5000](http://localhost:5000)

### Step 4: Login with Default SuperAdmin credentials

Use the default administrator account to establish the first hostel and manager accounts:

* **Username/Email:** `demo` (or custom `ADMIN_USERNAME` configured in `.env`)
* **Password:** `demo` (or custom `ADMIN_PASSWORD` configured in `.env`)

---

## DigitalOcean App Platform Deployment

Deploying the system using Docker and DigitalOcean's managed services ensures a robust, production-grade SaaS delivery pipeline.

### Step 1: Prepare Your Project

Make sure all your source code changes are committed and pushed to your GitHub repository.
The included [Dockerfile](file:///d:/Program%20Files/code/projects/hostel_management_system/Dockerfile) is fully configured for Python 3.11-slim, installs necessary system packages (for building modules), and binds the application to port `8080` using `gunicorn`.

### Step 2: Create App on DigitalOcean App Platform

1. Log in to your **DigitalOcean Control Panel**.
2. Click **Create** in the top right, then select **Apps**.
3. Choose **GitHub** as the source, authorize DigitalOcean access if prompted, and select your repository and deployment branch (e.g., `main`).
4. Click **Next**.

### Step 3: Configure Resources & Database

1. DigitalOcean will automatically detect the `Dockerfile` at the root of the project.
2. Under **HTTP Routes**, ensure the port is set to `8080` (this matches the `gunicorn` bind command in the Dockerfile).
3. Under **Resources**, click **Add Database**.
   * Select **PostgreSQL** as the database engine.
   * Choose the cluster size and plan that suits your volume.
   * DigitalOcean will automatically inject the connection string as the `DATABASE_URL` environment variable. Our app automatically handles converting `postgres://` prefixes to `postgresql://` so that SQLAlchemy integrates seamlessly.

### Step 4: Setup Environment Variables

Under the **App Settings** -> **Environment Variables** panel in DigitalOcean, manually add your system secrets (mirroring `.env` settings):

* `SECRET_KEY`: (A secure random 32-byte hex key)
* `ENCRYPTION_KEY`: (Your generated 32-byte AES Fernet encryption key)
* `ADMIN_USERNAME`: (Production SuperAdmin email/username)
* `ADMIN_PASSWORD`: (Production SuperAdmin secure password)
* `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET`: (OAuth 2.0 Client credentials)
* `MAIL_SERVER` / `MAIL_PORT` / `MAIL_USERNAME` / `MAIL_PASSWORD`: (Your SMTP server credentials)
* `TWILIO_ACCOUNT_SID` / `TWILIO_AUTH_TOKEN` / `TWILIO_PHONE_NUMBER`: (Your Twilio credentials, if using SMS)

### Step 5: Database Schema Initialization & Migrations

The application is pre-configured with **Flask-Migrate**.
On every startup (including when DigitalOcean spins up your Docker container), the application context automatically checks for and applies any pending migrations to ensure your SQL database is fully up-to-date with your models.

Should you need to manually force table updates or verify the database state:

1. Navigate to the **Console** tab of your App service component in DigitalOcean.
2. Execute the initialization command:

   ```bash
   python manage.py init-db
   ```

---

## Database Migrations (Flask-Migrate)

When you modify database models in `app/models/db.py` during development, you should record and apply schema migrations:

1. **Create a migration script** (detects model changes):

   ```bash
   flask db migrate -m "Describe your schema change"
   ```

2. **Apply the migration locally**:

   ```bash
   flask db upgrade
   ```

3. **Deploy the migration**:
   Commit the generated script in `migrations/versions/` to your Git repository. On your next push, DigitalOcean App Platform will automatically apply the database upgrade script on startup!

## Support & License

Distributed under the **MIT License**. For support, issues, or configuration queries, email: [pranjalshukla2222@gmail.com](mailto:pranjalshukla2222@gmail.com).
