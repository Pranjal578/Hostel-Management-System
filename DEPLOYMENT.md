# Deployment Guide - Hostel Management System

This guide covers deploying the Hostel Management System to a production environment.

## Prerequisites

- Python 3.8 or higher
- pip package manager
- A production-grade database (PostgreSQL, MySQL) or use SQLite for small deployments
- A reverse proxy like Nginx or Apache
- Systemd or a process manager (supervisor, systemd)

## Pre-Deployment Checklist

- [ ] Security credentials are strong and unique
- [ ] Database is configured and tested
- [ ] Static files are collected
- [ ] Environment variables are set
- [ ] SSL/TLS certificates are obtained (Let's Encrypt recommended)
- [ ] Database backups are configured
- [ ] Logging is configured

## 1. Prepare Environment

### 1.1 Clone Repository

```bash
git clone <repository-url>
cd hostel_management_system
```

### 1.2 Create Virtual Environment

```bash
python -m venv venv

# On Linux/macOS
source venv/bin/activate

# On Windows
venv\Scripts\activate
```

### 1.3 Install Dependencies

```bash
pip install -r requirements.txt
```

## 2. Configure Environment Variables

### 2.1 Create .env File

Copy the example file and update it with production values:

```bash
cp .env.example .env
```

### 2.2 Set Required Variables

Edit `.env` and set:

```env
FLASK_ENV=production
SECRET_KEY=<generate-strong-random-key>
ADMIN_USERNAME=<secure-admin-username>
ADMIN_PASSWORD=<secure-admin-password>
DATABASE_URL=<your-database-url>
SESSION_COOKIE_SECURE=True
```

### 2.3 Generate Secret Key

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Copy the output and set as `SECRET_KEY` in `.env`.

## 3. Database Setup

### Option A: SQLite (Small Deployments)

```bash
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

### Option B: PostgreSQL (Recommended)

1. Create database:

   ```bash
   createdb hostel_management
   ```

2. Update `DATABASE_URL` in `.env`:

   ```env
   DATABASE_URL=postgresql://username:password@localhost/hostel_management
   ```

3. Install driver:

   ```bash
   pip install psycopg2-binary
   ```

4. Initialize database:

   ```bash
   python -c "from app import app, db; app.app_context().push(); db.create_all()"
   ```

### Option C: MySQL

1. Create database:

   ```bash
   mysql -u root -p -e "CREATE DATABASE hostel_management;"
   ```

2. Update `DATABASE_URL` in `.env`:

   ```env
   DATABASE_URL=mysql://username:password@localhost/hostel_management
   ```

3. Install driver:

   ```bash
   pip install mysql-connector-python
   ```

4. Initialize database:

   ```bash
   python -c "from app import app, db; app.app_context().push(); db.create_all()"
   ```

## 4. Create Required Directories

```bash
mkdir -p instance
mkdir -p static/qr
mkdir -p static/images
chmod 755 static/qr
chmod 755 static/images
```

## 5. Run with Gunicorn

### 5.1 Test Gunicorn Server

```bash
gunicorn --workers 4 --bind 127.0.0.1:5000 wsgi:app
```

### 5.2 Create Systemd Service File

Create `/etc/systemd/system/hostel-mgmt.service`:

```ini
[Unit]
Description=Hostel Management System
After=network.target

[Service]
Type=notify
User=www-data
WorkingDirectory=/path/to/hostel_management_system
Environment="PATH=/path/to/hostel_management_system/venv/bin"
EnvironmentFile=/path/to/hostel_management_system/.env
ExecStart=/path/to/hostel_management_system/venv/bin/gunicorn \
    --workers 4 \
    --worker-class sync \
    --bind unix:/run/hostel-mgmt.sock \
    --access-logfile /var/log/hostel-mgmt/access.log \
    --error-logfile /var/log/hostel-mgmt/error.log \
    wsgi:app

[Install]
WantedBy=multi-user.target
```

### 5.3 Enable and Start Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable hostel-mgmt
sudo systemctl start hostel-mgmt
sudo systemctl status hostel-mgmt
```

## 6. Configure Nginx

Create `/etc/nginx/sites-available/hostel-mgmt`:

```nginx
server {
    listen 80;
    server_name example.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name example.com;

    # SSL certificates
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;

    # Log files
    access_log /var/log/nginx/hostel-mgmt-access.log;
    error_log /var/log/nginx/hostel-mgmt-error.log;

    # Max upload size
    client_max_body_size 16M;

    location / {
        proxy_pass http://unix:/run/hostel-mgmt.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /path/to/hostel_management_system/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

Enable and reload Nginx:

```bash
sudo ln -s /etc/nginx/sites-available/hostel-mgmt /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 7. SSL/TLS Setup (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot certonly --standalone -d example.com
```

Update Nginx configuration with certificate paths.

## 8. Monitoring and Logging

### Create Log Directory

```bash
sudo mkdir -p /var/log/hostel-mgmt
sudo chown www-data:www-data /var/log/hostel-mgmt
```

### Check Logs

```bash
# Application logs
sudo tail -f /var/log/hostel-mgmt/error.log
sudo tail -f /var/log/hostel-mgmt/access.log

# Nginx logs
sudo tail -f /var/log/nginx/hostel-mgmt-error.log
```

## 9. Security Hardening

### 9.1 System Updates

```bash
sudo apt update && sudo apt upgrade
```

### 9.2 Firewall Rules

```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 9.3 Database Backups

Set up automated backups:

```bash
# For PostgreSQL
pg_dump hostel_management > backup_$(date +%Y%m%d_%H%M%S).sql

# For MySQL
mysqldump -u username -p hostel_management > backup_$(date +%Y%m%d_%H%M%S).sql
```

### 9.4 Regular Updates

- Keep dependencies updated: `pip install --upgrade -r requirements.txt`
- Monitor security advisories
- Apply OS patches regularly

## 10. Troubleshooting

### Application Won't Start

```bash
# Check syntax errors
python -m py_compile app.py config.py

# Test configuration loading
python -c "from config import ProductionConfig; print(ProductionConfig.DEBUG)"

# Check systemd journal
sudo journalctl -u hostel-mgmt -n 50 --no-pager
```

### Database Connection Issues

```bash
# Test connection string
python -c "from sqlalchemy import create_engine; create_engine(os.environ.get('DATABASE_URL')).connect()"
```

### Permission Errors

Ensure `/var/log/hostel-mgmt` and socket directory have correct permissions:

```bash
sudo chown -R www-data:www-data /var/log/hostel-mgmt
sudo chown -R www-data:www-data /run/hostel-mgmt.sock (if using socket)
```

## 11. Performance Optimization

### Gunicorn Workers

Recommended: `(2 × CPU cores) + 1`

```bash
# For 4-core system: 9 workers
gunicorn --workers 9 wsgi:app
```

### Database Connection Pooling

Update config.py if using PostgreSQL:

```python
SQLALCHEMY_ENGINE_OPTIONS = {
    "pool_size": 10,
    "pool_recycle": 3600,
    "pool_pre_ping": True,
}
```

## 12. Verification Checklist

After deployment:

- [ ] Application loads without errors
- [ ] Admin login works with new credentials
- [ ] Resident registration and login work
- [ ] QR code generation works
- [ ] Static files load properly (CSS, images)
- [ ] SSL certificate is valid and not expired
- [ ] Database backups are working
- [ ] Logs are being generated
- [ ] Monitoring is configured
- [ ] Recovery procedures are documented

## Support

For issues or questions, refer to the main README.md or check system logs:

```bash
sudo journalctl -u hostel-mgmt -f
```
