from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from app.utils.encryption import encrypt_field, decrypt_field
from sqlalchemy import MetaData

naming_convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

db = SQLAlchemy(metadata=MetaData(naming_convention=naming_convention))

class User(db.Model):
    """Core credentials model for all system users (SuperAdmin, HostelOwner, Resident)"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='Resident')  # 'SuperAdmin', 'HostelOwner', 'Resident'
    full_name = db.Column(db.String(100), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    
    # OTP Configuration (2FA Mandatory for all users)
    otp_enabled = db.Column(db.Boolean, default=True)
    otp_code = db.Column(db.String(200), nullable=True)  # Hashed OTP code
    otp_expires_at = db.Column(db.DateTime, nullable=True)
    otp_method = db.Column(db.String(10), default='email')  # 'email' or 'sms'
    
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
        """2FA is mandatory across all users."""
        return True
        
    def setup_otp(self, method):
        """Update OTP delivery method for user"""
        self.otp_enabled = True
        self.otp_method = method or 'email'
        
    def disable_otp(self):
        """2FA is mandatory - defaults to email method."""
        self.otp_enabled = True
        self.otp_method = 'email'
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
    
    # Prices / bills
    rent = db.Column(db.Float, nullable=True, default=0.0)
    electricity_bill = db.Column(db.Float, nullable=True, default=0.0)
    
    # Multi-tenant discovery fields
    hostel_code = db.Column(db.String(20), unique=True, nullable=True)  # e.g. HOS-2026-001
    facilities = db.Column(db.Text, nullable=True)  # Comma-separated: "Wi-Fi,Laundry,Mess"
    hostel_qr_code = db.Column(db.String(200), nullable=True)  # Path to hostel-info QR image
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    residents = db.relationship('Resident', backref='hostel', lazy=True)
    payments = db.relationship('Payment', backref='hostel', lazy=True)
    notices = db.relationship('Notice', backref='hostel', lazy=True, cascade='all, delete-orphan')
    
    @property
    def facilities_list(self):
        """Return facilities as a Python list"""
        if not self.facilities:
            return []
        return [f.strip() for f in self.facilities.split(',') if f.strip()]
    
    @property
    def available_rooms(self):
        """Calculate available rooms dynamically from resident count"""
        return max(0, self.total_capacity - len(self.residents))
    
    @property
    def pending_payments_count(self):
        """Returns count of pending payments in this hostel. Efficient if payments are preloaded."""
        count = 0
        for r in self.residents:
            for p in r.payments:
                if p.status == 'Pending':
                    count += 1
        return count

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
    room_number = db.Column(db.String(10), nullable=True)  # Unique per hostel, handled in validation
    date_of_joining = db.Column(db.Date, nullable=False)
    rent = db.Column(db.Float, nullable=True, default=0.0)
    electricity_bill = db.Column(db.Float, nullable=True, default=0.0)
    status = db.Column(db.String(20), nullable=False, default='Pending')  # 'Pending', 'Active', 'Rejected'
    
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
        
    @property
    def payment_status(self):
        """Returns the status of the latest payment, or 'None' if no payments exist. Efficient when payments are preloaded."""
        if not self.payments:
            return 'None'
        sorted_payments = sorted(self.payments, key=lambda p: p.created_at, reverse=True)
        return sorted_payments[0].status
        
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


class Notice(db.Model):
    """Notice model for hostel owner announcements to residents"""
    __tablename__ = 'notices'
    
    id = db.Column(db.Integer, primary_key=True)
    hostel_id = db.Column(db.Integer, db.ForeignKey('hostels.id'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Notice Hostel {self.hostel_id} - {self.title}>'


class Message(db.Model):
    """Message model for simple chat history between owners and residents"""
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message_content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)
    
    # Relationships
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_messages')
    
    def __repr__(self):
        return f'<Message Sender {self.sender_id} -> Receiver {self.receiver_id} at {self.created_at}>'


# ─────────────────────────────────────────────────────────────────
# Pharmacy / Medical Store Module Models
# ─────────────────────────────────────────────────────────────────

class Shop(db.Model):
    """Shop model representing a licensed medical/pharmacy store on the platform"""
    __tablename__ = 'shops'

    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    shop_name = db.Column(db.String(150), nullable=False)
    license_number = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(250), nullable=False)
    description = db.Column(db.Text, nullable=True)
    contact_phone = db.Column(db.String(20), nullable=True)
    contact_email = db.Column(db.String(120), nullable=True)
    verification_status = db.Column(db.String(20), nullable=False, default='Pending')  # 'Pending', 'Approved', 'Rejected'
    rating_avg = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    owner = db.relationship('User', backref='shops', foreign_keys=[owner_id])
    medicines = db.relationship('Medicine', backref='shop', lazy=True, cascade='all, delete-orphan')
    orders = db.relationship('MedicineOrder', backref='shop', lazy=True)

    @property
    def approved_medicines_count(self):
        return Medicine.query.filter_by(shop_id=self.id, is_available=True).count()

    @property
    def total_reviews(self):
        count = 0
        for med in self.medicines:
            count += len(med.reviews)
        return count

    def recalculate_rating(self):
        """Recalculate average rating from all medicine reviews in this shop"""
        total, count = 0, 0
        for med in self.medicines:
            for review in med.reviews:
                total += review.rating
                count += 1
        self.rating_avg = round(total / count, 1) if count > 0 else 0.0

    def __repr__(self):
        return f'<Shop {self.shop_name} - Status {self.verification_status}>'


class Medicine(db.Model):
    """Medicine/product model in a medical store inventory"""
    __tablename__ = 'medicines'

    id = db.Column(db.Integer, primary_key=True)
    shop_id = db.Column(db.Integer, db.ForeignKey('shops.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Float, nullable=False)
    photo_path = db.Column(db.String(250), nullable=True)  # Relative to static/images/medicines/
    salt_composition = db.Column(db.String(500), nullable=True)  # e.g. "Paracetamol 500mg + Ibuprofen 200mg"
    category = db.Column(db.String(100), nullable=True)           # e.g. "Analgesic", "Antibiotic"
    description = db.Column(db.Text, nullable=True)
    stock_quantity = db.Column(db.Integer, nullable=False, default=0)
    delivery_options = db.Column(db.String(100), nullable=True, default='Standard')  # Comma-separated: 'Express,Standard'
    payment_options = db.Column(db.String(100), nullable=True, default='UPI,COD')    # Comma-separated: 'UPI,COD'
    is_available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    reviews = db.relationship('MedicineReview', backref='medicine', lazy=True, cascade='all, delete-orphan')
    orders = db.relationship('MedicineOrder', backref='medicine', lazy=True)

    @property
    def delivery_options_list(self):
        if not self.delivery_options:
            return []
        return [d.strip() for d in self.delivery_options.split(',') if d.strip()]

    @property
    def payment_options_list(self):
        if not self.payment_options:
            return []
        return [p.strip() for p in self.payment_options.split(',') if p.strip()]

    @property
    def average_rating(self):
        if not self.reviews:
            return 0.0
        return round(sum(r.rating for r in self.reviews) / len(self.reviews), 1)

    @property
    def photo_url(self):
        if self.photo_path:
            return f'/static/images/medicines/{self.photo_path}'
        return '/static/images/default_medicine.png'

    def __repr__(self):
        return f'<Medicine {self.name} - Shop {self.shop_id} - ₹{self.price}>'


class MedicineOrder(db.Model):
    """Order record created when a user purchases a medicine"""
    __tablename__ = 'medicine_orders'

    id = db.Column(db.Integer, primary_key=True)
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicines.id'), nullable=False)
    shop_id = db.Column(db.Integer, db.ForeignKey('shops.id'), nullable=False)
    buyer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    total_price = db.Column(db.Float, nullable=False)
    delivery_option = db.Column(db.String(50), nullable=False, default='Standard')  # 'Express' or 'Standard'
    payment_option = db.Column(db.String(50), nullable=False, default='UPI')       # 'UPI' or 'COD'
    delivery_address = db.Column(db.Text, nullable=True)     # Buyer's local campus / hostel address
    contact_phone = db.Column(db.String(20), nullable=True)  # Buyer contact for delivery
    receipt_path = db.Column(db.String(250), nullable=True)  # Proof of payment (for UPI orders)
    status = db.Column(db.String(20), nullable=False, default='Pending')  # 'Pending', 'Confirmed', 'Rejected'
    # Delivery pipeline status (only relevant for Confirmed orders)
    delivery_status = db.Column(db.String(30), nullable=False, default='Order Placed')
    # Stages: 'Order Placed' -> 'Confirmed' -> 'Packed' -> 'Out for Delivery' -> 'Delivered'
    notes = db.Column(db.Text, nullable=True)  # Buyer notes / special requests
    rejection_reason = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    buyer = db.relationship('User', backref='medicine_orders', foreign_keys=[buyer_id])

    # Ordered list of all delivery stages for progress tracking
    DELIVERY_STAGES = ['Order Placed', 'Confirmed', 'Packed', 'Out for Delivery', 'Delivered']

    @property
    def delivery_stage_index(self):
        """Return 0-based index of the current delivery_status in the pipeline"""
        try:
            return self.DELIVERY_STAGES.index(self.delivery_status)
        except ValueError:
            return 0

    def __repr__(self):
        return f'<MedicineOrder #{self.id} - Medicine {self.medicine_id} - Buyer {self.buyer_id} - Status {self.status} - Delivery {self.delivery_status}>'



class MedicineReview(db.Model):
    """Customer review and star rating for a medicine"""
    __tablename__ = 'medicine_reviews'

    id = db.Column(db.Integer, primary_key=True)
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicines.id'), nullable=False)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 integer rating
    comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    reviewer = db.relationship('User', backref='medicine_reviews', foreign_keys=[reviewer_id])

    def __repr__(self):
        return f'<MedicineReview Medicine {self.medicine_id} - Rating {self.rating}/5 by User {self.reviewer_id}>'
