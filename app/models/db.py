from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from app.utils.encryption import encrypt_field, decrypt_field

db = SQLAlchemy()

class User(db.Model):
    """Core credentials model for all system users (SuperAdmin, HostelOwner, Resident)"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='Resident')  # 'SuperAdmin', 'HostelOwner', 'Resident'
    
    # OTP Configuration
    otp_enabled = db.Column(db.Boolean, default=False)
    otp_code = db.Column(db.String(200), nullable=True)  # Hashed OTP code
    otp_expires_at = db.Column(db.DateTime, nullable=True)
    otp_method = db.Column(db.String(10), nullable=True)  # 'email' or 'sms'
    
    # Session / Password version for session invalidation on password change
    password_version = db.Column(db.Integer, default=1, nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    hostels = db.relationship('Hostel', backref='owner', lazy=True)
    resident_profile = db.relationship('Resident', backref='user', uselist=False, lazy=True, cascade="all, delete-orphan")
    audit_logs = db.relationship('AuditLog', backref='user', lazy=True)
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
        if self.password_version is None:
            self.password_version = 1
        else:
            self.password_version += 1
        
    def check_password(self, password):
        """Check if password is correct"""
        return check_password_hash(self.password_hash, password)
        
    def is_otp_enabled(self):
        """Check if OTP is enabled for this user"""
        return self.otp_enabled
        
    def setup_otp(self, method):
        """Enable OTP for user"""
        self.otp_enabled = True
        self.otp_method = method
        
    def disable_otp(self):
        """Disable OTP for user"""
        self.otp_enabled = False
        self.otp_method = None
        self.otp_code = None
        self.otp_expires_at = None
        
    def __repr__(self):
        return f'<User {self.email} - Role {self.role}>'


class Hostel(db.Model):
    """Hostel model representing a hostel managed under the platform"""
    __tablename__ = 'hostels'
    
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    hostel_name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    total_capacity = db.Column(db.Integer, nullable=False, default=100)
    payment_qr_code = db.Column(db.String(200), nullable=True)  # Path to payment QR image
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    residents = db.relationship('Resident', backref='hostel', lazy=True)
    payments = db.relationship('Payment', backref='hostel', lazy=True)
    
    def __repr__(self):
        return f'<Hostel {self.hostel_name} - Owner {self.owner_id}>'


class Resident(db.Model):
    """Resident model for hostel residents containing profile details. Sensitive fields are encrypted at rest."""
    __tablename__ = 'residents'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    hostel_id = db.Column(db.Integer, db.ForeignKey('hostels.id'), nullable=False)
    
    # Personal Information
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(250), unique=True, nullable=False)  # Encrypted phone
    date_of_birth = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    
    # Address Information (Encrypted permanent address)
    permanent_address = db.Column(db.Text, nullable=False)  # Encrypted address
    city = db.Column(db.String(50), nullable=False)
    state = db.Column(db.String(50), nullable=False)
    pincode = db.Column(db.String(10), nullable=False)
    
    # Hostel Information
    room_number = db.Column(db.String(10), nullable=False)  # Unique per hostel, handled in validation
    date_of_joining = db.Column(db.Date, nullable=False)
    
    # Emergency Contact
    emergency_contact_name = db.Column(db.String(100), nullable=False)
    emergency_contact_phone = db.Column(db.String(15), nullable=False)
    emergency_contact_relation = db.Column(db.String(50), nullable=False)
    
    # Identity & Documents (Encrypted aadhar id)
    aadhar_id = db.Column(db.String(250), nullable=True)  # Encrypted Aadhar
    
    # Profile
    profile_image = db.Column(db.String(200), default='default_profile.png')
    profile_photo_base64 = db.Column(db.LargeBinary, nullable=True)
    
    # Guardian Information
    guardian_name = db.Column(db.String(100), nullable=True)
    guardian_phone = db.Column(db.String(15), nullable=True)
    guardian_email = db.Column(db.String(120), nullable=True)
    guardian_relation = db.Column(db.String(50), nullable=True)
    
    # Additional Contact
    emergency_contact_address = db.Column(db.Text, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    payments = db.relationship('Payment', backref='resident', lazy=True, cascade="all, delete-orphan")
    
    # Encrypted Properties getters and setters
    @property
    def phone_decrypted(self):
        return decrypt_field(self.phone)
        
    @phone_decrypted.setter
    def phone_decrypted(self, value):
        self.phone = encrypt_field(value)
        
    @property
    def permanent_address_decrypted(self):
        return decrypt_field(self.permanent_address)
        
    @permanent_address_decrypted.setter
    def permanent_address_decrypted(self, value):
        self.permanent_address = encrypt_field(value)
        
    @property
    def aadhar_id_decrypted(self):
        return decrypt_field(self.aadhar_id)
        
    @aadhar_id_decrypted.setter
    def aadhar_id_decrypted(self, value):
        self.aadhar_id = encrypt_field(value)
        
    def mask_aadhar(self):
        """Return masked aadhar: XXXX-XXXX-9012"""
        aadhar_dec = self.aadhar_id_decrypted
        if not aadhar_dec:
            return None
        aadhar_clean = aadhar_dec.replace('-', '')
        if len(aadhar_clean) >= 4:
            return f"XXXX-XXXX-{aadhar_clean[-4:]}"
        return None
        
    def validate_aadhar_format(self):
        """Check if aadhar is valid 12-digit format"""
        aadhar_dec = self.aadhar_id_decrypted
        if not aadhar_dec:
            return True  # Optional field
        aadhar_clean = aadhar_dec.replace('-', '')
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
        return aadhar_clean
        
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'hostel_id': self.hostel_id,
            'full_name': self.full_name,
            'email': self.user.email if self.user else None,
            'phone': self.phone_decrypted,
            'date_of_birth': self.date_of_birth.strftime('%Y-%m-%d') if self.date_of_birth else None,
            'gender': self.gender,
            'permanent_address': self.permanent_address_decrypted,
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


class Payment(db.Model):
    """Payment model to track rent transactions and approvals"""
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    resident_id = db.Column(db.Integer, db.ForeignKey('residents.id'), nullable=False)
    hostel_id = db.Column(db.Integer, db.ForeignKey('hostels.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.Date, nullable=False)
    transaction_id = db.Column(db.String(100), nullable=False)
    screenshot_path = db.Column(db.String(250), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Pending')  # 'Pending', 'Verified', 'Rejected'
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Payment Resident {self.resident_id} - Amount {self.amount} - Status {self.status}>'


class AuditLog(db.Model):
    """AuditLog model for logging administrative and high-security operations"""
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Null if system-initiated
    action = db.Column(db.String(250), nullable=False)
    ip_address = db.Column(db.String(50), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<AuditLog User {self.user_id} - Action {self.action} - Time {self.timestamp}>'
