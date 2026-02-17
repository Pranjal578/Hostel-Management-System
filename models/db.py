from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class Resident(db.Model):
    """Resident model for hostel residents"""
    __tablename__ = 'residents'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Personal Information
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(15), unique=True, nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    
    # Address Information
    permanent_address = db.Column(db.Text, nullable=False)
    city = db.Column(db.String(50), nullable=False)
    state = db.Column(db.String(50), nullable=False)
    pincode = db.Column(db.String(10), nullable=False)
    
    # Hostel Information
    room_number = db.Column(db.String(10), unique=True, nullable=False)
    date_of_joining = db.Column(db.Date, nullable=False)
    
    # Emergency Contact
    emergency_contact_name = db.Column(db.String(100), nullable=False)
    emergency_contact_phone = db.Column(db.String(15), nullable=False)
    emergency_contact_relation = db.Column(db.String(50), nullable=False)
    
    # Authentication
    password_hash = db.Column(db.String(200), nullable=False)

    # Identity & Documents
    aadhar_id = db.Column(db.String(14), nullable=True)  # Format: XXXX-XXXX-XXXX

    # Profile
    profile_image = db.Column(db.String(200), default='default_profile.png')
    profile_photo_base64 = db.Column(db.LargeBinary, nullable=True)  # Store Base64 photo data

    # Guardian Information
    guardian_name = db.Column(db.String(100), nullable=True)
    guardian_phone = db.Column(db.String(15), nullable=True)
    guardian_email = db.Column(db.String(120), nullable=True)
    guardian_relation = db.Column(db.String(50), nullable=True)  # e.g., Father, Mother, Guardian

    # Additional Contact
    emergency_contact_address = db.Column(db.Text, nullable=True)

    # OTP Configuration
    otp_enabled = db.Column(db.Boolean, default=False)
    otp_code = db.Column(db.String(20), nullable=True)
    otp_expires_at = db.Column(db.DateTime, nullable=True)
    otp_method = db.Column(db.String(10), nullable=True)  # 'email' or 'sms'

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if password is correct"""
        return check_password_hash(self.password_hash, password)

    def is_otp_enabled(self):
        """Check if OTP is enabled for this resident"""
        return self.otp_enabled

    def setup_otp(self, method):
        """Enable OTP for resident"""
        self.otp_enabled = True
        self.otp_method = method

    def disable_otp(self):
        """Disable OTP for resident"""
        self.otp_enabled = False
        self.otp_method = None
        self.otp_code = None
        self.otp_expires_at = None

    def mask_aadhar(self):
        """Return masked aadhar: XXXX-XXXX-9012"""
        if not self.aadhar_id:
            return None
        aadhar_clean = self.aadhar_id.replace('-', '')
        if len(aadhar_clean) >= 4:
            return f"XXXX-XXXX-{aadhar_clean[-4:]}"
        return None

    def validate_aadhar_format(self):
        """Check if aadhar is valid 12-digit format"""
        if not self.aadhar_id:
            return True  # Optional field
        aadhar_clean = self.aadhar_id.replace('-', '')
        return aadhar_clean.isdigit() and len(aadhar_clean) == 12

    def has_guardian(self):
        """Check if guardian information is available"""
        return bool(self.guardian_name and self.guardian_phone)

    def format_aadhar(self, aadhar_string):
        """Format aadhar string to XXXX-XXXX-XXXX format"""
        if not aadhar_string:
            return None
        aadhar_clean = aadhar_string.replace('-', '')
        if aadhar_clean.isdigit() and len(aadhar_clean) == 12:
            return f"{aadhar_clean[:4]}-{aadhar_clean[4:8]}-{aadhar_clean[8:12]}"
        return aadhar_clean  # Return as-is if invalid format
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'full_name': self.full_name,
            'email': self.email,
            'phone': self.phone,
            'date_of_birth': self.date_of_birth.strftime('%Y-%m-%d') if self.date_of_birth else None,
            'gender': self.gender,
            'permanent_address': self.permanent_address,
            'city': self.city,
            'state': self.state,
            'pincode': self.pincode,
            'room_number': self.room_number,
            'date_of_joining': self.date_of_joining.strftime('%Y-%m-%d') if self.date_of_joining else None,
            'emergency_contact_name': self.emergency_contact_name,
            'emergency_contact_phone': self.emergency_contact_phone,
            'emergency_contact_relation': self.emergency_contact_relation,
            'profile_image': self.profile_image,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Resident {self.full_name} - Room {self.room_number}>'
