"""
WSGI entry point for production servers (Gunicorn, uWSGI, etc.)

Usage with Gunicorn:
    gunicorn --workers 4 --bind 0.0.0.0:5000 wsgi:app

Set environment variables before running:
    export FLASK_ENV=production
    export SECRET_KEY=<your-secret-key>
    export ADMIN_USERNAME=<your-admin-username>
    export ADMIN_PASSWORD=<your-admin-password>
    export DATABASE_URL=<your-database-url>
"""

import os
from app import app, db

if __name__ == "__main__":
    # Ensure instance folder exists
    os.makedirs(app.instance_path, exist_ok=True)

    # Create tables if they don't exist
    with app.app_context():
        db.create_all()

    app.run()
