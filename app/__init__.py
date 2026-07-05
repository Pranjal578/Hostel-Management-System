import os
from flask import Flask, redirect, url_for, session, render_template
from app.models.db import db, User
from app.utils.email_sender import init_mail
from config import DevelopmentConfig, ProductionConfig
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from authlib.integrations.flask_client import OAuth
from flask_migrate import Migrate

# Global Extensions
csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address, default_limits=["200 per day", "50 per hour"])
oauth = OAuth()
migrate = Migrate()

def create_app(config_name=None):
    """Application Factory to create and configure the Flask app"""
    app = Flask(__name__)
    
    # Load configuration
    env = os.environ.get('FLASK_ENV', 'development')
    if config_name == 'production' or env == 'production':
        app.config.from_object(ProductionConfig)
    else:
        app.config.from_object(DevelopmentConfig)
        
    # Ensure instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Initialize extensions
    db.init_app(app)
    init_mail(app)
    csrf.init_app(app)
    limiter.init_app(app)
    oauth.init_app(app)
    migrate.init_app(app, db)
    
    # Register Google OAuth client
    oauth.register(
        name='google',
        client_id=app.config.get('GOOGLE_CLIENT_ID') or 'placeholder-id',
        client_secret=app.config.get('GOOGLE_CLIENT_SECRET') or 'placeholder-secret',
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email profile'}
    )
    
    # Register Blueprints
    from app.routes.auth import auth_bp
    from app.routes.admin import admin_bp
    from app.routes.owner import owner_bp
    from app.routes.resident import resident_bp
    from app.routes.settings import settings_bp
    from app.routes.api import api_bp
    
    app.register_blueprint(auth_bp, url_prefix='/')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(owner_bp, url_prefix='/owner')
    app.register_blueprint(resident_bp, url_prefix='/resident')
    app.register_blueprint(settings_bp, url_prefix='/settings')
    app.register_blueprint(api_bp, url_prefix='/api')

    # Migrate old static payment paths to secure path in db
    with app.app_context():
        # Run auto-upgrades for database migrations on start
        if not app.config.get('TESTING'):
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

        try:
            from app.models.db import Payment, Hostel
            from app.utils.qr_generator import generate_hostel_qr
            
            old_payments = Payment.query.filter(Payment.screenshot_path.like('/static/uploads/payments/%')).all()
            for p in old_payments:
                filename = p.screenshot_path.split('/')[-1]
                p.screenshot_path = f"/secure-receipt/{filename}"
            if old_payments:
                db.session.commit()
                print(f"[OK] Migrated {len(old_payments)} payment paths to secure-receipt route.")

            # Self-healing missing Hostel Codes & QR Codes
            hostels = Hostel.query.all()
            for h in hostels:
                modified = False
                if not h.hostel_code:
                    from datetime import datetime
                    year = datetime.utcnow().year
                    existing_codes = db.session.query(Hostel.hostel_code).filter(Hostel.hostel_code.like(f"HOS-{year}-%")).all()
                    seq = len(existing_codes) + 1
                    h.hostel_code = f"HOS-{year}-{seq:03d}"
                    modified = True
                if not h.hostel_qr_code or not os.path.exists(os.path.join(app.root_path, h.hostel_qr_code.lstrip('/'))):
                    h.hostel_qr_code = generate_hostel_qr(h)
                    modified = True
                if modified:
                    db.session.commit()
                    print(f"[OK] Self-healed code/QR for hostel '{h.hostel_name}'.")
        except Exception as e:
            # Database or table might not exist yet during initialization/checks
            pass
    
    # Session validity check (password version change invalidates other active sessions)
    @app.before_request
    def check_session_validity():
        if 'user_id' in session:
            user = User.query.get(session['user_id'])
            if not user or session.get('password_version') != user.password_version:
                session.clear()
                # Clear session, which forces login redirect on the next check/decorator
                
    # Default landing route
    @app.route('/')
    def index():
        return render_template('index.html')

    # Security Headers Middleware
    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        # CSP: Allowing local script assets, inline styling, Google Fonts, and html5-qrcode CDN
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://unpkg.com https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: blob:; "
            "connect-src 'self';"
        )
        return response

    return app
