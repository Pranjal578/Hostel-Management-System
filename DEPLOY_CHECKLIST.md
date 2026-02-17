# Quick Deployment Checklist

Follow this checklist to deploy the Hostel Management System to production:

## 1. Pre-Deployment (5-10 minutes)

- [ ] **Environment Setup**

  ```bash
  # Copy example environment file
  cp .env.example .env

  # Edit .env with production values
  nano .env
  ```

- [ ] **Generate Secret Key**

  ```bash
  python manage.py generate-secret
  # Copy output and add to .env as SECRET_KEY
  ```

- [ ] **Set Admin Credentials**
  - Edit `.env` and set strong values for:
    - `ADMIN_USERNAME` (not just "admin")
    - `ADMIN_PASSWORD` (strong, unique password)

- [ ] **Set Database URL**
  - For SQLite: `DATABASE_URL=sqlite:///instance/database.db` (default)
  - For PostgreSQL: `DATABASE_URL=postgresql://user:password@localhost/dbname`
  - For MySQL: `DATABASE_URL=mysql://user:password@localhost/dbname`

## 2. System Preparation (10-20 minutes)

```bash
# Load environment variables
export $(cat .env | xargs)

# Install dependencies
pip install -r requirements.txt

# Run deployment checks
python manage.py check

# Initialize database
python manage.py init-db

# Create static directories
python manage.py collect-static
```

## 3. Local Testing (5 minutes)

```bash
# Test with Gunicorn
export FLASK_ENV=production
gunicorn --workers 4 --bind 127.0.0.1:5000 wsgi:app

# Visit http://127.0.0.1:5000 and verify:
# - [ ] Home page loads
# - [ ] Admin login works with new credentials
# - [ ] QR code generation works
# - [ ] Static files load (CSS, images)
```

## 4. Production Deployment

### Option A: Linux Systemd (Recommended)

```bash
# 1. Create service file (must run as root)
sudo nano /etc/systemd/system/hostel-mgmt.service
# Paste content from DEPLOYMENT.md

# 2. Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable hostel-mgmt
sudo systemctl start hostel-mgmt

# 3. Configure Nginx (see DEPLOYMENT.md)

# 4. Setup SSL with Let's Encrypt
sudo certbot certonly --standalone -d yourdomain.com
```

### Option B: Docker (Alternative)

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create required directories
RUN mkdir -p instance static/qr static/images

ENV FLASK_ENV=production
EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "wsgi:app"]
```

Build and run:

```bash
docker build -t hostel-mgmt .
docker run -p 5000:5000 --env-file .env hostel-mgmt
```

## 5. Post-Deployment Verification

```bash
# Check application is running
curl http://your-server/

# Check logs
sudo tail -f /var/log/hostel-mgmt/error.log

# Verify database
python -c "from app import db; print('Database connected!' if db.engine else 'Database error!')"

# Verify SSL (if applicable)
curl -I https://your-domain/
```

## 6. Monitoring & Maintenance

### Daily

- [ ] Check error logs for issues
- [ ] Monitor disk space

### Weekly

- [ ] Verify database integrity
- [ ] Check for dependency updates
- [ ] Review access logs

### Monthly

- [ ] Update system packages: `sudo apt update && sudo apt upgrade`
- [ ] Update Python dependencies: `pip install --upgrade -r requirements.txt`
- [ ] Test database backups

## Security Checklist

Before going live:

- [ ] **Changed default admin credentials** (not "admin"/"admin123")
- [ ] **Generated strong SECRET_KEY** (use `manage.py generate-secret`)
- [ ] **Database password is strong**
- [ ] **Firewall is configured** (allow only 80/443)
- [ ] **SSL/TLS certificate is valid** (not self-signed)
- [ ] **.env file is in .gitignore** (no secrets in git)
- [ ] **Database is backed up** (before first deployment)
- [ ] **Session cookies are secure** (SESSION_COOKIE_SECURE=True)
- [ ] **Debug mode is disabled** (FLASK_ENV=production)
- [ ] **Regular backups are configured**

## Troubleshooting

### Application won't start

```bash
# Check environment
python manage.py check-env

# Check for syntax errors
python -m py_compile app.py config.py

# Check logs
sudo journalctl -u hostel-mgmt -n 50
```

### Database connection fails

```bash
# Verify DATABASE_URL
echo $DATABASE_URL

# Test connection
python -c "from sqlalchemy import create_engine; print('Connected!' if create_engine('$DATABASE_URL').connect() else 'Failed')"
```

### Static files not loading

```bash
# Ensure directories exist
python manage.py collect-static

# Check Nginx configuration
sudo nginx -t
```

## Rollback Procedure

If deployment fails:

```bash
# Stop application
sudo systemctl stop hostel-mgmt

# Restore previous .env
git checkout .env

# Restart with previous config
sudo systemctl start hostel-mgmt
```

## Additional Resources

- **Full deployment guide**: See `DEPLOYMENT.md`
- **Project overview**: See `PROJECT_OVERVIEW.md`
- **Quick start**: See `QUICKSTART.md`
- **README**: See `README.md`

---

**Estimated time to full deployment**: 30-60 minutes (excluding SSL certificate setup)

**Support**: Check error logs at `/var/log/hostel-mgmt/` or run `python manage.py check` for diagnostics
