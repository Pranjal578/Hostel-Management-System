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
    
    # Profile
    profile_image = db.Column(db.String(200), default='default_profile.png')
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if password is correct"""
        return check_password_hash(self.password_hash, password)
    
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
