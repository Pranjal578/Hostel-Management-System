# System Architecture & Technical Specifications
## ROOMMET — Multi-Tenant Hostel SaaS Platform

---

## 1. High-Level Architecture Diagram

```
                               ┌────────────────────────┐
                               │     Client Devices     │
                               └───────────┬────────────┘
                                           │
                    ┌──────────────────────┴──────────────────────┐
                    ▼                                             ▼
          ┌────────────────────┐                        ┌────────────────────┐
          │ Modern Web Browser │                        │ Flutter Mobile App │
          │ (HTML5 / CSS / JS) │                        │  (iOS/Android/Web) │
          └─────────┬──────────┘                        └─────────┬──────────┘
                    │ HTTPS (Session Cookie / CSRF)               │ HTTPS (JWT Bearer)
                    └──────────────────────┬──────────────────────┘
                                           │
                                           ▼
          ┌─────────────────────────────────────────────────────────────────┐
          │               Reverse Proxy & TLS Termination                   │
          │             (Nginx / Caddy / Cloudflare / DO / Railway)         │
          └────────────────────────────────┬────────────────────────────────┘
                                           │ X-Forwarded-For, X-Forwarded-Proto
                                           ▼
          ┌─────────────────────────────────────────────────────────────────┐
          │                   Flask Application Server                      │
          │                   (WSGI / Gunicorn / ProxyFix)                  │
          │                                                                 │
          │  ┌───────────────────────────────────────────────────────────┐  │
          │  │ Security & Middleware Layer                               │  │
          │  │ • HSTS (1 yr) • Nosniff • FrameOptions • RateLimiter      │  │
          │  │ • CSRF Protection • Session Invalidation (Password Ver)   │  │
          │  └─────────────────────────────┬─────────────────────────────┘  │
          │                                │                                │
          │  ┌─────────────────────────────┴─────────────────────────────┐  │
          │  │ Route Controllers & Blueprints                            │  │
          │  │ • AuthBP (`/`)          • AdminBP (`/admin`)              │  │
          │  │ • OwnerBP (`/owner`)    • ResidentBP (`/resident`)        │  │
          │  │ • SettingsBP (`/settings`) • PharmacyBP (`/pharmacy`)     │  │
          │  │ • MobileApiBP (`/api/mobile`)                             │  │
          │  └─────────────────────────────┬─────────────────────────────┘  │
          │                                │                                │
          │  ┌─────────────────────────────┴─────────────────────────────┐  │
          │  │ Services & Utilities Layer                                │  │
          │  │ • Validators (Magic bytes, RFC email, phone, aadhar)      │  │
          │  │ • AES-256 Fernet Encryption Engine                        │  │
          │  │ • OTP Engine (HMAC hashing, 10-min TTL)                   │  │
          │  │ • QR Code Generator & Pillow EXIF Sanitizer               │  │
          │  │ • SMTP Mailer & Twilio SMS Sender                         │  │
          │  └─────────────────────────────┬─────────────────────────────┘  │
          │                                │                                │
          │  ┌─────────────────────────────┴─────────────────────────────┐  │
          │  │ SQLAlchemy ORM & Multi-Tenancy Data Access Layer (RLS)    │  │
          │  └─────────────────────────────┬─────────────────────────────┘  │
          └────────────────────────────────┼────────────────────────────────┘
                                           │
                    ┌──────────────────────┴──────────────────────┐
                    ▼                                             ▼
          ┌────────────────────┐                        ┌────────────────────┐
          │  Relational DB     │                        │ File Storage       │
          │  (PostgreSQL /     │                        │ (Instance Uploads  │
          │   SQLite Engine)   │                        │  & Static Assets)  │
          └────────────────────┘                        └────────────────────┘
```

---

## 2. Multi-Tenancy Data Architecture

The platform implements **Shared Database, Shared Schema Multi-Tenancy with Logical Row-Level Security (RLS)**:
- Every tenant property is identified by a unique `hostel_id` and unique alphanumeric join code `hostel_code` (`HOS-YYYY-NNN`).
- **HostelOwner Scope:** Route queries dynamically filter tables via `owner_id = session['user_id']` or `hostel_id.in_(owner_hostel_ids)`.
- **Resident Scope:** Tenants access records exclusively mapped to their foreign key `user_id` or assigned `hostel_id`.
- **SuperAdmin Scope:** Unrestricted platform-wide visibility across all hostel organizations.

```
       ┌────────────────┐
       │     User       │ (SuperAdmin, HostelOwner, Resident, ShopOwner)
       └───────┬────────┘
               │ 1:N
       ┌───────┴────────┐
       │     Hostel     │ (Managed by HostelOwner)
       └───────┬────────┘
               ├─────────────────────────────────────────┐
               │ 1:N                                     │ 1:N
       ┌───────┴────────┐                        ┌───────┴────────┐
       │    Resident    │                        │     Notice     │
       └───────┬────────┘                        └────────────────┘
               ├────────────────────────┬────────────────────────┐
               │ 1:N                    │ 1:N                    │ 1:N
       ┌───────┴────────┐       ┌───────┴────────┐       ┌───────┴────────┐
       │    Payment     │       │    Message     │       │   Cart/Order   │
       └────────────────┘       └────────────────┘       └────────────────┘
```

---

## 3. Database Schema Specification

### 3.1. Entity Relationship Details

| Model | Table Name | Key Attributes | Relationships |
|-------|------------|----------------|---------------|
| `User` | `users` | `id`, `email`, `password_hash`, `role`, `full_name`, `phone`, `otp_enabled`, `otp_code`, `otp_expires_at`, `otp_method`, `password_version` | Has many `Hostel`, has one `Resident`, has many `AuditLog` |
| `Hostel` | `hostels` | `id`, `owner_id` (FK), `hostel_name`, `location`, `total_capacity`, `rent`, `electricity_bill`, `hostel_code`, `facilities`, `hostel_qr_code`, `payment_qr_code` | Belongs to `User` (owner), has many `Resident`, `Payment`, `Notice` |
| `Resident` | `residents` | `id`, `user_id` (FK), `hostel_id` (FK), `full_name`, `date_of_birth`, `gender`, `phone_encrypted`, `permanent_address_encrypted`, `aadhar_id_encrypted`, `city`, `state`, `pincode`, `room_number`, `rent`, `electricity_bill`, `status`, `profile_image`, `qr_code` | Belongs to `User` & `Hostel`, has many `Payment` |
| `Payment` | `payments` | `id`, `resident_id` (FK), `hostel_id` (FK), `amount`, `payment_date`, `status` ('Pending', 'Verified', 'Rejected'), `screenshot_path`, `rejection_reason` | Belongs to `Resident` & `Hostel` |
| `Notice` | `notices` | `id`, `hostel_id` (FK), `title`, `description`, `created_at` | Belongs to `Hostel` |
| `Message` | `messages` | `id`, `sender_id` (FK), `receiver_id` (FK), `message_content`, `created_at`, `is_read` | Belongs to sender `User` & receiver `User` |
| `Shop` | `shops` | `id`, `owner_id` (FK), `shop_name`, `address`, `contact_phone`, `verification_status` | Belongs to `User`, has many `Medicine`, `Order` |
| `Medicine` | `medicines` | `id`, `shop_id` (FK), `name`, `category`, `price`, `stock_quantity`, `description`, `photo_url` | Belongs to `Shop` |
| `AuditLog` | `audit_logs` | `id`, `user_id` (FK), `action`, `ip_address`, `timestamp` | Belongs to `User` |

---

## 4. Cryptographic Storage & Security Pipeline

```
[ Raw User Input ] 
       │
       ▼
[ Server-Side Validation: validators.py ] ── (Fails) ──► [ Reject Request & Flash Error ]
       │ (Passes)
       ▼
[ PII Field Detection ] (Phone / Address / Aadhar)
       │
       ├── (Is PII) ──► [ AES-256 Fernet Engine (app/utils/encryption.py) ] ──► [ Encrypted Ciphertext ] ──┐
       │                                                                                                    │
       └── (Non-PII) ───────────────────────────────────────────────────────────────────────────────────────┴──► [ SQLAlchemy DB Commit ]
```

### 4.1. Key Security Safeguards
1. **At-Rest Field Encryption:** Master encryption key generated via `Fernet.generate_key()`. PII is never stored in plain text.
2. **Deterministic & Safe Masking:** Public ID verification views show masked Aadhar numbers (e.g. `XXXX-XXXX-1234`) and obscured contact numbers.
3. **Session Invalidation:** Each `User` record holds a monotonic `password_version`. The `@app.before_request` hook matches `session['password_version'] == user.password_version`, immediately terminating stale sessions when credentials change.
4. **Receipt Access Control Gate:** Payment screenshots are stored outside web-accessible roots and served solely through `/secure-receipt/<filename>` with RBAC ownership checks.

---

## 5. Authentication Engine (Web vs Mobile API)

| Feature | Web Application Flow | Mobile API Flow (`/api/mobile/*`) |
|---------|----------------------|-----------------------------------|
| **Auth Mechanism** | HTTPOnly, SameSite=Lax Secure Cookie Session | JWT Bearer Token in `Authorization` header |
| **CSRF Protection** | Flask-WTF CSRF Token in Forms/AJAX Headers | CSRF Exempt (Stateless Bearer Tokens) |
| **2FA Verification** | Session pending state `otp_pending_user_id` → `/verify-otp` | Pre-auth token → `/auth/verify-otp` → Full JWT |
| **Google Sign-In** | Authlib OAuth 2.0 Web Redirection Callback | Client passes Google ID Token → Verified via `google-auth` |
| **Rate Limiting** | Flask-Limiter by remote IP (`ProxyFix` adjusted) | Flask-Limiter by IP & JWT Subject |

---

## 6. REST API Endpoint Mapping (`/api/mobile/*`)

| Method | Endpoint | Auth Required | Description |
|--------|----------|---------------|-------------|
| `POST` | `/api/mobile/auth/login` | None | Initial credential verification; dispatches 2FA OTP code. |
| `POST` | `/api/mobile/auth/verify-otp` | Pre-Auth | Validates OTP and issues 24-hour access JWT. |
| `POST` | `/api/mobile/auth/google` | None | Exchanges Google ID token for access JWT. |
| `GET` | `/api/mobile/resident/profile` | Resident JWT | Retrieves authenticated resident profile, room allotment, and QR badge. |
| `GET` | `/api/mobile/resident/payments` | Resident JWT | Lists billing history and payment verification statuses. |
| `POST` | `/api/mobile/resident/payments/upload` | Resident JWT | Uploads UPI transaction screenshot proof. |
| `GET` | `/api/mobile/resident/notices` | Resident JWT | Fetches active hostel notice announcements. |
| `GET` | `/api/mobile/pharmacy/medicines` | JWT | Lists available marketplace medicines and essentials. |
| `POST` | `/api/mobile/pharmacy/order` | JWT | Places an order for delivery/pickup from local shop. |

---

## 7. Infrastructure, Runtime & Deployment Topologies

- **Runtime:** Python 3.10+ / Linux x86_64.
- **Web Server:** Gunicorn WSGI container behind reverse proxy (Nginx or Cloud PaaS Load Balancer).
- **Database Support:** Dual-mode SQLite (development/local instance) and PostgreSQL 14+ (production cloud instances via `DATABASE_URL`).
- **Asset Pipeline:** Vanilla CSS with custom property variables, vanilla ES6 modular JS with no bundler dependencies.
