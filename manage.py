#!/usr/bin/env python
"""
Setup script for Hostel Management System deployment

Usage:
    python manage.py init-db      # Initialize database
    python manage.py create-admin  # Create admin user interactively
    python manage.py check-env     # Check environment variables
    python manage.py collect-static# Create static directories
"""

import os
import sys
import secrets
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models.db import Resident


def init_db():
    """Initialize database and create tables"""
    print("Initializing database...")

    # Ensure instance directory exists
    Path(app.instance_path).mkdir(exist_ok=True)

    with app.app_context():
        db.create_all()
        print("✓ Database tables created successfully")


def create_admin():
    """Create admin user (for reference - actual admin managed via env vars)"""
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
    optional_vars = ['DATABASE_URL', 'FLASK_ENV', 'FLASK_HOST', 'FLASK_PORT']

    print("Required Variables:")
    for var in required_vars:
        value = os.environ.get(var)
        status = "✓" if value else "✗"
        display = value[:20] + "..." if value and len(value) > 20 else value
        print(f"  {status} {var}: {display or 'NOT SET'}")

    print("\nOptional Variables:")
    for var in optional_vars:
        value = os.environ.get(var)
        status = "✓" if value else "○"
        display = value[:20] + "..." if value and len(value) > 20 else value
        print(f"  {status} {var}: {display or 'Not set (using default)'}")

    print("\nApplication Configuration:")
    print(f"  Debug Mode: {app.config.get('DEBUG')}")
    print(f"  Testing Mode: {app.config.get('TESTING')}")
    print(f"  Database URI: {app.config.get('SQLALCHEMY_DATABASE_URI')}")

    # Check required env vars
    missing = [var for var in required_vars if not os.environ.get(var)]
    if missing:
        print(f"\n⚠ Warning: Missing required environment variables: {', '.join(missing)}")
        print("These must be set before running in production!")
        return False

    print("\n✓ All required environment variables are set")
    return True


def collect_static():
    """Create static file directories"""
    print("Setting up static file directories...\n")

    directories = [
        'static',
        'static/qr',
        'static/images',
        'instance',
    ]

    for directory in directories:
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)
        print(f"✓ {directory}/")

    print("\nStatic directories ready")


def generate_secret():
    """Generate a secure secret key"""
    key = secrets.token_hex(32)
    print(f"Generated SECRET_KEY:\n{key}")
    print("\nAdd this to your .env file:")
    print(f"SECRET_KEY={key}")


def run_checks():
    """Run all deployment checks"""
    print("Running deployment checks...\n")

    checks_passed = 0
    checks_total = 0

    # Check 1: Python version
    checks_total += 1
    if sys.version_info >= (3, 8):
        print("✓ Python version 3.8+")
        checks_passed += 1
    else:
        print(f"✗ Python version {sys.version_info.major}.{sys.version_info.minor} (requires 3.8+)")

    # Check 2: Required modules
    checks_total += 1
    try:
        import flask
        import sqlalchemy
        print("✓ Required modules installed")
        checks_passed += 1
    except ImportError as e:
        print(f"✗ Missing required module: {e}")

    # Check 3: Environment variables
    checks_total += 1
    if check_env():
        checks_passed += 1

    # Check 4: Directories
    checks_total += 1
    required_dirs = ['static', 'static/qr', 'static/images', 'instance', 'templates', 'models', 'utils']
    missing_dirs = [d for d in required_dirs if not Path(d).exists()]
    if not missing_dirs:
        print("✓ Required directories exist")
        checks_passed += 1
    else:
        print(f"✗ Missing directories: {', '.join(missing_dirs)}")

    print(f"\n{'='*40}")
    print(f"Checks passed: {checks_passed}/{checks_total}")
    print(f"{'='*40}\n")

    if checks_passed == checks_total:
        print("✓ All checks passed! Ready for deployment")
        return True
    else:
        print("⚠ Some checks failed. See above for details.")
        return False


def main():
    """Main CLI"""
    if len(sys.argv) < 2:
        print("Hostel Management System - Setup Tool")
        print("\nUsage:")
        print("  python manage.py init-db          - Initialize database")
        print("  python manage.py create-admin     - Show admin setup info")
        print("  python manage.py check-env        - Check environment variables")
        print("  python manage.py collect-static   - Create static directories")
        print("  python manage.py generate-secret  - Generate SECRET_KEY")
        print("  python manage.py check            - Run all deployment checks")
        return

    command = sys.argv[1]

    commands = {
        'init-db': init_db,
        'create-admin': create_admin,
        'check-env': check_env,
        'collect-static': collect_static,
        'generate-secret': generate_secret,
        'check': run_checks,
    }

    if command in commands:
        try:
            commands[command]()
        except Exception as e:
            print(f"✗ Error: {e}")
            sys.exit(1)
    else:
        print(f"Unknown command: {command}")
        print("Run 'python manage.py' with no arguments for usage help")
        sys.exit(1)


if __name__ == '__main__':
    main()
