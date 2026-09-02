# Central System Brain & Cognitive Index
## ROOMMET — Multi-Tenant Hostel & Community Management SaaS Platform

---

## 1. System Identity & Mental Model

**ROOMMET** is a production-hardened, multi-tenant SaaS ecosystem providing end-to-end digital operations for hostel properties, resident verification, rent ledger workflows, and integrated emergency commerce (pharmacy / convenience stores).

```
 ┌────────────────────────────────────────────────────────────────────────────┐
 │                               ROOMMET BRAIN                                │
 ├─────────────────────────────────────┬──────────────────────────────────────┤
 │  🌐 Web Platform (Flask + Jinja2)   │  📱 Mobile Client (Flutter + Dio)    │
 │  • Role Dashboards & Admin Controls │  • Native UI for iOS / Android / Web │
 │  • Session Cookies & CSRF Protection│  • Stateless JWT Bearer Token Auth   │
 ├─────────────────────────────────────┴──────────────────────────────────────┤
 │                     ⚙️ Shared Backend & Security Engine                     │
 │  • Mandatory 2FA OTP Engine         • AES-256 Fernet PII Encryption        │
 │  • Dynamic QR Code Generator        • Magic-Byte File Upload Validation    │
 │  • HSTS, ProxyFix & CORS Middleware • Row-Level Multi-Tenancy Security     │
 ├────────────────────────────────────────────────────────────────────────────┤
 │                        🗄️ Unified Common Database                          │
 │         Single Source of Truth: SQLite / PostgreSQL (Relational)           │
 └────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Platform Core Invariants & Governance

1. **Shared Common Database:** Both the Web Application and the Flutter Mobile Client query and modify the same database in real-time.
2. **Mandatory Google OAuth 2.0 Authentication:** All users authenticate via Google Sign-In as the mandatory unified gateway.
3. **Primary SuperAdmin Guarantee:** Account `pranjalshukla2222@gmail.com` is permanently provisioned and verified as `SuperAdmin` on every application boot.
4. **Strict Multi-Tenancy Isolation:** Owners can only access, edit, or delete records associated with their assigned hostels via `hostel_id.in_(owner_hostels)`.
5. **PII Cryptography at Rest:** Indian 12-digit Aadhar IDs, resident phone numbers, and permanent addresses are AES-256 Fernet encrypted at rest.
6. **Disaster Recovery:** Rolling automated backups via `python manage.py backup --keep N`.

---

## 3. Registered Google Accounts & Access Matrix

| Role | Verified Google Email | Access Level & Scope |
|------|-----------------------|----------------------|
| **SuperAdmin** | `pranjalshukla2222@gmail.com` | Global Platform Governance, Database Backups, Owner & Shop Approvals |
| **HostelOwner** | `shyamshukla@gmail.com` | Property Management (*Vishnu Villa*, *Vaishnavi Palace*), Tenant Ledger, UPI Payments |
| **Resident** | `pranjal6466@gmail.com` | Digital QR ID, Rent Payment Uploads, Notice Bulletins, Tenant Support |
| **Resident** | `rishabh@gmail.com` | Secondary Tenant Profile |
| **ShopOwner** | `tiwari@gmail.com` | Local Chemist & Convenience Store, Prescription Orders & Inventory |


---

## 4. Master Documentation Sitemap

| Document | Primary Focus | Absolute Link |
|----------|---------------|---------------|
| **`PRD.md`** | Product Requirements, Personas, Functional Modules, NFRs | [`PRD.md`](file:///home/pj/Projects/hostel_management_system/PRD.md) |
| **`architecture.md`** | System Architecture, Data Flows, Schemas, Security Pipelines | [`architecture.md`](file:///home/pj/Projects/hostel_management_system/architecture.md) |
| **`rules.md`** | Security Rules, OWASP Compliance, Input Validation, Coding Standards | [`rules.md`](file:///home/pj/Projects/hostel_management_system/rules.md) |
| **`phases.doc.md`** | Milestone Roadmap, Phases 1–8 Deliverables, Version Changelog | [`phases.doc.md`](file:///home/pj/Projects/hostel_management_system/phases.doc.md) |
| **`design.md`** | 2026 Dark Glassmorphism, Color Tokens, Bento Grids, Shortcuts | [`design.md`](file:///home/pj/Projects/hostel_management_system/design.md) |
| **`memory.md`** | System State, File Tree, Key Decisions, Operational Runbooks | [`memory.md`](file:///home/pj/Projects/hostel_management_system/memory.md) |
| **`brain.md`** | *This Document* — Central Cognitive Index & Mental Model | [`brain.md`](file:///home/pj/Projects/hostel_management_system/brain.md) |

---

## 5. Operational Commands Quick Reference

```bash
# 1. Start the Flask Backend (Daemon):
./.venv/bin/python app.py

# 2. Run the Flutter Mobile App (Chrome):
cd roommet_flutter && flutter run -d chrome

# 3. Create a Timestamped Database Backup:
./.venv/bin/python manage.py backup

# 4. System Deployment Diagnostics:
./.venv/bin/python manage.py check

# 5. Database Migrations Upgrade:
./.venv/bin/python manage.py init-db
```

---

## 6. Troubleshooting & Diagnostics Runbook

### Issue: "Login failed. Check your connection" in Flutter
- **Check 1:** Ensure Flask is running (`curl -I http://127.0.0.1:5000/api/mobile/hostels/public`). If not, launch via `./.venv/bin/python app.py`.
- **Check 2:** Confirm CORS headers are returned (`Access-Control-Allow-Origin: *`).
- **Check 3:** Verify `AppConfig.baseDomain` in [`roommet_flutter/lib/core/config/app_config.dart`](file:///home/pj/Projects/hostel_management_system/roommet_flutter/lib/core/config/app_config.dart) points to `http://127.0.0.1:5000` during local development.

### Issue: 2FA OTP Delivery
- In local development without SMTP configured, the generated 6-digit OTP code is printed directly to the terminal stdout/logs.
