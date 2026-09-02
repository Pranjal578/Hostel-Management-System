# Product Requirements Document (PRD)
## ROOMMET — Multi-Tenant Hostel & Community Management SaaS Platform

---

## 1. Executive Summary

**ROOMMET** is an enterprise-grade, multi-tenant Software-as-a-Service (SaaS) platform built for hostel management, student accommodation operations, resident verification, and integrated hyper-local commerce (emergency pharmacy and daily essentials).

The platform bridges the operational divide between **Super Administrators**, **Hostel Owners / Property Managers**, **Residents (Students / Working Professionals)**, and **Verified Local Shop Owners** via:
1. A desktop-optimized, responsive web application built with Python Flask and a 2026 Glassmorphic design system.
2. A cross-platform mobile application built with Flutter (iOS / Android / Web) communicating via a secure REST API protected by JWT Bearer authentication.

---

## 2. Target Audience & Personas

| Role | Persona Description | Key Objectives |
|------|---------------------|----------------|
| **SuperAdmin** | Platform Operator (e.g. `pranjalshukla2222@gmail.com`) | Oversee global platform health, onboard hostel owners, assign properties, approve pharmacy vendors, inspect audit logs, and trigger encrypted database backups. |
| **HostelOwner** | Property Proprietor / Warden | Manage one or more hostel properties, approve resident registration requests, allot rooms, set rent/electricity billing, verify UPI screenshot receipts, broadcast notice bulletins, and chat directly with tenants. |
| **Resident** | Student or Tenant | Discover hostels via unique join codes (`HOS-YYYY-NNN`), obtain a dynamic QR digital identity card, upload payment proofs, order OTC medicines, view real-time notices, and submit support tickets. |
| **ShopOwner** | Local Chemist / Convenience Store | Manage medicine/goods inventory, review student prescription requests, fulfill delivery/pickup orders, and track revenue. |

---

## 3. Core Functional Modules

### 3.1. Authentication, Authorization & Security
- **Multi-Factor Authentication (MFA / 2FA):** Mandatory 6-digit cryptographic Time/HMAC-based OTP verification sent via SMTP Email (or Twilio SMS fallback) for all user accounts.
- **Role-Based Access Control (RBAC):** Strict role hierarchies (`SuperAdmin`, `HostelOwner`, `Resident`, `ShopOwner`) enforced via decorator gates (`@role_required`) and session/token validation.
- **Google OAuth 2.0:** High-assurance federated authentication for verified Google accounts.
- **Session Integrity & Invalidation:** Monotonic `password_version` tracking that revokes all active sessions across devices upon password rotation.
- **End-to-End Cryptography:** Field-level AES-256 Fernet encryption at rest for sensitive PII (Resident phone numbers, permanent residential addresses, and 12-digit Indian Aadhar IDs).
- **HTTP Hardening:** HSTS (`max-age=31536000; includeSubDomains; preload`), ProxyFix header reconciliation, CSRF token validation on web forms, and nosniff/XSS-protection headers.

### 3.2. Hostel Multi-Tenancy & Discovery
- **Unique Hostel Identification:** Auto-generated human-readable codes (`HOS-YYYY-NNN`) and scannable QR cards for every registered property.
- **Public Discovery Portal:** Fast search and filtering across locations, property names, owner profiles, and amenities (Wi-Fi, AC, Mess, Power Backup).
- **Dynamic Pricing:** Property-level and resident-level custom base rent and variable electricity billing configuration.

### 3.3. Resident Lifecycle & Digital Identity
- **Self-Service Registration:** Tenant registration with unique hostel code linkage, 12-digit Aadhar validation, and optional profile photo upload with automated EXIF/GPS metadata stripping.
- **Automated Digital QR Identity:** High-resolution dynamic QR badges linking to public verification endpoints for security guard validation at hostel entry gates.
- **Profile Management:** Secure portal to update emergency contacts, guardian credentials, and residential details.

### 3.4. Ledger, Billing & Fast UPI Payments
- **Dynamic UPI QR Presentation:** Owners upload property-specific UPI QR codes; residents scan and remit rent directly.
- **Payment Verification Workflow:** Residents upload payment transaction screenshots (validated against magic bytes); owners review in an approval queue (Verify or Reject with reason).
- **Email Notifications:** Automated email dispatches upon payment receipt submission, approval, or rejection.
- **Encrypted Access Route:** Payment receipts are shielded behind session/JWT-verified access endpoints (`/secure-receipt/<filename>`) to prevent unauthorized scraping.

### 3.5. Internal Communications & Community
- **Notice Bulletin System:** Urgent announcements with email broadcasting to all registered tenants in the property.
- **Direct Messaging Hub:** WhatsApp-style asynchronous messaging channels between residents and property owners.

### 3.6. Hyper-Local Emergency Pharmacy Marketplace
- **Catalog Management:** OTC medicines, first-aid kits, and daily essentials with dosage guidelines and price tagging.
- **Prescription & Direct Ordering:** Resident checkout with cash-on-delivery (COD) or UPI advance payment.
- **Vendor Onboarding & Verification:** SuperAdmin approval workflow for local pharmacy stores.

---

## 4. Non-Functional Requirements (NFRs)

| Dimension | Requirement | Specification / Metric |
|-----------|-------------|------------------------|
| **Security** | OWASP Top 10 Compliance | Centralized server-side validation (`validators.py`), rate-limiting on all auth/admin routes, magic-byte inspection, AES-256 Fernet encryption for PII. |
| **Performance** | Web Response Time | Sub-150ms 95th percentile response time for database queries via SQLAlchemy index optimizations and joined eager loads. |
| **Availability** | Uptime & Resilience | Stateless web container design suitable for Railway, DigitalOcean App Platform, and AWS Elastic Beanstalk; automated SQLite/PostgreSQL self-healing migrations on start. |
| **Scalability** | Multi-Tenancy Isolation | Row-Level Security (RLS) filters scoped by `owner_id` and `hostel_id` preventing cross-tenant data leakage. |
| **Accessibility** | WCAG 2.1 AA Compliance | Skip-to-content links, semantic HTML5 landmarks, high-contrast dark/light mode toggle, keyboard navigation (`?`, `Ctrl+K`, `Alt+T`), and screen-reader ARIA tags. |
| **Data Retention & Backup** | Disaster Recovery | CLI-based hot database backup tool (`python manage.py backup --keep N`) with support for SQLite file snapshots and PostgreSQL `pg_dump` streaming. |

---

## 5. User Journey & Workflow Diagrams

```
[ Unauthenticated Visitor ]
           │
     ┌─────┴──────────────────────────────┐
     ▼                                    ▼
[ Browse Hostels ]                 [ Login Portal ]
     │                                    │
     ▼                                    ▼
[ Register with Code ] ───► [ Enter Email & Password ]
(HOS-YYYY-NNN)                            │
                                          ▼
                               [ Mandatory 2FA OTP ]
                               (Sent via Email/SMS)
                                          │
                                          ▼
                         ┌─────────────────────────────────┐
                         │ Role-Based Routing Gate         │
                         └────────────────┬────────────────┘
           ┌─────────────────┬────────────┴───────┬─────────────────┐
           ▼                 ▼                    ▼                 ▼
   [ SuperAdmin ]     [ HostelOwner ]        [ Resident ]     [ ShopOwner ]
   - Global Metrics   - Tenant Approvals     - Digital ID QR  - Inventory
   - Onboard Owners   - UPI Billing/Receipts - Upload Payment - Orders Queue
   - Backup CLI       - Broadcast Notices    - Chat / Notices - Reviews
   - Approve Shops    - Property Scanner     - Pharmacy Store - Store Settings
```

---

## 6. Success Metrics & Key Performance Indicators (KPIs)

1. **Zero Data Breach Incident Rate:** 100% masking and AES-256 encryption on all stored identity/Aadhar credentials.
2. **Payment Reconcile Turnaround:** Sub-2-hour average verification turnaround from resident screenshot upload to owner verification.
3. **MFA Adherence:** 100% login enforcement across all user roles via cryptographic OTP challenge.
4. **Mobile Responsiveness:** Zero layout breaks across viewport widths from 320px (mobile) to 4K ultra-wide screens.
