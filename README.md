# 🏠 Hostel Resident Management System

A modern, professional web-based hostel management system with QR code-based resident profiles. Built with Flask, SQLite, and responsive design.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Flask](https://img.shields.io/badge/Flask-3.0.0-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## ✨ Features

### For Residents
- ✅ **One-time Registration** - Register once with comprehensive details
- 🔐 **Secure Login** - Password-protected access to personal profile
- ✏️ **Profile Management** - Update contact and emergency information
- 📱 **Unique QR Code** - Each resident gets a permanent QR code
- 🔄 **Real-time Updates** - Changes reflect instantly on QR-linked profiles

### For Admins
- 👮‍♂️ **Full Control** - Manage all resident records
- 📊 **Dashboard** - View all residents organized by room number
- ✏️ **Edit Capabilities** - Update any resident's information
- 🗑️ **Delete Records** - Remove residents when they leave
- 🔍 **Search & Filter** - Easily find residents

### Technical Features
- 📱 **Responsive Design** - Works on all devices
- 🎨 **Modern UI** - Clean, professional interface
- 🔒 **Role-based Access** - Separate admin and resident permissions
- 💾 **Dynamic Database** - SQLite for easy deployment
- 📥 **QR Download** - Export QR codes as images

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Installation

1. **Clone or download the project**
```bash
cd hostel_management_system
```

2. **Install dependencies**
```bash
pip install -r requirements.txt --break-system-packages
```

3. **Run the application**
```bash
python app.py
```

4. **Access the system**
- Open browser and go to: `http://localhost:5000`
- Admin credentials: 
  - Username: `admin`
  - Password: `admin123`

## 📁 Project Structure

```
hostel_management_system/
│
├── app.py                      # Main Flask application
├── config.py                   # Configuration settings
├── requirements.txt            # Python dependencies
├── README.md                   # This file
│
├── models/
│   └── db.py                   # Database models
│
├── utils/
│   └── qr_generator.py         # QR code generation
│
├── static/
│   ├── css/
│   │   └── style.css           # Professional styling
│   ├── js/
│   │   └── script.js           # Interactive features
│   ├── images/                 # Profile images
│   └── qr/                     # Generated QR codes
│
└── templates/
    ├── base.html               # Base template
    ├── index.html              # Home page
    ├── register.html           # Registration form
    ├── resident_login.html     # Resident login
    ├── admin_login.html        # Admin login
    ├── resident_profile.html   # Profile display
    ├── edit_profile.html       # Edit profile
    ├── admin_dashboard.html    # Admin panel
    └── error.html              # Error pages
```

## 🎯 Usage Guide

### For Residents

1. **Registration**
   - Go to the home page
   - Click "Register Now"
   - Fill in all required details
   - Create a password
   - Submit the form
   - You'll receive a unique QR code

2. **Login**
   - Click "Resident Login"
   - Enter your email and password
   - Access your dashboard

3. **Update Profile**
   - Login to your account
   - Click "Edit Profile"
   - Update allowed fields (contact info, address, emergency contact)
   - Save changes

4. **Download QR Code**
   - View your profile
   - Click "Download QR Code"
   - Share it for easy profile access

### For Admin

1. **Login**
   - Click "Admin Login"
   - Default credentials:
     - Username: `admin`
     - Password: `admin123`
   - **⚠️ Change these in production!**

2. **View All Residents**
   - Access the admin dashboard
   - See all residents in a table
   - Use search to find specific residents

3. **Edit Resident**
   - Click the edit (✏️) button next to any resident
   - Modify any field
   - Update password if needed
   - Save changes

4. **Delete Resident**
   - Click delete (🗑️) button
   - Confirm deletion
   - Resident can re-register after deletion

## 🔧 Configuration

### Change Admin Credentials
Edit `config.py`:
```python
ADMIN_USERNAME = 'your_username'
ADMIN_PASSWORD = 'your_secure_password'
```

### Database Configuration
The system uses SQLite by default. To change database:
```python
SQLALCHEMY_DATABASE_URI = 'sqlite:///database.db'
```

### QR Code Base URL
Update in `utils/qr_generator.py` for production:
```python
base_url = 'https://yourdomain.com'
```

## 🌐 Deployment

### Local Deployment
```bash
python app.py
```

### Production Deployment

1. **Set environment variables**
```bash
export SECRET_KEY='your-secret-key'
export FLASK_ENV=production
```

2. **Use production WSGI server**
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

3. **Configure reverse proxy (Nginx)**
```nginx
server {
    listen 80;
    server_name yourdomain.com;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 📊 Database Schema

### Resident Table
- `id` - Primary key
- `full_name` - Resident's full name
- `email` - Unique email (login username)
- `phone` - Unique phone number
- `date_of_birth` - DOB
- `gender` - Gender
- `permanent_address` - Full address
- `city` - City
- `state` - State
- `pincode` - Postal code
- `room_number` - Unique room number
- `date_of_joining` - Joining date
- `emergency_contact_name` - Emergency contact
- `emergency_contact_phone` - Emergency phone
- `emergency_contact_relation` - Relationship
- `password_hash` - Hashed password
- `profile_image` - Profile picture filename
- `created_at` - Registration timestamp
- `updated_at` - Last update timestamp

## 🔒 Security Features

- ✅ Password hashing using Werkzeug
- ✅ Session-based authentication
- ✅ CSRF protection (Flask built-in)
- ✅ SQL injection protection (SQLAlchemy ORM)
- ✅ Role-based access control
- ✅ Input validation
- ✅ Unique constraints on email, phone, room

## 🎨 Customization

### Change Color Scheme
Edit `static/css/style.css`:
```css
:root {
    --primary-color: #2563eb;  /* Change to your color */
    --secondary-color: #10b981;
    --danger-color: #ef4444;
}
```

### Add New Fields
1. Update `models/db.py` - Add field to Resident model
2. Update templates - Add form inputs
3. Update `app.py` - Handle new field in routes
4. Run migration or recreate database

## 📱 QR Code System

- Each resident gets a unique QR code upon registration
- QR code contains only the profile URL (no personal data)
- Scanning opens the public profile page
- QR codes never need regeneration (dynamic data)
- Can be downloaded and printed

## 🐛 Troubleshooting

### Database not created
```bash
python
>>> from app import app, db
>>> with app.app_context():
...     db.create_all()
```

### QR codes not generating
- Ensure `static/qr/` directory exists
- Check write permissions
- Verify qrcode library is installed

### Port already in use
```bash
# Use different port
python app.py --port 5001
```

### Import errors
```bash
pip install -r requirements.txt --break-system-packages --force-reinstall
```

## 🚧 Future Enhancements

- [ ] Fees management
- [ ] Attendance tracking
- [ ] Complaints/Requests system
- [ ] Email notifications
- [ ] Bulk operations
- [ ] Data export (CSV/Excel)
- [ ] Photo upload for residents
- [ ] Mobile app
- [ ] Multi-hostel support
- [ ] Advanced analytics

## 📄 License

MIT License - Feel free to use and modify for your needs.

## 👨‍💻 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📧 Support

For issues and questions:
- Create an issue on GitHub
- Email: support@example.com

## 🙏 Acknowledgments

- Flask framework
- QRCode library
- Modern CSS design patterns
- Open source community

---

**Made with ❤️ for better hostel management**

⭐ Star this project if you find it helpful!
