from functools import wraps
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from app.models.db import db, User, Resident, Hostel, AuditLog, Notice
from app.utils.otp_generator import generate_otp, hash_otp, validate_otp, get_otp_expiry_time
from app.utils.email_sender import send_otp_email
from app.utils.sms_sender import send_otp_sms
from app.utils.photo_handler import save_photo, validate_photo
from app.utils.qr_generator import generate_qr_code
from app.utils.validators import (
    validate_email, validate_phone, validate_password,
    validate_aadhar, validate_pincode, validate_text_field, collect_errors
)
from app import limiter, oauth

auth_bp = Blueprint('auth', __name__)

def role_required(*roles):
    """Decorator to restrict access to specific roles"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please login to access this page.', 'warning')
                return redirect(url_for('auth.login'))
            
            user = User.query.get(session['user_id'])
            if not user or user.role not in roles:
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('auth.dashboard_redirect'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def login():
    """Unified login portal — Google OAuth 2.0 is the mandatory authentication method."""
    # If already logged in, redirect to respective role dashboard
    if 'user_id' in session:
        return redirect(url_for('auth.dashboard_redirect'))

    if request.method == 'POST':
        # Direct password bypasses are disabled in favor of Google OAuth
        flash('Password-based login is deprecated. Please click "Sign in with Google" below to authenticate securely.', 'info')
        return redirect(url_for('auth.google_login'))

    return render_template('admin_login.html')


@auth_bp.route('/verify-otp', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def send_otp_view():
    """Verify 2FA OTP code page"""
    if 'otp_pending_user_id' not in session:
        return redirect(url_for('auth.login'))

    user = User.query.get(session['otp_pending_user_id'])
    if not user:
        session.pop('otp_pending_user_id', None)
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        otp_code = request.form.get('otp_code', '').strip()
        
        is_valid, error_msg = validate_otp(otp_code, user.otp_code, user.otp_expires_at)
        if is_valid:
            # Login successful, clear OTP state
            session['user_id'] = user.id
            session['user_email'] = user.email
            session['user_role'] = user.role
            session['password_version'] = user.password_version
            session.pop('otp_pending_user_id', None)
            
            # Clear OTP from db
            user.otp_code = None
            user.otp_expires_at = None
            db.session.commit()
            
            log_security_action(user.id, "Completed OTP MFA Verification")
            flash('Verification complete!', 'success')
            return redirect(url_for('auth.dashboard_redirect'))
        else:
            flash(error_msg, 'danger')

    return render_template('verify_otp.html', email=user.email, method=user.otp_method)


@auth_bp.route('/resend-otp', methods=['POST'])
@limiter.limit("3 per minute")
def resend_otp():
    """Resend a new OTP code to user"""
    if 'otp_pending_user_id' not in session:
        return redirect(url_for('auth.login'))

    user = User.query.get(session['otp_pending_user_id'])
    if not user:
        return redirect(url_for('auth.login'))

    # Generate new OTP
    otp_code = generate_otp(6)
    user.otp_code = hash_otp(otp_code)
    user.otp_expires_at = get_otp_expiry_time(10)
    db.session.commit()

    user_name = user.email
    if user.role == 'Resident' and user.resident_profile:
        user_name = user.resident_profile.full_name

    success = False
    if user.otp_method == 'sms' and user.role == 'Resident' and user.resident_profile:
        success, msg = send_otp_sms(user.resident_profile.phone_decrypted, otp_code, user_name)
    else:
        success, msg = send_otp_email(user.email, otp_code, user_name)

    if success:
        flash('A new verification code has been sent.', 'success')
    else:
        flash(f'Failed to send code: {msg}', 'danger')

    return redirect(url_for('auth.send_otp_view'))


@auth_bp.route('/register', methods=['GET', 'POST'])
@limiter.limit("5 per hour")
def register():
    """Resident registration page"""
    if 'user_id' in session:
        return redirect(url_for('auth.dashboard_redirect'))

    hostels = Hostel.query.all()
    hostel_code = request.args.get('hostel_code', '').strip().upper()
    hostel_id = request.args.get('hostel_id', '').strip()
    if hostel_id and not hostel_code:
        hostel_obj = Hostel.query.get(hostel_id)
        if hostel_obj:
            hostel_code = hostel_obj.hostel_code

    prefilled_hostel = None
    if hostel_code:
        prefilled_hostel = Hostel.query.filter_by(hostel_code=hostel_code).first()

    def render_register_form(**kwargs):
        return render_template(
            'register.html',
            hostels=hostels,
            hostel_code=hostel_code,
            prefilled_hostel=prefilled_hostel,
            **kwargs
        )

    if request.method == 'POST':
        hostel_code = request.form.get('hostel_code', '').strip().upper()
        # Re-fetch prefilled_hostel in case hostel_code was sent on post
        if hostel_code:
            prefilled_hostel = Hostel.query.filter_by(hostel_code=hostel_code).first()

        try:
            email    = request.form.get('email', '').strip()
            phone    = request.form.get('phone', '').strip()
            password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '')
            full_name = request.form.get('full_name', '').strip()
            pincode   = request.form.get('pincode', '').strip()
            aadhar_raw = request.form.get('aadhar_id', '').replace('-', '').strip()

            # ── Server-Side Field Validation ──────────────────
            field_errors = collect_errors(
                validate_text_field(full_name, 'Full name', 100),
                validate_email(email),
                validate_phone(phone),
                validate_password(password),
                validate_pincode(pincode),
                validate_aadhar(aadhar_raw),
            )
            if field_errors:
                for err in field_errors:
                    flash(err, 'danger')
                return render_register_form()

            if not hostel_code:
                flash('Unique Hostel Code is required to register.', 'danger')
                return render_register_form()

            if password != confirm_password:
                flash('Passwords do not match.', 'danger')
                return render_register_form()

            # Check if email is already taken
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                flash('Email is already registered.', 'danger')
                return render_register_form(clear_email=True)

            # Resolve hostel by unique code
            hostel = Hostel.query.filter_by(hostel_code=hostel_code).first()
            if not hostel:
                flash(f'Unique Hostel Code "{hostel_code}" not found. Please verify the code and try again.', 'danger')
                return render_register_form()
            hostel_id = hostel.id

            # Check phone uniqueness
            all_residents = Resident.query.all()
            for r in all_residents:
                if r.phone_decrypted == phone:
                    flash('Phone number is already registered.', 'danger')
                    return render_register_form(clear_phone=True)

            # Parse DOB and Joining Date
            dob = datetime.strptime(request.form['date_of_birth'], '%Y-%m-%d').date()
            doj = datetime.strptime(request.form['date_of_joining'], '%Y-%m-%d').date()

            # Format Aadhar
            aadhar_formatted = None
            if aadhar_raw:
                if aadhar_raw.isdigit() and len(aadhar_raw) == 12:
                    aadhar_formatted = f"{aadhar_raw[:4]}-{aadhar_raw[4:8]}-{aadhar_raw[8:12]}"
                else:
                    flash('Aadhar ID must be exactly 12 digits.', 'warning')
                    return render_register_form(clear_aadhar=True)

            # Create User login entry
            user = User(email=email, role='Resident')
            user.set_password(password)
            db.session.add(user)
            db.session.commit()

            # Create Resident Profile linked to User
            resident = Resident(
                user_id=user.id,
                hostel_id=hostel_id,
                full_name=request.form['full_name'],
                date_of_birth=dob,
                gender=request.form['gender'],
                city=request.form['city'],
                state=request.form['state'],
                pincode=request.form['pincode'],
                room_number="Pending",
                rent=0.0,
                electricity_bill=0.0,
                date_of_joining=doj,
                emergency_contact_name=request.form['emergency_contact_name'],
                emergency_contact_phone=request.form['emergency_contact_phone'],
                emergency_contact_relation=request.form['emergency_contact_relation'],
                guardian_name=request.form.get('guardian_name') or None,
                guardian_phone=request.form.get('guardian_phone') or None,
                guardian_email=request.form.get('guardian_email') or None,
                guardian_relation=request.form.get('guardian_relation') or None,
                emergency_contact_address=request.form.get('emergency_contact_address') or None
            )
            # Use encrypted setters
            resident.phone_decrypted = phone
            resident.permanent_address_decrypted = request.form['permanent_address']
            if aadhar_formatted:
                resident.aadhar_id_decrypted = aadhar_formatted

            db.session.add(resident)
            db.session.commit()

            # Photo upload (optional)
            photo_file = request.files.get('profile_photo')
            if photo_file and photo_file.filename:
                is_valid, error_msg = validate_photo(photo_file)
                if not is_valid:
                    flash(f'Photo upload skipped: {error_msg}', 'warning')
                else:
                    success, err = save_photo(photo_file, resident.id, db, resident)
                    if not success:
                        flash(f'Photo upload skipped: {err}', 'warning')

            # Generate profile QR code
            generate_qr_code(resident.id)
            
            log_security_action(user.id, "Registered new resident account")
            flash('Registration successful! You can now login.', 'success')
            return redirect(url_for('auth.login'))

        except Exception as e:
            db.session.rollback()
            flash(f'Registration failed: {str(e)}', 'danger')

    return render_register_form()


@auth_bp.route('/register/owner', methods=['GET', 'POST'])
@limiter.limit("5 per hour")
def register_owner():
    """Public self-registration page for Hostel Owners"""
    if 'user_id' in session:
        return redirect(url_for('auth.dashboard_redirect'))

    if request.method == 'POST':
        email    = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        full_name = request.form.get('full_name', '').strip()
        phone     = request.form.get('phone', '').strip()

        # Server-side validation
        field_errors = collect_errors(
            validate_text_field(full_name, 'Full name', 100),
            validate_email(email),
            validate_phone(phone),
            validate_password(password),
        )
        if field_errors:
            for err in field_errors:
                flash(err, 'danger')
            return render_template('owner_register.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('owner_register.html')

        existing = User.query.filter_by(email=email).first()
        if existing:
            flash('This email is already registered.', 'danger')
            return render_template('owner_register.html')

        owner = User(email=email, role='HostelOwner', full_name=full_name, phone=phone)
        owner.set_password(password)
        db.session.add(owner)
        db.session.commit()

        log_security_action(owner.id, "Self-registered as HostelOwner")
        flash('Owner account created! You can now log in. A SuperAdmin will assign your hostel.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('owner_register.html')


@auth_bp.route('/register/shop', methods=['GET', 'POST'])
@limiter.limit("10 per hour")
def register_shop():
    """ShopOwner self-registration page — account is Pending admin approval"""
    if 'user_id' in session:
        return redirect(url_for('auth.dashboard_redirect'))

    if request.method == 'POST':
        email     = request.form.get('email', '').strip()
        full_name = request.form.get('full_name', '').strip()
        phone     = request.form.get('phone', '').strip()
        password  = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Server-side validation
        field_errors = collect_errors(
            validate_text_field(full_name, 'Full name', 100),
            validate_email(email),
            validate_phone(phone),
            validate_password(password),
        )
        if field_errors:
            for err in field_errors:
                flash(err, 'danger')
            return render_template('register_shop.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('register_shop.html')

        if User.query.filter_by(email=email).first():
            flash('This email is already registered.', 'danger')
            return render_template('register_shop.html')

        shop_owner = User(email=email, role='ShopOwner', full_name=full_name, phone=phone)
        shop_owner.set_password(password)
        db.session.add(shop_owner)
        db.session.commit()

        log_security_action(shop_owner.id, "Self-registered as ShopOwner")
        flash('Shop owner account created! Log in and then complete your shop profile — a SuperAdmin will review and approve it.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register_shop.html')


@auth_bp.route('/hostels')
def hostel_discovery():
    """Public hostel discovery page — card view of all registered hostels"""
    search = request.args.get('q', '').strip().lower()
    hostels = Hostel.query.all()
    if search:
        hostels = [
            h for h in hostels
            if search in h.hostel_name.lower()
            or search in h.location.lower()
            or (h.hostel_code and search in h.hostel_code.lower())
            or (h.facilities and search in h.facilities.lower())
            or (h.owner and search in h.owner.email.lower())
        ]
    return render_template('hostel_discovery.html', hostels=hostels, search=search)


@auth_bp.route('/logout')
def logout():
    """Clear session logs and logout"""
    user_id = session.get('user_id')
    if user_id:
        log_security_action(user_id, "Logged out")
    session.clear()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('auth.login'))


@auth_bp.route('/dashboard')
def dashboard_redirect():
    """Helper route to redirect authenticated users to their roles"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    user = User.query.get(session['user_id'])
    if user:
        if user.role == 'SuperAdmin':
            return redirect(url_for('admin.dashboard'))
        elif user.role == 'HostelOwner':
            return redirect(url_for('owner.dashboard'))
        elif user.role == 'Resident':
            return redirect(url_for('resident.dashboard'))
        elif user.role == 'ShopOwner':
            return redirect(url_for('pharmacy.shop_dashboard'))

    session.clear()
    return redirect(url_for('auth.login'))


def log_security_action(user_id, action):
    """Write action audit entry to database"""
    try:
        ip = request.remote_addr
        log_entry = AuditLog(user_id=user_id, action=action, ip_address=ip)
        db.session.add(log_entry)
        db.session.commit()
    except Exception as e:
        print(f"Failed to write audit log: {str(e)}")


@auth_bp.route('/secure-receipt/<filename>')
def serve_secure_receipt(filename):
    """Serve payment receipts securely after validating session or JWT authorization."""
    import os
    from flask import abort, send_from_directory, current_app
    from app.models.db import Payment, Hostel, Resident, User

    user = None

    # ── Try Flask session first (web portal) ────────────────────
    if 'user_id' in session:
        user = User.query.get(session['user_id'])

    # ── Fallback: try JWT Bearer token (mobile app) ─────────────
    if user is None:
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
            try:
                import jwt as pyjwt
                secret = current_app.config.get('JWT_SECRET_KEY') or current_app.config.get('SECRET_KEY')
                payload = pyjwt.decode(token, secret, algorithms=['HS256'])
                user = User.query.get(payload.get('user_id'))
            except Exception:
                pass

    if not user:
        abort(403)

    # Query database to check if payment exists
    payment = Payment.query.filter(Payment.screenshot_path.like(f"%{filename}")).first_or_404()

    # Authorize access based on user role
    authorized = False
    if user.role == 'SuperAdmin':
        authorized = True
    elif user.role == 'HostelOwner':
        # Owner is authorized if they manage the hostel associated with this payment
        hostel = Hostel.query.filter_by(id=payment.hostel_id, owner_id=user.id).first()
        if hostel:
            authorized = True
    elif user.role == 'Resident':
        resident = Resident.query.filter_by(user_id=user.id).first()
        if resident and payment.resident_id == resident.id:
            authorized = True

    if not authorized:
        abort(403)

    directory = os.path.join(current_app.instance_path, 'uploads', 'payments')
    return send_from_directory(directory, filename)



@auth_bp.route('/login/google')
@limiter.limit("10 per minute")
def google_login():
    """Redirect to Google OAuth 2.0 Auth Server"""
    # Google OAuth 2.0 policy forbids private LAN IPs (e.g. 10.x.x.x, 192.168.x.x).
    # We normalize the redirect URI to a valid loopback URI or configured BASE_URL.
    base_url = (current_app.config.get('BASE_URL') or '').strip().rstrip('/')
    host = request.host.split(':')[0]
    is_private_ip = (
        host.startswith('10.') or 
        host.startswith('192.168.') or 
        (host.startswith('172.') and host.split('.')[1].isdigit() and 16 <= int(host.split('.')[1]) <= 31)
    )

    if is_private_ip:
        if base_url and not any(base_url.startswith(f"http://{p}") for p in ['10.', '192.168.']):
            redirect_uri = f"{base_url}/login/google/callback"
        else:
            port = request.host.split(':')[1] if ':' in request.host else '5000'
            redirect_uri = f"http://127.0.0.1:{port}/login/google/callback"
    else:
        redirect_uri = url_for('auth.google_authorize', _external=True)

    return oauth.google.authorize_redirect(redirect_uri)


@auth_bp.route('/login/google/callback')
@limiter.limit("10 per minute")
def google_authorize():
    """Google OAuth callback, logins user if registered"""
    try:
        token = oauth.google.authorize_access_token()
        user_info = token.get('userinfo')
    except Exception as e:
        flash(f'Google authentication failed: {str(e)}', 'danger')
        return redirect(url_for('auth.login'))

    if not user_info:
        flash('Failed to retrieve user info from Google.', 'danger')
        return redirect(url_for('auth.login'))

    email = user_info.get('email')
    if not email:
        flash('Google account does not provide an email address.', 'danger')
        return redirect(url_for('auth.login'))

    # Check if the user exists in our local database (case-insensitive)
    user = User.query.filter(User.email.ilike(email)).first()
    if not user:
        if email == 'pranjalshukla2222@gmail.com':
            # Auto-provision primary SuperAdmin
            user = User(
                email=email,
                role='SuperAdmin',
                full_name='Pranjal Shukla (SuperAdmin)',
                otp_enabled=True,
                otp_method='email'
            )
            user.set_password('Admin@12345')
            db.session.add(user)
            db.session.commit()
        else:
            flash(f'The Google account {email} is not registered in the system. Please register first or contact your hostel manager.', 'danger')
            return redirect(url_for('auth.login'))

    # If pranjalshukla2222@gmail.com logs in, guarantee SuperAdmin role
    if email == 'pranjalshukla2222@gmail.com' and user.role != 'SuperAdmin':
        user.role = 'SuperAdmin'
        db.session.commit()

    # Google Sign-in serves as high-assurance MFA. Establish verified session.
    session['user_id'] = user.id
    session['user_email'] = user.email
    session['user_role'] = user.role
    session['password_version'] = user.password_version

    log_security_action(user.id, f"Logged in via Google OAuth 2.0 as {user.role}")
    flash(f'Welcome back, {user.full_name or user.email}!', 'success')
    return redirect(url_for('auth.dashboard_redirect'))


@auth_bp.route('/hostel/view/<int:hostel_id>')
def hostel_view(hostel_id):
    """Dynamic public page showing hostel details and registration button"""
    hostel = Hostel.query.get_or_404(hostel_id)
    return render_template('hostel_detail.html', hostel=hostel)


@auth_bp.route('/profile/<int:resident_id>')
def public_profile(resident_id):
    """Public secure verification page for a resident, scanned via ID QR code"""
    resident = Resident.query.get_or_404(resident_id)
    return render_template(
        'resident_profile.html',
        resident=resident,
        hostel_notices=[],
        is_public=True
    )

