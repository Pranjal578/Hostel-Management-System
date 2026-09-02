#!/usr/bin/env python
"""
Setup and management script for Multi-Tenant Hostel SaaS Platform
Usage:
    python manage.py init-db          # Initialize database
    python manage.py create-admin     # Show admin setup info
    python manage.py check-env        # Check environment variables
    python manage.py collect-static   # Create static directories
    python manage.py check            # Run deployment verification checks
    python manage.py generate-secret  # Generate secure SECRET_KEY
    python manage.py backup           # Create a timestamped database backup
    python manage.py backup --keep N  # Backup and keep only last N backups (default 7)
    python manage.py test-email [to]  # Test live SMTP email delivery to specified recipient
"""

import os
import sys
import secrets
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models.db import db, User, Hostel, Resident

# Instantiate app for CLI commands
app = create_app()


def init_db():
    """Initialize database and create tables using migrations"""
    print("Initializing database...")

    # Ensure instance directory exists
    Path(app.instance_path).mkdir(exist_ok=True)

    with app.app_context():
        try:
            from flask_migrate import upgrade as db_upgrade
            db_upgrade()
            print("[OK] Database tables created/upgraded via migrations successfully")
        except Exception as e:
            print(f"[WARN] Migrations upgrade failed: {e}. Falling back to create_all().")
            db.create_all()
            print("[OK] Database tables created via fallback successfully")


def create_admin():
    """Create admin credentials helper details"""
    print("Note: Admin credentials are managed via environment variables.")
    print(f"Current admin username: {app.config.get('ADMIN_USERNAME')}")
    print("\nTo change admin credentials, update:")
    print("  - ADMIN_USERNAME environment variable")
    print("  - ADMIN_PASSWORD environment variable")
    print("\nExample:")
    print("  export ADMIN_USERNAME=admin")
    print("  export ADMIN_PASSWORD=your-secure-password")


def check_env():
    """Check environment variables"""
    print("Checking environment configuration...\n")

    required_vars = ['SECRET_KEY', 'ADMIN_USERNAME', 'ADMIN_PASSWORD']
    optional_vars = [
        'DATABASE_URL', 'FLASK_ENV', 'FLASK_HOST', 'FLASK_PORT', 'ENCRYPTION_KEY',
        'MAIL_SERVER', 'MAIL_PORT', 'MAIL_USERNAME', 'SENDER_EMAIL'
    ]

    print("Required Variables:")
    for var in required_vars:
        value = os.environ.get(var)
        status = "[OK]" if value else "[MISSING]"
        display = value[:20] + "..." if value and len(value) > 20 else value
        print(f"  {status} {var}: {display or 'NOT SET'}")

    print("\nOptional Variables:")
    for var in optional_vars:
        value = os.environ.get(var)
        status = "[SET]" if value else "[DEFAULT]"
        display = value[:20] + "..." if value and len(value) > 20 else value
        print(f"  {status} {var}: {display or 'Not set (using default)'}")

    print("\nApplication Configuration:")
    print(f"  Debug Mode: {app.config.get('DEBUG')}")
    print(f"  Testing Mode: {app.config.get('TESTING')}")
    print(f"  Database URI: {app.config.get('SQLALCHEMY_DATABASE_URI')}")

    # Check required env vars
    missing = [var for var in required_vars if not os.environ.get(var)]
    if missing:
        print(f"\n[WARN] Warning: Missing required environment variables: {', '.join(missing)}")
        print("These must be set before running in production!")
        return False

    print("\n[OK] All required environment variables are set")
    return True


def collect_static():
    """Create static file and upload directories"""
    print("Setting up static file directories...\n")

    # Define directories inside app package
    directories = [
        'app/static',
        'app/static/qr',
        'app/static/images',
        'app/static/uploads',
        'app/static/uploads/payments',
        'app/static/uploads/payment_qrs',
        'instance',
    ]

    for directory in directories:
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)
        print(f"[OK] {directory}/")

    print("\nStatic directories ready")


def generate_secret():
    """Generate a secure secret key"""
    key = secrets.token_hex(32)
    print(f"Generated SECRET_KEY:\n{key}")
    print("\nAdd this to your .env file:")
    print(f"SECRET_KEY={key}")


def test_email():
    """Test real SMTP email delivery using configured settings"""
    recipient = sys.argv[2] if len(sys.argv) > 2 else (app.config.get('MAIL_USERNAME') or app.config.get('SENDER_EMAIL'))
    if not recipient:
        print("[ERROR] Please provide a recipient email: python manage.py test-email user@example.com")
        return
    print(f"Testing real SMTP connection to {app.config.get('MAIL_SERVER')}:{app.config.get('MAIL_PORT')}...")
    print(f"Target recipient: {recipient}")
    from app.utils.email_sender import send_test_email
    with app.app_context():
        success, msg = send_test_email(recipient)
        if success:
            print(f"[OK] {msg}")
        else:
            print(f"[FAILED] {msg}")


def backup(keep: int = 7):
    """
    Create a timestamped database backup.

    For SQLite: copies the .db file to backups/<timestamp>.db
    For PostgreSQL: runs pg_dump and saves to backups/<timestamp>.sql

    Args:
        keep: Number of most-recent backups to retain (older ones are deleted).
    """
    import shutil
    import subprocess
    import glob
    from datetime import datetime
    from urllib.parse import urlparse

    backup_dir = Path('backups')
    backup_dir.mkdir(exist_ok=True)
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')

    db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')

    if db_uri.startswith('sqlite'):
        # Resolve the .db file path from the URI
        db_path_str = db_uri.replace('sqlite:///', '').replace('sqlite://', '')
        if not db_path_str:
            db_path_str = str(Path(app.instance_path) / 'database.db')

        db_path = Path(db_path_str)
        if not db_path.exists():
            # Also try instance path
            db_path = Path(app.instance_path) / 'database.db'

        if not db_path.exists():
            print(f"[ERROR] SQLite database file not found at: {db_path}")
            sys.exit(1)

        dest = backup_dir / f"{timestamp}.db"
        shutil.copy2(str(db_path), str(dest))
        print(f"[OK] SQLite backup created: {dest} ({dest.stat().st_size / 1024:.1f} KB)")

    elif db_uri.startswith('postgresql') or db_uri.startswith('postgres'):
        parsed = urlparse(db_uri)
        dest = backup_dir / f"{timestamp}.sql"

        env = os.environ.copy()
        if parsed.password:
            env['PGPASSWORD'] = parsed.password

        cmd = [
            'pg_dump',
            '-h', parsed.hostname or 'localhost',
            '-p', str(parsed.port or 5432),
            '-U', parsed.username or 'postgres',
            '-d', parsed.path.lstrip('/'),
            '-F', 'p',      # plain SQL format
            '--no-owner',
            '--no-acl',
        ]
        print(f"[INFO] Running: {' '.join(cmd)}")
        with open(str(dest), 'w') as f:
            result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, env=env)

        if result.returncode != 0:
            print(f"[ERROR] pg_dump failed: {result.stderr.decode()}")
            sys.exit(1)

        size_kb = dest.stat().st_size / 1024
        print(f"[OK] PostgreSQL backup created: {dest} ({size_kb:.1f} KB)")

    else:
        print(f"[ERROR] Unsupported database URI scheme: {db_uri[:30]}...")
        sys.exit(1)

    # ── Rotation: delete oldest backups beyond `keep` ──────────
    all_backups = sorted(
        list(backup_dir.glob('*.db')) + list(backup_dir.glob('*.sql')),
        key=lambda p: p.stat().st_mtime
    )
    if len(all_backups) > keep:
        to_delete = all_backups[:len(all_backups) - keep]
        for old in to_delete:
            old.unlink()
            print(f"[ROTATE] Deleted old backup: {old.name}")

    print(f"[OK] Backup rotation complete. Keeping last {keep} backups.")


def run_checks():
    """Run all deployment verification checks"""
    print("Running system deployment checks...\n")

    checks_passed = 0
    checks_total = 0

    # Check 1: Python version
    checks_total += 1
    if sys.version_info >= (3, 8):
        print("[OK] Python version 3.8+")
        checks_passed += 1
    else:
        print(f"[ERROR] Python version {sys.version_info.major}.{sys.version_info.minor} (requires 3.8+)")

    # Check 2: Required modules
    checks_total += 1
    try:
        import flask
        import sqlalchemy
        import cryptography
        import PIL
        import qrcode
        import twilio
        print("[OK] All required modules and libraries installed")
        checks_passed += 1
    except ImportError as e:
        print(f"[ERROR] Missing required module: {e}")

    # Check 3: Environment variables
    checks_total += 1
    if check_env():
        checks_passed += 1

    # Check 4: Directories
    checks_total += 1
    required_dirs = [
        'app/static',
        'app/static/qr',
        'app/static/images',
        'app/static/uploads/payments',
        'app/static/uploads/payment_qrs',
        'instance',
        'app/templates',
        'app/models',
        'app/routes',
        'app/utils'
    ]
    missing_dirs = [d for d in required_dirs if not Path(d).exists()]
    if not missing_dirs:
        print("[OK] Required directories exist")
        checks_passed += 1
    else:
        print(f"[ERROR] Missing directories: {', '.join(missing_dirs)}")

    print(f"\n{'='*40}")
    print(f"Checks passed: {checks_passed}/{checks_total}")
    print(f"{'='*40}\n")

    if checks_passed == checks_total:
        print("[OK] All checks passed! Ready for SaaS platform operation.")
        return True
    else:
        print("[WARN] Some checks failed. See details above.")
        return False


def main():
    """Main CLI entrypoint"""
    if len(sys.argv) < 2:
        print("Hostel SaaS Platform - Setup Tool")
        print("\nUsage:")
        print("  python manage.py init-db          - Initialize database")
        print("  python manage.py create-admin     - Show admin setup info")
        print("  python manage.py check-env        - Check environment variables")
        print("  python manage.py collect-static   - Create static directories")
        print("  python manage.py generate-secret  - Generate SECRET_KEY")
        print("  python manage.py check            - Run all checks")
        print("  python manage.py backup           - Backup database (SQLite or PostgreSQL)")
        print("  python manage.py backup --keep N  - Backup & keep only last N backups")
        print("  python manage.py test-email [to]  - Test live SMTP email delivery")
        return

    command = sys.argv[1]

    commands = {
        'init-db': init_db,
        'create-admin': create_admin,
        'check-env': check_env,
        'collect-static': collect_static,
        'generate-secret': generate_secret,
        'check': run_checks,
        'backup': lambda: backup(
            keep=int(sys.argv[sys.argv.index('--keep') + 1])
            if '--keep' in sys.argv else 7
        ),
        'test-email': test_email,
        'test-mail': test_email,
    }

    if command in commands:
        try:
            commands[command]()
        except Exception as e:
            print(f"[ERROR] Error: {e}")
            sys.exit(1)
    else:
        print(f"Unknown command: {command}")
        print("Run 'python manage.py' with no arguments for usage help")
        sys.exit(1)


if __name__ == '__main__':
    main()
