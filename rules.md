# Engineering Guidelines, Security Rules & Coding Standards
## ROOMMET — Multi-Tenant Hostel SaaS Platform

---

## 1. Security & Compliance Rules (Zero-Tolerance Invariants)

1. **Mandatory 2-Factor Authentication (2FA):**
   - Every user account must undergo OTP verification upon password login.
   - 2FA cannot be globally bypassed; default delivery channel is email, with SMS as an optional tenant channel.
2. **Never Commit Secrets or Plaintext Credentials:**
   - `.env` files and `.db` database files must always be listed in `.gitignore`.
   - Never hardcode database connection strings, JWT signing keys, or API tokens in Python or Flutter source files.
3. **No Direct Unsanitized File Uploads:**
   - Every file upload must pass through `validate_image_upload` or `validate_photo` in `app/utils/validators.py`.
   - Magic bytes must be verified (JPEG: `\xff\xd8\xff`, PNG: `\x89PNG`).
   - Image metadata (EXIF/GPS) must be stripped via Pillow before persisting to disk.
4. **Row-Level Security (RLS) & Multi-Tenant Isolation:**
   - Hostel Owners must never be able to query, edit, or delete records (Residents, Payments, Notices) belonging to another owner's properties.
   - All tenant queries in `owner_bp` must filter by `hostel_id.in_(owner_hostel_ids)`.
5. **Session Security & Invalidation:**
   - When a user changes their password, `password_version` must be incremented.
   - The `@app.before_request` hook invalidates all sessions matching the old password version.
6. **PII Cryptography at Rest:**
   - Phone numbers, home addresses, and 12-digit Indian Aadhar IDs must be encrypted using `AES-256 Fernet` (`app/utils/encryption.py`) before writing to the database.

---

## 2. Backend Python & Flask Coding Rules

1. **Application Factory Pattern:**
   - Always instantiate blueprints, extensions, and configuration inside `create_app()` in `app/__init__.py`.
2. **Route Authorization Decorators:**
   - Protected web routes must use `@role_required('SuperAdmin', 'HostelOwner', ...)` from `app.routes.auth`.
   - Mobile API routes must validate JWT Bearer tokens via `verify_jwt_token`.
3. **Rate Limiting on Sensitive Endpoints:**
   - Auth endpoints (`/login`, `/verify-otp`, `/resend-otp`) must have strict limits (e.g. `5 per minute`).
   - Registration endpoints (`/register`, `/register/owner`) must be restricted to prevent spam (e.g. `5 per hour`).
4. **Centralized Input Validation:**
   - Always import and use validators from `app.utils.validators` (`validate_email`, `validate_phone`, `validate_password`, `validate_aadhar`, `validate_pincode`, `validate_capacity`, `validate_text_field`, `collect_errors`).
   - Never rely solely on client-side HTML form validation.
5. **Database Queries & Migrations:**
   - Use SQLAlchemy ORM relationships and eager joins (`joinedload`) when querying nested resident/hostel data to avoid N+1 query bottlenecks.
   - Schema modifications must be supported by Flask-Migrate migration scripts or self-healing migrations in `app/__init__.py`.

---

## 3. Frontend UI/UX & Styling Rules

1. **Design Aesthetics:**
   - Use curated dark glassmorphic styling based on the design system defined in `style.css`.
   - Primary accents: `#38bdf8` (Sky Blue) and `#a855f7` (Vibrant Purple).
   - Card backgrounds: semi-transparent RGBA with backdrop blur (`backdrop-filter: blur(12px)`).
2. **Accessibility Standards:**
   - All interactive elements must have visible focus rings and appropriate `aria-label` / `aria-expanded` attributes.
   - Include skip-to-content links on every template.
   - Maintain color contrast ratios compliant with WCAG 2.1 AA.
3. **Responsiveness:**
   - Mobile menu overlay must operate cleanly on touchscreens (<768px).
   - Bento grids must automatically reflow from 12-column desktop layouts to single-column mobile views.
4. **No External CSS Framework Dependency:**
   - Do not inject TailwindCSS or Bootstrap unless explicitly requested by the user. Use Vanilla CSS with design system custom tokens.

---

## 4. Database Backup & Maintenance Rules

1. **Disaster Recovery:**
   - Always test database backup mechanisms using `python manage.py backup`.
   - Retain at least 7 rolling timestamped backups in the `backups/` directory.
2. **Deployment Verification:**
   - Run `python manage.py check` before promoting code to production.
   - Ensure `SECRET_KEY` and `ENCRYPTION_KEY` are provisioned in production environments.
