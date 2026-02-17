from dotenv import load_dotenv
load_dotenv()

from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
from models.db import db, Resident
from utils.qr_generator import generate_qr_code, delete_qr_code
from utils.otp_generator import generate_otp, hash_otp, validate_otp, get_otp_expiry_time, get_remaining_time
from utils.email_sender import send_otp_email, init_mail
from utils.sms_sender import send_otp_sms
from utils.photo_handler import save_photo, validate_photo
from config import DevelopmentConfig, ProductionConfig, Config
from datetime import datetime
from functools import wraps
import os

app = Flask(__name__)

# Load configuration based on environment
env = os.environ.get('FLASK_ENV', 'development')
if env == 'production':
    app.config.from_object(ProductionConfig)
else:
    app.config.from_object(DevelopmentConfig)

# Initialize database
db.init_app(app)

# Initialize email
init_mail(app)

# Create tables
with app.app_context():
    db.create_all()

# Decorators for authentication
def login_required(f):
    """Decorator to require resident login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'resident_id' not in session:
            flash('Please login to access this page.', 'warning')
            return redirect(url_for('resident_login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to require admin login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            flash('Admin access required.', 'danger')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def otp_pending_required(f):
    """Decorator to require OTP verification pending state"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'otp_pending_resident_id' not in session:
            flash('Please login first.', 'warning')
            return redirect(url_for('resident_login'))
        return f(*args, **kwargs)
    return decorated_function

# ============= PUBLIC ROUTES =============

@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Resident registration with photo and additional details"""
    if request.method == 'POST':
        try:
            # Check if email or phone already exists
            existing_email = Resident.query.filter_by(email=request.form['email']).first()
            existing_phone = Resident.query.filter_by(phone=request.form['phone']).first()
            existing_room = Resident.query.filter_by(room_number=request.form['room_number']).first()

            if existing_email:
                flash('Email already registered!', 'danger')
                return redirect(url_for('register'))

            if existing_phone:
                flash('Phone number already registered!', 'danger')
                return redirect(url_for('register'))

            if existing_room:
                flash('Room number already occupied!', 'danger')
                return redirect(url_for('register'))

            # Validate password match
            if request.form['password'] != request.form['confirm_password']:
                flash('Passwords do not match!', 'danger')
                return redirect(url_for('register'))

            # Format aadhar if provided
            aadhar_raw = request.form.get('aadhar_id', '').replace('-', '')
            aadhar_formatted = None
            if aadhar_raw:
                if aadhar_raw.isdigit() and len(aadhar_raw) == 12:
                    aadhar_formatted = f"{aadhar_raw[:4]}-{aadhar_raw[4:8]}-{aadhar_raw[8:12]}"
                else:
                    flash('Aadhar must be 12 digits', 'warning')
                    aadhar_formatted = None

            # Create new resident
            resident = Resident(
                full_name=request.form['full_name'],
                email=request.form['email'],
                phone=request.form['phone'],
                date_of_birth=datetime.strptime(request.form['date_of_birth'], '%Y-%m-%d'),
                gender=request.form['gender'],
                permanent_address=request.form['permanent_address'],
                city=request.form['city'],
                state=request.form['state'],
                pincode=request.form['pincode'],
                room_number=request.form['room_number'],
                date_of_joining=datetime.strptime(request.form['date_of_joining'], '%Y-%m-%d'),
                emergency_contact_name=request.form['emergency_contact_name'],
                emergency_contact_phone=request.form['emergency_contact_phone'],
                emergency_contact_relation=request.form['emergency_contact_relation'],
                # New fields
                aadhar_id=aadhar_formatted,
                guardian_name=request.form.get('guardian_name') or None,
                guardian_phone=request.form.get('guardian_phone') or None,
                guardian_email=request.form.get('guardian_email') or None,
                guardian_relation=request.form.get('guardian_relation') or None,
                emergency_contact_address=request.form.get('emergency_contact_address') or None
            )

            # Set password
            resident.set_password(request.form['password'])

            # Save to database first (to get ID for photo storage)
            db.session.add(resident)
            db.session.commit()

            # Handle photo upload
            photo_file = request.files.get('profile_photo')
            if photo_file and photo_file.filename:
                is_valid, error_msg = validate_photo(photo_file)
                if not is_valid:
                    flash(f'Photo error: {error_msg}', 'warning')
                else:
                    success, error = save_photo(photo_file, resident.id, db, resident)
                    if success:
                        flash('Photo uploaded successfully!', 'success')
                    else:
                        flash(f'Photo upload error: {error}', 'warning')

            # Generate QR code
            generate_qr_code(resident.id)

            flash('Registration successful! You can now login.', 'success')
            return redirect(url_for('resident_login'))

        except Exception as e:
            db.session.rollback()
            flash(f'Registration failed: {str(e)}', 'danger')
            return redirect(url_for('register'))

    return render_template('register.html')

@app.route('/profile/<int:resident_id>')
def profile(resident_id):
    """View resident profile (public via QR code)"""
    resident = Resident.query.get_or_404(resident_id)
    return render_template('resident_profile.html', resident=resident, is_public=True)

# ============= RESIDENT ROUTES =============

@app.route('/resident/login', methods=['GET', 'POST'])
def resident_login():
    """Resident login with optional OTP"""
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        resident = Resident.query.filter_by(email=email).first()

        if resident and resident.check_password(password):
            # Password correct
            if resident.is_otp_enabled():
                # OTP enabled for this resident - redirect to OTP verification
                session['otp_pending_resident_id'] = resident.id
                # Generate OTP
                otp_code = generate_otp(app.config['OTP_LENGTH'])
                resident.otp_code = hash_otp(otp_code)
                resident.otp_expires_at = get_otp_expiry_time(app.config['OTP_EXPIRY_MINUTES'])
                db.session.commit()

                flash('Password verified! Please enter the OTP sent to your account.', 'info')
                return redirect(url_for('send_otp'))
            else:
                # No OTP - standard login
                session['resident_id'] = resident.id
                session['resident_name'] = resident.full_name
                flash(f'Welcome back, {resident.full_name}!', 'success')
                return redirect(url_for('resident_dashboard'))
        else:
            flash('Invalid email or password!', 'danger')

    return render_template('resident_login.html')

@app.route('/resident/dashboard')
@login_required
def resident_dashboard():
    """Resident dashboard"""
    resident = Resident.query.get(session['resident_id'])
    return render_template('resident_profile.html', resident=resident, is_public=False)

@app.route('/resident/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Edit resident profile with photo upload and new fields"""
    resident = Resident.query.get(session['resident_id'])
    is_admin = session.get('is_admin', False)

    if request.method == 'POST':
        try:
            # Validation: password confirmation match if new password provided
            new_password = request.form.get('new_password', '').strip()
            if new_password:
                confirm_password = request.form.get('confirm_new_password', '').strip()
                if new_password != confirm_password:
                    flash('New passwords do not match!', 'danger')
                    return redirect(url_for('edit_profile'))
                if len(new_password) < 6:
                    flash('Password must be at least 6 characters!', 'danger')
                    return redirect(url_for('edit_profile'))

            # Admin can edit all fields
            if is_admin:
                resident.full_name = request.form['full_name']
                resident.gender = request.form['gender']
                resident.date_of_birth = request.form['date_of_birth']
                resident.email = request.form['email']
                resident.phone = request.form['phone']
                resident.room_number = request.form['room_number']
                resident.date_of_joining = request.form['date_of_joining']

                # Aadhar formatting for admin
                aadhar_raw = request.form.get('aadhar_id', '').replace('-', '')
                if aadhar_raw:
                    if aadhar_raw.isdigit() and len(aadhar_raw) == 12:
                        resident.aadhar_id = f"{aadhar_raw[:4]}-{aadhar_raw[4:8]}-{aadhar_raw[8:12]}"
                    else:
                        resident.aadhar_id = None
                else:
                    resident.aadhar_id = None

            # Both admin and residents can edit these
            resident.permanent_address = request.form['permanent_address']
            resident.city = request.form['city']
            resident.state = request.form['state']
            resident.pincode = request.form['pincode']
            resident.phone = request.form['phone']
            resident.emergency_contact_name = request.form['emergency_contact_name']
            resident.emergency_contact_phone = request.form['emergency_contact_phone']
            resident.emergency_contact_relation = request.form['emergency_contact_relation']

            # Guardian information (optional for both)
            resident.guardian_name = request.form.get('guardian_name', '') or None
            resident.guardian_phone = request.form.get('guardian_phone', '') or None
            resident.guardian_email = request.form.get('guardian_email', '') or None
            resident.guardian_relation = request.form.get('guardian_relation', '') or None

            # Emergency contact address (optional for both)
            resident.emergency_contact_address = request.form.get('emergency_contact_address', '') or None

            # Handle photo upload (optional)
            if 'profile_photo' in request.files and request.files['profile_photo'].filename:
                file = request.files['profile_photo']
                success, error_msg = save_photo(file, resident.id, db=db, resident=resident)
                if not success:
                    flash(f'Photo upload failed: {error_msg}', 'danger')
                    return redirect(url_for('edit_profile'))

            # Update password if provided
            if new_password:
                resident.set_password(new_password)

            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('resident_dashboard'))

        except Exception as e:
            db.session.rollback()
            flash(f'Update failed: {str(e)}', 'danger')

    return render_template('edit_profile.html', resident=resident, is_admin=is_admin)

@app.route('/resident/logout')
def resident_logout():
    """Resident logout"""
    session.pop('resident_id', None)
    session.pop('resident_name', None)
    flash('Logged out successfully!', 'info')
    return redirect(url_for('index'))

@app.route('/resident/download-qr/<int:resident_id>')
@login_required
def download_qr(resident_id):
    """Download QR code"""
    # Check if resident is accessing their own QR
    if session['resident_id'] != resident_id:
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('resident_dashboard'))
    
    qr_path = os.path.join(os.path.dirname(__file__), 'static', 'qr', f"{resident_id}.png")
    if os.path.exists(qr_path):
        return send_file(qr_path, as_attachment=True, download_name=f'qr_code_{resident_id}.png')
    else:
        flash('QR code not found!', 'danger')
        return redirect(url_for('resident_dashboard'))

# ============= OTP ROUTES =============

@app.route('/resident/send-otp', methods=['GET', 'POST'])
@otp_pending_required
def send_otp():
    """Send OTP via email or SMS"""
    resident_id = session.get('otp_pending_resident_id')
    resident = Resident.query.get_or_404(resident_id)

    if request.method == 'POST':
        method = request.form.get('method')

        if method == 'email':
            # Send via email
            otp_code = generate_otp(app.config['OTP_LENGTH'])
            resident.otp_code = hash_otp(otp_code)
            resident.otp_expires_at = get_otp_expiry_time(app.config['OTP_EXPIRY_MINUTES'])
            db.session.commit()

            success, message = send_otp_email(resident.email, otp_code, resident.full_name)
            if success:
                flash(f'OTP sent to {resident.email}', 'success')
                return redirect(url_for('verify_otp'))
            else:
                flash(f'Error: {message}', 'danger')
        elif method == 'sms':
            # Send via SMS
            otp_code = generate_otp(app.config['OTP_LENGTH'])
            resident.otp_code = hash_otp(otp_code)
            resident.otp_expires_at = get_otp_expiry_time(app.config['OTP_EXPIRY_MINUTES'])
            db.session.commit()

            success, message = send_otp_sms(resident.phone, otp_code, resident.full_name)
            if success:
                flash(f'OTP sent via SMS', 'success')
                return redirect(url_for('verify_otp'))
            else:
                flash(f'Error: {message}', 'danger')

    # Prepare display values (mask sensitive info)
    masked_email = resident.email
    masked_phone = (resident.phone[-4:] if resident.phone else '****').rjust(len(resident.phone or '*'), '*')

    return render_template('send_otp.html',
                         resident=resident,
                         masked_email=masked_email,
                         masked_phone=masked_phone)


@app.route('/resident/verify-otp', methods=['GET', 'POST'])
@otp_pending_required
def verify_otp():
    """Verify OTP code"""
    resident_id = session.get('otp_pending_resident_id')
    resident = Resident.query.get_or_404(resident_id)

    if request.method == 'POST':
        otp_entered = request.form.get('otp_code', '').strip()

        if not otp_entered:
            flash('Please enter OTP code', 'danger')
            return redirect(url_for('verify_otp'))

        # Validate OTP
        is_valid, error_message = validate_otp(
            otp_entered,
            resident.otp_code,
            resident.otp_expires_at
        )

        if is_valid:
            # OTP verified - complete login
            session['resident_id'] = resident.id
            session['resident_name'] = resident.full_name
            session.pop('otp_pending_resident_id', None)

            # Clear OTP from database
            resident.otp_code = None
            resident.otp_expires_at = None
            db.session.commit()

            flash(f'Welcome back, {resident.full_name}!', 'success')
            return redirect(url_for('resident_dashboard'))
        else:
            flash(f'Error: {error_message}', 'danger')

    # Get remaining time for OTP
    remaining_time = get_remaining_time(resident.otp_expires_at)

    return render_template('verify_otp.html',
                         resident=resident,
                         remaining_time=remaining_time)


@app.route('/resident/resend-otp', methods=['POST'])
@otp_pending_required
def resend_otp():
    """Resend OTP to user"""
    resident_id = session.get('otp_pending_resident_id')
    resident = Resident.query.get_or_404(resident_id)

    method = resident.otp_method or 'email'

    if method == 'email':
        otp_code = generate_otp(app.config['OTP_LENGTH'])
        resident.otp_code = hash_otp(otp_code)
        resident.otp_expires_at = get_otp_expiry_time(app.config['OTP_EXPIRY_MINUTES'])
        db.session.commit()

        success, message = send_otp_email(resident.email, otp_code, resident.full_name)
        if success:
            flash('OTP resent to your email', 'info')
        else:
            flash(f'Error: {message}', 'danger')
    elif method == 'sms':
        otp_code = generate_otp(app.config['OTP_LENGTH'])
        resident.otp_code = hash_otp(otp_code)
        resident.otp_expires_at = get_otp_expiry_time(app.config['OTP_EXPIRY_MINUTES'])
        db.session.commit()

        success, message = send_otp_sms(resident.phone, otp_code, resident.full_name)
        if success:
            flash('OTP resent via SMS', 'info')
        else:
            flash(f'Error: {message}', 'danger')

    return redirect(url_for('verify_otp'))


@app.route('/resident/setup-otp', methods=['GET', 'POST'])
@login_required
def setup_otp():
    """Setup OTP for resident profile"""
    resident = Resident.query.get(session['resident_id'])

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'enable':
            method = request.form.get('method')
            if method in ['email', 'sms']:
                resident.setup_otp(method)
                db.session.commit()
                flash(f'OTP enabled! You will receive codes via {method} on next login', 'success')
            else:
                flash('Invalid OTP method', 'danger')
        elif action == 'disable':
            resident.disable_otp()
            db.session.commit()
            flash('OTP disabled', 'info')

        return redirect(url_for('edit_profile'))

    return render_template('otp_settings.html', resident=resident)

# ============= ADMIN ROUTES =============

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username == Config.ADMIN_USERNAME and password == Config.ADMIN_PASSWORD:
            session['is_admin'] = True
            session['admin_username'] = username
            flash('Admin login successful!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid admin credentials!', 'danger')
    
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    """Admin dashboard - view all residents"""
    # Get all residents sorted by room number
    residents = Resident.query.order_by(Resident.room_number).all()
    
    # Group by room number for better display
    residents_by_room = {}
    for resident in residents:
        residents_by_room[resident.room_number] = resident
    
    return render_template('admin_dashboard.html', residents=residents, residents_by_room=residents_by_room)

@app.route('/admin/resident/<int:resident_id>')
@admin_required
def admin_view_resident(resident_id):
    """Admin view specific resident"""
    resident = Resident.query.get_or_404(resident_id)
    return render_template('resident_profile.html', resident=resident, is_admin=True)

@app.route('/admin/resident/<int:resident_id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_edit_resident(resident_id):
    """Admin edit resident"""
    resident = Resident.query.get_or_404(resident_id)
    
    if request.method == 'POST':
        try:
            # Admin can update all fields
            resident.full_name = request.form['full_name']
            resident.email = request.form['email']
            resident.phone = request.form['phone']
            resident.date_of_birth = datetime.strptime(request.form['date_of_birth'], '%Y-%m-%d')
            resident.gender = request.form['gender']
            resident.permanent_address = request.form['permanent_address']
            resident.city = request.form['city']
            resident.state = request.form['state']
            resident.pincode = request.form['pincode']
            resident.room_number = request.form['room_number']
            resident.date_of_joining = datetime.strptime(request.form['date_of_joining'], '%Y-%m-%d')
            resident.emergency_contact_name = request.form['emergency_contact_name']
            resident.emergency_contact_phone = request.form['emergency_contact_phone']
            resident.emergency_contact_relation = request.form['emergency_contact_relation']
            
            # Update password if provided
            if request.form.get('new_password'):
                resident.set_password(request.form['new_password'])
            
            db.session.commit()
            flash('Resident updated successfully!', 'success')
            return redirect(url_for('admin_dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Update failed: {str(e)}', 'danger')
    
    return render_template('edit_profile.html', resident=resident, is_admin=True)

@app.route('/admin/resident/<int:resident_id>/delete', methods=['POST'])
@admin_required
def admin_delete_resident(resident_id):
    """Admin delete resident"""
    try:
        resident = Resident.query.get_or_404(resident_id)
        
        # Delete QR code
        delete_qr_code(resident_id)
        
        # Delete from database
        db.session.delete(resident)
        db.session.commit()
        
        flash(f'Resident {resident.full_name} deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Deletion failed: {str(e)}', 'danger')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/logout')
def admin_logout():
    """Admin logout"""
    session.pop('is_admin', None)
    session.pop('admin_username', None)
    flash('Admin logged out successfully!', 'info')
    return redirect(url_for('index'))

# ============= ERROR HANDLERS =============

@app.errorhandler(404)
def not_found(error):
    """404 error handler"""
    return render_template('error.html', error_code=404, error_message='Page not found'), 404

@app.errorhandler(403)
def forbidden(error):
    """403 error handler"""
    return render_template('error.html', error_code=403, error_message='Access forbidden'), 403

@app.errorhandler(500)
def internal_error(error):
    """500 error handler"""
    db.session.rollback()
    return render_template('error.html', error_code=500, error_message='Internal server error'), 500

if __name__ == '__main__':
    app.run(debug=app.config['DEBUG'], 
            host='0.0.0.0', 
            port=int(os.environ.get('FLASK_PORT', 5000))
            )
