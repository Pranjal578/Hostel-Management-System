import os
from flask import Flask, redirect, url_for, session
from app.models.db import db, User
from app.utils.email_sender import init_mail
from config import DevelopmentConfig, ProductionConfig
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from authlib.integrations.flask_client import OAuth

# Global Extensions
csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address, default_limits=["200 per day", "50 per hour"])
oauth = OAuth()

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
        try:
            from app.models.db import Payment
            old_payments = Payment.query.filter(Payment.screenshot_path.like('/static/uploads/payments/%')).all()
            for p in old_payments:
                filename = p.screenshot_path.split('/')[-1]
                p.screenshot_path = f"/secure-receipt/{filename}"
            if old_payments:
                db.session.commit()
                print(f"[OK] Migrated {len(old_payments)} payment paths to secure-receipt route.")
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
        if 'user_id' in session:
            # Re-route logged in user to their dashboard
            user = User.query.get(session['user_id'])
            if user:
                if user.role == 'SuperAdmin':
                    return redirect(url_for('admin.dashboard'))
                elif user.role == 'HostelOwner':
                    return redirect(url_for('owner.dashboard'))
                elif user.role == 'Resident':
                    return redirect(url_for('resident.dashboard'))
        return redirect(url_for('auth.login'))

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
