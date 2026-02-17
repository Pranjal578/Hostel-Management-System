# Quick Start Guide

Get your Hostel Management System up and running in 5 minutes!

## Option 1: Automatic Setup (Recommended)

### For Linux/Mac

```bash
chmod +x setup.sh
./setup.sh
```

### For Windows

```cmd
setup.bat
```

The script will:

- Check Python installation
- Install all dependencies
- Create necessary directories
- Initialize the database
- Set up everything automatically

## Option 2: Manual Setup

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Create Directories

```bash
mkdir -p static/images static/qr
```

### Step 3: Run the Application

```bash
python app.py
```

### Step 4: Access the System

Open your browser and navigate to:

```link
http://localhost:5000
```

## Default Login Credentials

### Admin Access

- **Username:** `admin`
- **Password:** `admin123`

**IMPORTANT:** Change these credentials in production!

## First Steps

### 1. Test the System

1. Visit <http://localhost:5000>
2. Click "Register Now"
3. Fill in the registration form
4. Login with your new account

### 2. Access Admin Panel

1. Click "Admin Login"
2. Use the default credentials
3. View all residents
4. Test edit and delete functions

### 3. Test QR Code Feature

1. Login as a resident
2. View your profile
3. Download your QR code
4. Scan it with your phone to test

## Project Structure

```structure
hostel_management_system/
├── app.py              ← Main application (START HERE)
├── config.py           ← Configuration settings
├── requirements.txt    ← Dependencies
├── models/             ← Database models
├── utils/              ← Helper functions
├── static/             ← CSS, JS, Images, QR codes
└── templates/          ← HTML templates
```

## Common Issues

### Port 5000 already in use

```bash
# Use a different port
python app.py --port 5001
```

### Dependencies won't install

```bash
# Try with --break-system-packages flag
pip install -r requirements.txt --break-system-packages
```

### Database not created

```python
# Run in Python console
from app import app, db
with app.app_context():
    db.create_all()
```

## Next Steps

1. Customize the color scheme in `static/css/style.css`
2. Change admin credentials in `config.py`
3. Add your logo/images
4. Test all features
5. Deploy to production

## Need Help?

- Read the full [README.md](README.md)
- Check the Troubleshooting section
- Create an issue on GitHub

---

**Happy Managing!**
