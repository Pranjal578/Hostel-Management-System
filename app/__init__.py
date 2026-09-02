import os
import sys
import warnings
from flask import Flask, redirect, url_for, session, render_template, request
from app.models.db import db, User
from app.utils.email_sender import init_mail
from config import DevelopmentConfig, ProductionConfig
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from authlib.integrations.flask_client import OAuth
from flask_migrate import Migrate
from werkzeug.middleware.proxy_fix import ProxyFix

# ─────────────────────────────────────────────────────────────
# Global Extensions (initialized per-app in create_app)
# ─────────────────────────────────────────────────────────────
csrf    = CSRFProtect()
limiter = Limiter(key_func=get_remote_address, default_limits=["300 per day", "60 per hour"])
oauth   = OAuth()
migrate = Migrate()

# Default weak secret used in development only — never acceptable in production
_INSECURE_DEFAULTS = {
    'your-super-secret-key-change-in-production',
    'dev-secret-key',
    'changeme',
    'secret',
    '',
}


def _startup_security_check(app: Flask) -> None:
    """Emit loud warnings for insecure production configurations at startup."""
    secret = app.config.get('SECRET_KEY', '')
    env    = os.environ.get('FLASK_ENV', 'development')

    if env == 'production':
        if not secret or secret.lower() in _INSECURE_DEFAULTS or len(secret) < 24:
            msg = (
                "\n\n"
                "╔══════════════════════════════════════════════════════════╗\n"
                "║  ⚠  CRITICAL SECURITY WARNING                           ║\n"
                "║  SECRET_KEY is insecure or not set.                     ║\n"
                "║  Generate one with:                                      ║\n"
                "║    python manage.py generate-secret                      ║\n"
                "║  Then set it in your .env file.                          ║\n"
                "╚══════════════════════════════════════════════════════════╝\n"
            )
            print(msg, file=sys.stderr)
            warnings.warn(msg, RuntimeWarning, stacklevel=2)
    else:
        # Development: softer notice
        if not secret or secret.lower() in _INSECURE_DEFAULTS:
            print("[SECURITY-DEV] SECRET_KEY is using a default/empty value. "
                  "Run `python manage.py generate-secret` to create a secure key.", file=sys.stderr)


def create_app(config_name=None):
    """Application Factory — creates and fully configures the Flask app."""
    app = Flask(__name__)

    # ── Load Configuration ─────────────────────────────────────
    env = os.environ.get('FLASK_ENV', 'development')
    if config_name == 'production' or env == 'production':
        app.config.from_object(ProductionConfig)
    else:
        app.config.from_object(DevelopmentConfig)

    # ── Secure-Cookie Settings ─────────────────────────────────
    # SESSION_COOKIE_SECURE requires HTTPS; safe to set False in dev
    if env == 'production':
        app.config.setdefault('SESSION_COOKIE_SECURE', True)
        app.config.setdefault('SESSION_COOKIE_HTTPONLY', True)
        app.config.setdefault('SESSION_COOKIE_SAMESITE', 'Lax')
        app.config.setdefault('REMEMBER_COOKIE_SECURE', True)
        app.config.setdefault('REMEMBER_COOKIE_HTTPONLY', True)
    else:
        app.config.setdefault('SESSION_COOKIE_HTTPONLY', True)
        app.config.setdefault('SESSION_COOKIE_SAMESITE', 'Lax')
        app.config.setdefault('SESSION_COOKIE_SECURE', False)

    # ── ProxyFix: trust X-Forwarded-* from one upstream proxy ─
    # Required to receive real client IPs for rate limiting when
    # running behind Nginx, Caddy, Railway, or DigitalOcean proxies.
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    # ── Startup Checks ─────────────────────────────────────────
    _startup_security_check(app)

    # ── Ensure instance folder exists ──────────────────────────
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # ── Initialize Extensions ──────────────────────────────────
    db.init_app(app)
    init_mail(app)
    csrf.init_app(app)
    limiter.init_app(app)
    oauth.init_app(app)
    migrate.init_app(app, db)

    # ── Google OAuth Client ────────────────────────────────────
    oauth.register(
        name='google',
        client_id=app.config.get('GOOGLE_CLIENT_ID') or 'placeholder-id',
        client_secret=app.config.get('GOOGLE_CLIENT_SECRET') or 'placeholder-secret',
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email profile'}
    )

    # ── Register Blueprints ────────────────────────────────────
    from app.routes.auth       import auth_bp
    from app.routes.admin      import admin_bp
    from app.routes.owner      import owner_bp
    from app.routes.resident   import resident_bp
    from app.routes.settings   import settings_bp
    from app.routes.api        import api_bp
    from app.routes.pharmacy   import pharmacy_bp
    from app.routes.mobile_api import mobile_api_bp

    app.register_blueprint(auth_bp,       url_prefix='/')
    app.register_blueprint(admin_bp,      url_prefix='/admin')
    app.register_blueprint(owner_bp,      url_prefix='/owner')
    app.register_blueprint(resident_bp,   url_prefix='/resident')
    app.register_blueprint(settings_bp,   url_prefix='/settings')
    app.register_blueprint(api_bp,        url_prefix='/api')
    app.register_blueprint(pharmacy_bp,   url_prefix='/pharmacy')
    # Mobile API uses JWT Bearer tokens — exempt from CSRF cookie checks
    app.register_blueprint(mobile_api_bp, url_prefix='/api/mobile')
    csrf.exempt(mobile_api_bp)

    # ── Application Context: DB self-healing & migrations ──────
    with app.app_context():
        _ensure_static_dirs(app)
        _run_migrations(app)
        _self_heal_db()

    # ── Before-Request: Session Integrity & CORS Preflight ─────
    @app.before_request
    def handle_preflight_and_session():
        # Handle CORS preflight for mobile API
        if request.method == 'OPTIONS' and request.path.startswith('/api/'):
            from flask import Response
            resp = Response()
            origin = request.headers.get('Origin', '*')
            resp.headers['Access-Control-Allow-Origin'] = origin
            resp.headers['Access-Control-Allow-Credentials'] = 'true'
            resp.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS, PATCH'
            resp.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With, Accept, Origin'
            return resp

        # Invalidate session if password version changed
        if 'user_id' in session:
            user = User.query.get(session['user_id'])
            if not user or session.get('password_version') != user.password_version:
                session.clear()

    # ── Default Landing Route ──────────────────────────────────
    @app.route('/')
    def index():
        from app.models.db import Resident, Hostel, Payment
        verified_residents_count = Resident.query.filter_by(status='Active').count()
        connected_hostels_count = Hostel.query.count()
        hostels = Hostel.query.all()
        total_rooms_count = sum(h.total_capacity for h in hostels)
        total_rent_reconciled = db.session.query(db.func.sum(Payment.amount)).filter(Payment.status == 'Verified').scalar() or 0.0
        return render_template(
            'index.html',
            verified_residents_count=verified_residents_count,
            connected_hostels_count=connected_hostels_count,
            total_rooms_count=total_rooms_count,
            total_rent_reconciled=total_rent_reconciled
        )

    # ── Security & CORS Headers (after_request) ────────────────
    @app.after_request
    def add_security_headers(response):
        # Attach CORS headers to /api/ endpoints for mobile/Flutter clients
        if request.path.startswith('/api/'):
            origin = request.headers.get('Origin', '*')
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS, PATCH'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With, Accept, Origin'

        # HTTP Strict Transport Security — 1 year, include subdomains
        # Only sent over HTTPS; Nginx/Caddy will strip it in HTTP-only setups.
        response.headers['Strict-Transport-Security'] = (
            'max-age=31536000; includeSubDomains; preload'
        )
        response.headers['X-Content-Type-Options']  = 'nosniff'
        response.headers['X-Frame-Options']          = 'SAMEORIGIN'
        response.headers['X-XSS-Protection']         = '1; mode=block'
        response.headers['Referrer-Policy']          = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = (
            'camera=(), microphone=(), geolocation=(), payment=()'
        )
        # Content-Security-Policy
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://unpkg.com https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: blob:; "
            "connect-src 'self' *;"
        )
        return response

    return app


# ─────────────────────────────────────────────────────────────
# Internal Helpers
# ─────────────────────────────────────────────────────────────

def _ensure_static_dirs(app: Flask) -> None:
    """Create required static upload directories if they don't exist."""
    dirs = [
        os.path.join(app.root_path, 'static', 'images', 'medicines'),
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)


def _run_migrations(app: Flask) -> None:
    """Auto-apply database migrations on startup (non-test environments)."""
    if app.config.get('TESTING'):
        return
    migrations_dir = os.path.join(os.path.dirname(app.root_path), 'migrations')
    if os.path.exists(migrations_dir):
        try:
            from flask_migrate import upgrade as db_upgrade
            db_upgrade()
            print("[OK] Database migrations upgraded/applied successfully.")
        except Exception as e:
            print(f"[WARN] Migrations auto-upgrade failed: {e}. Falling back to default initialization.")
    else:
        print("[INFO] Migrations directory not found. Skipping auto-upgrade.")


def _self_heal_db() -> None:
    """Self-heal DB schema and data inconsistencies at startup."""
    try:
        from app.models.db import Payment, Hostel
        from app.utils.qr_generator import generate_hostel_qr
        from sqlalchemy import text

        with db.engine.connect() as conn:
            # Add full_name / phone columns to users if missing
            try:
                conn.execute(text("SELECT full_name, phone FROM users LIMIT 1"))
            except Exception:
                print("[INFO] Adding full_name and phone columns to users table...")
                for col_sql in [
                    "ALTER TABLE users ADD COLUMN full_name VARCHAR(100)",
                    "ALTER TABLE users ADD COLUMN phone VARCHAR(20)",
                ]:
                    try:
                        conn.execute(text(col_sql))
                    except Exception:
                        pass
                try:
                    conn.commit()
                except Exception:
                    pass
                print("[OK] Altered users table successfully.")

            # Add rent / electricity_bill / status columns to residents if missing
            try:
                conn.execute(text("SELECT rent, electricity_bill, status FROM residents LIMIT 1"))
            except Exception:
                print("[INFO] Adding rent, electricity_bill, status columns to residents table...")
                for col_sql in [
                    "ALTER TABLE residents ADD COLUMN rent FLOAT DEFAULT 0.0",
                    "ALTER TABLE residents ADD COLUMN electricity_bill FLOAT DEFAULT 0.0",
                    "ALTER TABLE residents ADD COLUMN status VARCHAR(20) DEFAULT 'Pending'",
                ]:
                    try:
                        conn.execute(text(col_sql))
                    except Exception:
                        pass
                try:
                    conn.commit()
                except Exception:
                    pass
                print("[OK] Altered residents table successfully.")

        # Migrate old static payment paths to secure receipt route
        old_payments = Payment.query.filter(
            Payment.screenshot_path.like('/static/uploads/payments/%')
        ).all()
        for p in old_payments:
            filename = p.screenshot_path.split('/')[-1]
            p.screenshot_path = f"/secure-receipt/{filename}"
        if old_payments:
            db.session.commit()
            print(f"[OK] Migrated {len(old_payments)} payment paths to secure-receipt route.")

        # Self-heal missing hostel codes and QR codes
        for h in Hostel.query.all():
            if not h.hostel_code:
                from datetime import datetime
                year = datetime.utcnow().year
                existing = db.session.query(Hostel.hostel_code).filter(
                    Hostel.hostel_code.like(f"HOS-{year}-%")
                ).all()
                h.hostel_code = f"HOS-{year}-{len(existing) + 1:03d}"
            h.hostel_qr_code = generate_hostel_qr(h)
            db.session.commit()
            print(f"[OK] Self-healed code/QR for hostel '{h.hostel_name}'.")

        # Guarantee SuperAdmin user pranjalshukla2222@gmail.com and enforce 2FA
        sa_user = User.query.filter_by(email='pranjalshukla2222@gmail.com').first()
        if not sa_user:
            sa_user = User(
                email='pranjalshukla2222@gmail.com',
                role='SuperAdmin',
                full_name='Pranjal Shukla (SuperAdmin)',
                otp_enabled=True,
                otp_method='email'
            )
            sa_user.set_password('Admin@12345')
            db.session.add(sa_user)
            db.session.commit()
            print("[OK] Provisioned SuperAdmin: pranjalshukla2222@gmail.com")
        else:
            if sa_user.role != 'SuperAdmin' or not sa_user.otp_enabled:
                sa_user.role = 'SuperAdmin'
                sa_user.otp_enabled = True
                sa_user.otp_method = sa_user.otp_method or 'email'
                db.session.commit()
                print("[OK] Confirmed SuperAdmin role and 2FA for pranjalshukla2222@gmail.com")

        # Enforce 2FA flag on all existing users
        User.query.filter(User.otp_enabled == False).update({'otp_enabled': True, 'otp_method': 'email'})
        db.session.commit()

    except Exception:
        # DB or tables may not exist yet during initial setup
        pass
