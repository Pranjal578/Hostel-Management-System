"""
ROOMMET Mobile API — JWT-authenticated REST endpoints for the Flutter app.
All existing web routes (session-based) are untouched.
URL prefix: /api/mobile/
"""
import os
import base64
from datetime import datetime, timedelta, timezone
from functools import wraps

import jwt
from flask import Blueprint, jsonify, request, current_app, send_from_directory
from werkzeug.utils import secure_filename

from app.models.db import (
    db, User, Resident, Hostel, Payment, Notice, Message,
    AuditLog, Shop, Medicine, MedicineOrder, MedicineReview
)

mobile_api_bp = Blueprint('mobile_api', __name__)

# ─────────────────────────────────────────────────────────────────
# JWT Helpers
# ─────────────────────────────────────────────────────────────────

def _get_jwt_secret():
    return current_app.config.get('JWT_SECRET_KEY') or current_app.config.get('SECRET_KEY')


def _create_token(user: User) -> str:
    """Mint a signed JWT for the given user. Expires in 7 days."""
    payload = {
        'user_id': user.id,
        'role': user.role,
        'password_version': user.password_version,
        'exp': datetime.now(timezone.utc) + timedelta(days=7),
        'iat': datetime.now(timezone.utc),
    }
    return jwt.encode(payload, _get_jwt_secret(), algorithm='HS256')


def jwt_required(f):
    """Decorator: validates Bearer JWT, injects current_user into kwargs."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing or invalid Authorization header.'}), 401
        token = auth_header[7:]
        try:
            payload = jwt.decode(token, _get_jwt_secret(), algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired. Please log in again.'}), 401
        except jwt.InvalidTokenError as e:
            return jsonify({'error': f'Invalid token: {str(e)}'}), 401

        user = User.query.get(payload['user_id'])
        if not user:
            return jsonify({'error': 'User not found.'}), 401
        # Invalidate token if password was changed
        if user.password_version != payload.get('password_version'):
            return jsonify({'error': 'Token invalidated due to password change. Please log in again.'}), 401

        kwargs['current_user'] = user
        return f(*args, **kwargs)
    return decorated


def role_required_jwt(*roles):
    """Decorator: combines jwt_required + role check."""
    def decorator(f):
        @jwt_required
        @wraps(f)
        def decorated(*args, **kwargs):
            user = kwargs.get('current_user')
            if user.role not in roles:
                return jsonify({'error': 'Forbidden: insufficient role.'}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator


def _log(user_id, action):
    try:
        log = AuditLog(user_id=user_id, action=action, ip_address=request.remote_addr)
        db.session.add(log)
        db.session.commit()
    except Exception:
        pass


# ─────────────────────────────────────────────────────────────────
# AUTH Endpoints
# ─────────────────────────────────────────────────────────────────

@mobile_api_bp.route('/auth/login', methods=['POST'])
def mobile_login():
    """Email + password login → returns JWT access_token."""
    data = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip()
    password = data.get('password') or ''

    if not email or not password:
        return jsonify({'error': 'Email and password are required.'}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid email or password.'}), 401

    # If OTP is enabled, signal the client to prompt for OTP
    if user.is_otp_enabled():
        from app.utils.otp_generator import generate_otp, hash_otp, get_otp_expiry_time
        from app.utils.email_sender import send_otp_email
        otp_code = generate_otp(6)
        user.otp_code = hash_otp(otp_code)
        user.otp_expires_at = get_otp_expiry_time(10)
        db.session.commit()
        user_name = user.full_name or user.email
        send_otp_email(user.email, otp_code, user_name)
        return jsonify({'otp_required': True, 'email': user.email}), 200

    token = _create_token(user)
    _log(user.id, 'Mobile login (email/password)')
    return jsonify({'access_token': token, 'role': user.role}), 200


@mobile_api_bp.route('/auth/google', methods=['POST'])
def mobile_google_login():
    """Verify Google OAuth id_token or access_token and return JWT access_token."""
    data = request.get_json(silent=True) or {}
    id_token = data.get('id_token')
    access_token = data.get('access_token')

    if not id_token and not access_token:
        return jsonify({'error': 'Google authentication token is required.'}), 400

    import requests
    try:
        email = None
        # 1. Try id_token if provided
        if id_token:
            res = requests.get(
                f'https://oauth2.googleapis.com/tokeninfo?id_token={id_token}',
                timeout=10
            )
            if res.status_code == 200:
                token_info = res.json()
                email = token_info.get('email')

        # 2. Try access_token if email was not retrieved from id_token
        if not email and access_token:
            res = requests.get(
                f'https://oauth2.googleapis.com/tokeninfo?access_token={access_token}',
                timeout=10
            )
            if res.status_code == 200:
                token_info = res.json()
                email = token_info.get('email')
            
            # Fallback to Google userinfo endpoint
            if not email:
                userinfo_res = requests.get(
                    'https://www.googleapis.com/oauth2/v3/userinfo',
                    headers={'Authorization': f'Bearer {access_token}'},
                    timeout=10
                )
                if userinfo_res.status_code == 200:
                    user_info = userinfo_res.json()
                    email = user_info.get('email')

        if not email:
            return jsonify({'error': 'Invalid Google token or expired session.'}), 400

        # Check if the user exists in database (case-insensitive)
        user = User.query.filter(User.email.ilike(email)).first()
        if not user:
            return jsonify({
                'error': f'The email {email} is not registered in ROOMMET. Please register first or contact your admin.'
            }), 403

        # Success! Mint and return JWT token
        token = _create_token(user)
        _log(user.id, 'Mobile login via Google OAuth')
        return jsonify({'access_token': token, 'role': user.role, 'email': user.email}), 200

    except requests.RequestException as e:
        return jsonify({'error': f'Failed to contact Google verification server: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'Google authentication failed: {str(e)}'}), 500


@mobile_api_bp.route('/auth/verify-otp', methods=['POST'])
def mobile_verify_otp():
    """Verify OTP after password login → returns JWT."""
    from app.utils.otp_generator import validate_otp
    data = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip()
    otp_code = (data.get('otp_code') or '').strip()

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'error': 'User not found.'}), 404

    is_valid, error_msg = validate_otp(otp_code, user.otp_code, user.otp_expires_at)
    if not is_valid:
        return jsonify({'error': error_msg}), 401

    user.otp_code = None
    user.otp_expires_at = None
    db.session.commit()

    token = _create_token(user)
    _log(user.id, 'Mobile login completed OTP MFA')
    return jsonify({'access_token': token, 'role': user.role}), 200


@mobile_api_bp.route('/auth/me', methods=['GET'])
@jwt_required
def mobile_me(current_user):
    """Return current user's role, name, and profile completeness."""
    profile_complete = True
    profile_data = {}

    if current_user.role == 'Resident':
        r = current_user.resident_profile
        profile_complete = r is not None and r.status != 'Pending'
        if r:
            profile_data = {
                'full_name': r.full_name,
                'hostel_name': r.hostel.hostel_name if r.hostel else None,
                'status': r.status,
                'room_number': r.room_number,
            }
    elif current_user.role == 'HostelOwner':
        profile_data = {
            'full_name': current_user.full_name,
            'hostel_count': len(current_user.hostels),
        }
    elif current_user.role == 'ShopOwner':
        shop = Shop.query.filter_by(owner_id=current_user.id).first()
        profile_complete = shop is not None and shop.verification_status == 'Approved'
        profile_data = {
            'full_name': current_user.full_name,
            'shop_status': shop.verification_status if shop else 'None',
        }

    return jsonify({
        'id': current_user.id,
        'email': current_user.email,
        'role': current_user.role,
        'profile_complete': profile_complete,
        **profile_data,
    }), 200


# ─────────────────────────────────────────────────────────────────
# RESIDENT Endpoints
# ─────────────────────────────────────────────────────────────────

@mobile_api_bp.route('/resident/profile', methods=['GET'])
@jwt_required
def resident_profile(current_user):
    if current_user.role != 'Resident':
        return jsonify({'error': 'Forbidden'}), 403
    r = current_user.resident_profile
    if not r:
        return jsonify({'error': 'Resident profile not found.'}), 404

    hostel = r.hostel
    return jsonify({
        'id': r.id,
        'user_id': r.user_id,
        'full_name': r.full_name,
        'email': current_user.email,
        'phone': r.phone_decrypted,
        'gender': r.gender,
        'date_of_birth': r.date_of_birth.strftime('%Y-%m-%d') if r.date_of_birth else None,
        'permanent_address': r.permanent_address_decrypted,
        'city': r.city,
        'state': r.state,
        'pincode': r.pincode,
        'room_number': r.room_number,
        'date_of_joining': r.date_of_joining.strftime('%Y-%m-%d') if r.date_of_joining else None,
        'rent': r.rent,
        'electricity_bill': r.electricity_bill,
        'status': r.status,
        'aadhar_masked': r.mask_aadhar(),
        'emergency_contact_name': r.emergency_contact_name,
        'emergency_contact_phone': r.emergency_contact_phone,
        'emergency_contact_relation': r.emergency_contact_relation,
        'guardian_name': r.guardian_name,
        'guardian_phone': r.guardian_phone,
        'guardian_email': r.guardian_email,
        'profile_image': r.profile_image,
        'payment_status': r.payment_status,
        'hostel': {
            'id': hostel.id,
            'name': hostel.hostel_name,
            'location': hostel.location,
            'code': hostel.hostel_code,
            'facilities': hostel.facilities_list,
        } if hostel else None,
    }), 200


@mobile_api_bp.route('/resident/qr', methods=['GET'])
@jwt_required
def resident_qr(current_user):
    """Return resident QR code as base64 PNG."""
    if current_user.role != 'Resident':
        return jsonify({'error': 'Forbidden'}), 403
    r = current_user.resident_profile
    if not r:
        return jsonify({'error': 'Profile not found'}), 404

    qr_path = os.path.join(current_app.root_path, 'static', 'qr', f'resident_{r.id}.png')
    if not os.path.exists(qr_path):
        from app.utils.qr_generator import generate_qr_code
        generate_qr_code(r.id)

    if os.path.exists(qr_path):
        with open(qr_path, 'rb') as f:
            b64 = base64.b64encode(f.read()).decode('utf-8')
        return jsonify({'qr_base64': b64, 'resident_id': r.id}), 200

    return jsonify({'error': 'QR code unavailable'}), 404


@mobile_api_bp.route('/resident/payments', methods=['GET'])
@jwt_required
def resident_payments(current_user):
    if current_user.role != 'Resident':
        return jsonify({'error': 'Forbidden'}), 403
    r = current_user.resident_profile
    if not r:
        return jsonify({'error': 'Profile not found'}), 404

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    pagination = Payment.query.filter_by(resident_id=r.id)\
        .order_by(Payment.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'payments': [{
            'id': p.id,
            'amount': p.amount,
            'payment_date': p.payment_date.strftime('%Y-%m-%d'),
            'transaction_id': p.transaction_id,
            'status': p.status,
            'screenshot_path': p.screenshot_path,
            'created_at': p.created_at.strftime('%Y-%m-%d %H:%M'),
        } for p in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'page': page,
    }), 200


@mobile_api_bp.route('/resident/payments', methods=['POST'])
@jwt_required
def resident_submit_payment(current_user):
    """Upload a new payment receipt (multipart/form-data)."""
    if current_user.role != 'Resident':
        return jsonify({'error': 'Forbidden'}), 403
    r = current_user.resident_profile
    if not r:
        return jsonify({'error': 'Profile not found'}), 404

    amount = request.form.get('amount', type=float)
    transaction_id = (request.form.get('transaction_id') or '').strip()
    payment_date_str = request.form.get('payment_date', '')
    receipt_file = request.files.get('receipt')

    if not all([amount, transaction_id, payment_date_str, receipt_file]):
        return jsonify({'error': 'amount, transaction_id, payment_date and receipt file are required.'}), 400

    try:
        payment_date = datetime.strptime(payment_date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'payment_date must be YYYY-MM-DD format.'}), 400

    # Save receipt securely (strip EXIF if image)
    import uuid
    from PIL import Image
    from io import BytesIO

    filename = f"{uuid.uuid4().hex}_{secure_filename(receipt_file.filename)}"
    upload_dir = os.path.join(current_app.instance_path, 'uploads', 'payments')
    os.makedirs(upload_dir, exist_ok=True)
    filepath = os.path.join(upload_dir, filename)

    ext = os.path.splitext(filename)[1].lower()
    if ext in ['.jpg', '.jpeg', '.png', '.webp']:
        try:
            img = Image.open(receipt_file)
            # Strip EXIF by re-saving
            clean = Image.new(img.mode, img.size)
            clean.putdata(list(img.getdata()))
            clean.save(filepath)
        except Exception:
            receipt_file.seek(0)
            receipt_file.save(filepath)
    else:
        receipt_file.save(filepath)

    payment = Payment(
        resident_id=r.id,
        hostel_id=r.hostel_id,
        amount=amount,
        payment_date=payment_date,
        transaction_id=transaction_id,
        screenshot_path=f'/secure-receipt/{filename}',
        status='Pending',
    )
    db.session.add(payment)
    db.session.commit()

    _log(current_user.id, f'Mobile: submitted payment ₹{amount}')
    return jsonify({'message': 'Payment submitted successfully.', 'payment_id': payment.id}), 201


@mobile_api_bp.route('/resident/notices', methods=['GET'])
@jwt_required
def resident_notices(current_user):
    if current_user.role != 'Resident':
        return jsonify({'error': 'Forbidden'}), 403
    r = current_user.resident_profile
    if not r:
        return jsonify({'error': 'Profile not found'}), 404

    notices = Notice.query.filter_by(hostel_id=r.hostel_id)\
        .order_by(Notice.created_at.desc()).limit(50).all()
    return jsonify([{
        'id': n.id,
        'title': n.title,
        'message': n.message,
        'created_at': n.created_at.strftime('%Y-%m-%d %H:%M'),
    } for n in notices]), 200


# ─────────────────────────────────────────────────────────────────
# CHAT Endpoints (Resident ↔ Owner)
# ─────────────────────────────────────────────────────────────────

@mobile_api_bp.route('/chat/<int:recipient_id>', methods=['GET'])
@jwt_required
def get_messages(current_user, recipient_id):
    """Fetch message thread between current user and recipient."""
    messages = Message.query.filter(
        ((Message.sender_id == current_user.id) & (Message.receiver_id == recipient_id)) |
        ((Message.sender_id == recipient_id) & (Message.receiver_id == current_user.id))
    ).order_by(Message.created_at.asc()).all()

    unread = [m for m in messages if m.receiver_id == current_user.id and not m.is_read]
    for m in unread:
        m.is_read = True
    if unread:
        db.session.commit()

    return jsonify([{
        'id': m.id,
        'sender_id': m.sender_id,
        'receiver_id': m.receiver_id,
        'message_content': m.message_content,
        'created_at': m.created_at.strftime('%Y-%m-%d %H:%M'),
        'is_read': m.is_read,
    } for m in messages]), 200


@mobile_api_bp.route('/chat/<int:recipient_id>', methods=['POST'])
@jwt_required
def send_message(current_user, recipient_id):
    """Send a message to a recipient."""
    data = request.get_json(silent=True) or {}
    content = (data.get('message_content') or '').strip()
    if not content:
        return jsonify({'error': 'Message content cannot be empty.'}), 400

    recipient = User.query.get(recipient_id)
    if not recipient:
        return jsonify({'error': 'Recipient not found.'}), 404

    msg = Message(
        sender_id=current_user.id,
        receiver_id=recipient_id,
        message_content=content,
    )
    db.session.add(msg)
    db.session.commit()

    return jsonify({
        'id': msg.id,
        'sender_id': msg.sender_id,
        'receiver_id': msg.receiver_id,
        'message_content': msg.message_content,
        'created_at': msg.created_at.strftime('%Y-%m-%d %H:%M'),
        'is_read': msg.is_read,
    }), 201


@mobile_api_bp.route('/chat/contacts', methods=['GET'])
@jwt_required
def chat_contacts(current_user):
    """Return list of people the current user can chat with."""
    contacts = []
    if current_user.role == 'Resident':
        r = current_user.resident_profile
        if r and r.hostel:
            owner = User.query.get(r.hostel.owner_id)
            if owner:
                contacts.append({
                    'user_id': owner.id,
                    'name': owner.full_name or owner.email,
                    'role': owner.role,
                })
    elif current_user.role == 'HostelOwner':
        for hostel in current_user.hostels:
            for resident in hostel.residents:
                if resident.user:
                    unread = Message.query.filter_by(
                        sender_id=resident.user_id,
                        receiver_id=current_user.id,
                        is_read=False
                    ).count()
                    contacts.append({
                        'user_id': resident.user_id,
                        'name': resident.full_name,
                        'role': 'Resident',
                        'hostel': hostel.hostel_name,
                        'room': resident.room_number,
                        'unread_count': unread,
                    })
    return jsonify(contacts), 200


# ─────────────────────────────────────────────────────────────────
# OWNER Endpoints
# ─────────────────────────────────────────────────────────────────

@mobile_api_bp.route('/owner/dashboard', methods=['GET'])
@jwt_required
def owner_dashboard(current_user):
    if current_user.role != 'HostelOwner':
        return jsonify({'error': 'Forbidden'}), 403

    hostels = current_user.hostels
    hostel_ids = [h.id for h in hostels]
    total_residents = sum(len(h.residents) for h in hostels)
    active_residents = sum(1 for h in hostels for r in h.residents if r.status == 'Active')
    total_capacity = sum(h.total_capacity for h in hostels)
    occupied_rooms = sum(1 for h in hostels for r in h.residents if r.status == 'Active' and r.room_number) or active_residents
    capacity_left = max(0, total_capacity - active_residents)
    
    total_pending_payments = sum(h.pending_payments_count for h in hostels)
    pending_approvals = sum(
        1 for h in hostels for r in h.residents if r.status == 'Pending'
    )
    
    total_rent_collected = float(db.session.query(db.func.sum(Payment.amount)).filter(
        Payment.hostel_id.in_(hostel_ids), Payment.status == 'Verified'
    ).scalar() or 0.0) if hostel_ids else 0.0
    
    total_pending_rent = float(db.session.query(db.func.sum(Payment.amount)).filter(
        Payment.hostel_id.in_(hostel_ids), Payment.status == 'Pending'
    ).scalar() or 0.0) if hostel_ids else 0.0

    return jsonify({
        'hostel_count': len(hostels),
        'total_residents': total_residents,
        'active_residents': active_residents,
        'total_capacity': total_capacity,
        'occupied_rooms': occupied_rooms,
        'capacity_left': capacity_left,
        'pending_payments': total_pending_payments,
        'pending_approvals': pending_approvals,
        'total_rent_collected': total_rent_collected,
        'total_pending_rent': total_pending_rent,
        'hostels': [{
            'id': h.id,
            'name': h.hostel_name,
            'location': h.location,
            'code': h.hostel_code,
            'capacity': h.total_capacity,
            'available_rooms': h.available_rooms,
            'resident_count': len(h.residents),
            'facilities': h.facilities_list,
        } for h in hostels],
    }), 200


@mobile_api_bp.route('/owner/residents', methods=['GET'])
@jwt_required
def owner_residents(current_user):
    if current_user.role != 'HostelOwner':
        return jsonify({'error': 'Forbidden'}), 403

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    hostel_id = request.args.get('hostel_id', type=int)
    search = request.args.get('q', '').strip()
    status_filter = request.args.get('status', '')

    owner_hostel_ids = [h.id for h in current_user.hostels]

    query = Resident.query.filter(Resident.hostel_id.in_(owner_hostel_ids))
    if hostel_id and hostel_id in owner_hostel_ids:
        query = query.filter_by(hostel_id=hostel_id)
    if search:
        query = query.filter(
            (Resident.full_name.ilike(f'%{search}%')) |
            (Resident.room_number.ilike(f'%{search}%'))
        )
    if status_filter:
        query = query.filter_by(status=status_filter)

    pagination = query.order_by(Resident.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'residents': [{
            'id': r.id,
            'full_name': r.full_name,
            'email': r.user.email if r.user else None,
            'room_number': r.room_number,
            'status': r.status,
            'hostel_id': r.hostel_id,
            'hostel_name': r.hostel.hostel_name if r.hostel else None,
            'payment_status': r.payment_status,
            'date_of_joining': r.date_of_joining.strftime('%Y-%m-%d') if r.date_of_joining else None,
        } for r in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'page': page,
    }), 200


@mobile_api_bp.route('/owner/residents/<int:resident_id>/approve', methods=['POST'])
@jwt_required
def owner_approve_resident(current_user, resident_id):
    if current_user.role != 'HostelOwner':
        return jsonify({'error': 'Forbidden'}), 403

    r = Resident.query.get_or_404(resident_id)
    owner_hostel_ids = [h.id for h in current_user.hostels]
    if r.hostel_id not in owner_hostel_ids:
        return jsonify({'error': 'Access denied.'}), 403

    data = request.get_json(silent=True) or {}
    room_number = (data.get('room_number') or '').strip()

    r.status = 'Active'
    if room_number:
        r.room_number = room_number
    if r.hostel:
        r.rent = r.hostel.rent
        r.electricity_bill = r.hostel.electricity_bill
    db.session.commit()

    _log(current_user.id, f'Mobile: approved resident {r.full_name} (id={r.id})')
    return jsonify({'message': f'Resident {r.full_name} approved.'}), 200


@mobile_api_bp.route('/owner/residents/<int:resident_id>/reject', methods=['POST'])
@jwt_required
def owner_reject_resident(current_user, resident_id):
    if current_user.role != 'HostelOwner':
        return jsonify({'error': 'Forbidden'}), 403

    r = Resident.query.get_or_404(resident_id)
    owner_hostel_ids = [h.id for h in current_user.hostels]
    if r.hostel_id not in owner_hostel_ids:
        return jsonify({'error': 'Access denied.'}), 403

    r.status = 'Rejected'
    db.session.commit()
    _log(current_user.id, f'Mobile: rejected resident {r.full_name} (id={r.id})')
    return jsonify({'message': f'Resident {r.full_name} rejected.'}), 200


@mobile_api_bp.route('/owner/payments', methods=['GET'])
@jwt_required
def owner_payments(current_user):
    if current_user.role != 'HostelOwner':
        return jsonify({'error': 'Forbidden'}), 403

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status_filter = request.args.get('status', 'Pending')
    owner_hostel_ids = [h.id for h in current_user.hostels]

    query = Payment.query.filter(Payment.hostel_id.in_(owner_hostel_ids))
    if status_filter:
        query = query.filter_by(status=status_filter)
    pagination = query.order_by(Payment.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'payments': [{
            'id': p.id,
            'amount': p.amount,
            'payment_date': p.payment_date.strftime('%Y-%m-%d'),
            'transaction_id': p.transaction_id,
            'status': p.status,
            'screenshot_path': p.screenshot_path,
            'resident_name': p.resident.full_name if p.resident else None,
            'resident_id': p.resident_id,
            'hostel_name': p.hostel.hostel_name if p.hostel else None,
            'created_at': p.created_at.strftime('%Y-%m-%d %H:%M'),
        } for p in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'page': page,
    }), 200


@mobile_api_bp.route('/owner/payments/<int:payment_id>/verify', methods=['POST'])
@jwt_required
def owner_verify_payment(current_user, payment_id):
    if current_user.role != 'HostelOwner':
        return jsonify({'error': 'Forbidden'}), 403

    p = Payment.query.get_or_404(payment_id)
    owner_hostel_ids = [h.id for h in current_user.hostels]
    if p.hostel_id not in owner_hostel_ids:
        return jsonify({'error': 'Access denied.'}), 403

    data = request.get_json(silent=True) or {}
    action = (data.get('action') or '').strip()  # 'approve' or 'reject'
    reason = (data.get('reason') or '').strip()

    if action not in ('approve', 'reject'):
        return jsonify({'error': "action must be 'approve' or 'reject'."}), 400

    p.status = 'Verified' if action == 'approve' else 'Rejected'
    db.session.commit()

    # Send email notification
    try:
        from app.utils.email_sender import send_payment_status_email
        resident = p.resident
        if resident and resident.user:
            send_payment_status_email(
                resident.user.email,
                resident.full_name,
                p.amount,
                p.status,
                reason or None
            )
    except Exception:
        pass

    _log(current_user.id, f'Mobile: {action}d payment #{p.id}')
    return jsonify({'message': f'Payment {p.status}.'}), 200


@mobile_api_bp.route('/owner/notices', methods=['GET'])
@jwt_required
def owner_get_notices(current_user):
    if current_user.role != 'HostelOwner':
        return jsonify({'error': 'Forbidden'}), 403

    hostel_id = request.args.get('hostel_id', type=int)
    owner_hostel_ids = [h.id for h in current_user.hostels]
    query = Notice.query.filter(Notice.hostel_id.in_(owner_hostel_ids))
    if hostel_id and hostel_id in owner_hostel_ids:
        query = query.filter_by(hostel_id=hostel_id)
    notices = query.order_by(Notice.created_at.desc()).limit(100).all()

    return jsonify([{
        'id': n.id,
        'hostel_id': n.hostel_id,
        'title': n.title,
        'message': n.message,
        'created_at': n.created_at.strftime('%Y-%m-%d %H:%M'),
    } for n in notices]), 200


@mobile_api_bp.route('/owner/notices', methods=['POST'])
@jwt_required
def owner_post_notice(current_user):
    if current_user.role != 'HostelOwner':
        return jsonify({'error': 'Forbidden'}), 403

    data = request.get_json(silent=True) or {}
    hostel_id = data.get('hostel_id', type=int) if hasattr(data.get('hostel_id'), '__int__') else data.get('hostel_id')
    title = (data.get('title') or '').strip()
    message = (data.get('message') or '').strip()

    if not all([hostel_id, title, message]):
        return jsonify({'error': 'hostel_id, title and message are required.'}), 400

    owner_hostel_ids = [h.id for h in current_user.hostels]
    if hostel_id not in owner_hostel_ids:
        return jsonify({'error': 'Access denied.'}), 403

    notice = Notice(hostel_id=hostel_id, title=title, message=message)
    db.session.add(notice)
    db.session.commit()

    _log(current_user.id, f'Mobile: posted notice "{title}" to hostel {hostel_id}')
    return jsonify({'message': 'Notice posted.', 'notice_id': notice.id}), 201


@mobile_api_bp.route('/owner/resident/<int:resident_id>', methods=['GET'])
@jwt_required
def owner_resident_detail(current_user, resident_id):
    """Full resident detail for QR scan result."""
    if current_user.role not in ('HostelOwner', 'SuperAdmin'):
        return jsonify({'error': 'Forbidden'}), 403

    r = Resident.query.get_or_404(resident_id)
    if current_user.role == 'HostelOwner':
        owner_hostel_ids = [h.id for h in current_user.hostels]
        if r.hostel_id not in owner_hostel_ids:
            return jsonify({'error': 'Access denied.'}), 403

    return jsonify({
        'id': r.id,
        'full_name': r.full_name,
        'email': r.user.email if r.user else None,
        'phone': r.phone_decrypted,
        'gender': r.gender,
        'room_number': r.room_number,
        'status': r.status,
        'payment_status': r.payment_status,
        'date_of_joining': r.date_of_joining.strftime('%Y-%m-%d') if r.date_of_joining else None,
        'hostel_name': r.hostel.hostel_name if r.hostel else None,
        'aadhar_masked': r.mask_aadhar(),
        'emergency_contact_name': r.emergency_contact_name,
        'emergency_contact_phone': r.emergency_contact_phone,
    }), 200


# ─────────────────────────────────────────────────────────────────
# PHARMACY Endpoints
# ─────────────────────────────────────────────────────────────────

@mobile_api_bp.route('/pharmacy/medicines', methods=['GET'])
@jwt_required
def pharmacy_medicines(current_user):
    """Paginated, searchable medicine list from all approved shops."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()

    query = Medicine.query.join(Shop).filter(
        Medicine.is_available == True,
        Shop.verification_status == 'Approved'
    )
    if search:
        query = query.filter(
            (Medicine.name.ilike(f'%{search}%')) |
            (Medicine.salt_composition.ilike(f'%{search}%')) |
            (Medicine.category.ilike(f'%{search}%'))
        )
    if category:
        query = query.filter(Medicine.category.ilike(f'%{category}%'))

    pagination = query.order_by(Medicine.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'medicines': [{
            'id': m.id,
            'name': m.name,
            'price': m.price,
            'category': m.category,
            'salt_composition': m.salt_composition,
            'stock_quantity': m.stock_quantity,
            'average_rating': m.average_rating,
            'photo_url': m.photo_url,
            'shop_name': m.shop.shop_name if m.shop else None,
            'shop_id': m.shop_id,
            'delivery_options': m.delivery_options_list,
            'payment_options': m.payment_options_list,
        } for m in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'page': page,
    }), 200


@mobile_api_bp.route('/pharmacy/medicines/<int:medicine_id>', methods=['GET'])
@jwt_required
def pharmacy_medicine_detail(current_user, medicine_id):
    m = Medicine.query.get_or_404(medicine_id)
    reviews = [{
        'id': rev.id,
        'rating': rev.rating,
        'comment': rev.comment,
        'reviewer': rev.reviewer.full_name or rev.reviewer.email if rev.reviewer else 'Anonymous',
        'created_at': rev.created_at.strftime('%Y-%m-%d'),
    } for rev in m.reviews]

    return jsonify({
        'id': m.id,
        'name': m.name,
        'price': m.price,
        'description': m.description,
        'category': m.category,
        'salt_composition': m.salt_composition,
        'stock_quantity': m.stock_quantity,
        'average_rating': m.average_rating,
        'photo_url': m.photo_url,
        'delivery_options': m.delivery_options_list,
        'payment_options': m.payment_options_list,
        'shop': {
            'id': m.shop.id,
            'name': m.shop.shop_name,
            'location': m.shop.location,
            'contact_phone': m.shop.contact_phone,
        } if m.shop else None,
        'reviews': reviews,
    }), 200


@mobile_api_bp.route('/pharmacy/orders', methods=['POST'])
@jwt_required
def pharmacy_place_order(current_user):
    """Place a medicine order."""
    data = request.get_json(silent=True) or {}
    medicine_id = data.get('medicine_id')
    quantity = data.get('quantity', 1)
    delivery_option = data.get('delivery_option', 'Standard')
    payment_option = data.get('payment_option', 'COD')
    delivery_address = (data.get('delivery_address') or '').strip()
    contact_phone = (data.get('contact_phone') or '').strip()
    notes = (data.get('notes') or '').strip()

    if not medicine_id:
        return jsonify({'error': 'medicine_id is required.'}), 400

    medicine = Medicine.query.get_or_404(medicine_id)
    if not medicine.is_available or medicine.stock_quantity < quantity:
        return jsonify({'error': 'Medicine unavailable or insufficient stock.'}), 400

    total_price = round(medicine.price * quantity, 2)
    order = MedicineOrder(
        medicine_id=medicine_id,
        shop_id=medicine.shop_id,
        buyer_id=current_user.id,
        quantity=quantity,
        total_price=total_price,
        delivery_option=delivery_option,
        payment_option=payment_option,
        delivery_address=delivery_address,
        contact_phone=contact_phone,
        notes=notes,
        status='Pending',
        delivery_status='Order Placed',
    )
    medicine.stock_quantity -= quantity
    db.session.add(order)
    db.session.commit()

    _log(current_user.id, f'Mobile: placed order #{order.id} for {medicine.name} x{quantity}')
    return jsonify({'message': 'Order placed successfully.', 'order_id': order.id, 'total': total_price}), 201


@mobile_api_bp.route('/pharmacy/orders/my', methods=['GET'])
@jwt_required
def my_orders(current_user):
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    pagination = MedicineOrder.query.filter_by(buyer_id=current_user.id)\
        .order_by(MedicineOrder.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'orders': [{
            'id': o.id,
            'medicine_name': o.medicine.name if o.medicine else None,
            'quantity': o.quantity,
            'total_price': o.total_price,
            'status': o.status,
            'delivery_status': o.delivery_status,
            'delivery_stage_index': o.delivery_stage_index,
            'delivery_stages': MedicineOrder.DELIVERY_STAGES,
            'payment_option': o.payment_option,
            'created_at': o.created_at.strftime('%Y-%m-%d %H:%M'),
        } for o in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'page': page,
    }), 200


# ─────────────────────────────────────────────────────────────────
# SHOP OWNER Endpoints
# ─────────────────────────────────────────────────────────────────

@mobile_api_bp.route('/shop/dashboard', methods=['GET'])
@jwt_required
def shop_dashboard(current_user):
    if current_user.role != 'ShopOwner':
        return jsonify({'error': 'Forbidden'}), 403

    shop = Shop.query.filter_by(owner_id=current_user.id).first()
    if not shop:
        return jsonify({'error': 'Shop not found. Please register your shop first.'}), 404

    pending_orders = MedicineOrder.query.filter_by(shop_id=shop.id, status='Pending').count()
    confirmed_orders = MedicineOrder.query.filter_by(shop_id=shop.id, status='Confirmed').count()
    total_medicines = Medicine.query.filter_by(shop_id=shop.id, is_available=True).count()

    return jsonify({
        'shop': {
            'id': shop.id,
            'name': shop.shop_name,
            'location': shop.location,
            'verification_status': shop.verification_status,
            'rating_avg': shop.rating_avg,
        },
        'stats': {
            'pending_orders': pending_orders,
            'confirmed_orders': confirmed_orders,
            'total_medicines': total_medicines,
        }
    }), 200


@mobile_api_bp.route('/shop/orders', methods=['GET'])
@jwt_required
def shop_orders(current_user):
    if current_user.role != 'ShopOwner':
        return jsonify({'error': 'Forbidden'}), 403

    shop = Shop.query.filter_by(owner_id=current_user.id).first()
    if not shop:
        return jsonify({'error': 'Shop not found.'}), 404

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status_filter = request.args.get('status', '')

    query = MedicineOrder.query.filter_by(shop_id=shop.id)
    if status_filter:
        query = query.filter_by(status=status_filter)
    pagination = query.order_by(MedicineOrder.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'orders': [{
            'id': o.id,
            'medicine_name': o.medicine.name if o.medicine else None,
            'buyer_name': o.buyer.full_name or o.buyer.email if o.buyer else None,
            'quantity': o.quantity,
            'total_price': o.total_price,
            'status': o.status,
            'delivery_status': o.delivery_status,
            'delivery_stage_index': o.delivery_stage_index,
            'payment_option': o.payment_option,
            'delivery_address': o.delivery_address,
            'contact_phone': o.contact_phone,
            'notes': o.notes,
            'created_at': o.created_at.strftime('%Y-%m-%d %H:%M'),
        } for o in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'page': page,
    }), 200


@mobile_api_bp.route('/shop/orders/<int:order_id>/status', methods=['POST'])
@jwt_required
def shop_update_order_status(current_user, order_id):
    if current_user.role != 'ShopOwner':
        return jsonify({'error': 'Forbidden'}), 403

    shop = Shop.query.filter_by(owner_id=current_user.id).first()
    if not shop:
        return jsonify({'error': 'Shop not found.'}), 404

    order = MedicineOrder.query.get_or_404(order_id)
    if order.shop_id != shop.id:
        return jsonify({'error': 'Access denied.'}), 403

    data = request.get_json(silent=True) or {}
    action = (data.get('action') or '').strip()     # 'approve', 'reject', 'advance'
    reason = (data.get('reason') or '').strip()

    if action == 'approve':
        order.status = 'Confirmed'
        order.delivery_status = 'Confirmed'
    elif action == 'reject':
        order.status = 'Rejected'
        order.rejection_reason = reason
        # Restore stock
        if order.medicine:
            order.medicine.stock_quantity += order.quantity
    elif action == 'advance':
        stages = MedicineOrder.DELIVERY_STAGES
        idx = order.delivery_stage_index
        if idx < len(stages) - 1:
            order.delivery_status = stages[idx + 1]
        else:
            return jsonify({'error': 'Order is already at final stage.'}), 400
    else:
        return jsonify({'error': "action must be 'approve', 'reject', or 'advance'."}), 400

    db.session.commit()
    _log(current_user.id, f'Mobile: {action}d order #{order.id}')
    return jsonify({'message': f'Order {action}d.', 'delivery_status': order.delivery_status}), 200


@mobile_api_bp.route('/shop/inventory', methods=['GET'])
@jwt_required
def shop_inventory(current_user):
    if current_user.role != 'ShopOwner':
        return jsonify({'error': 'Forbidden'}), 403

    shop = Shop.query.filter_by(owner_id=current_user.id).first()
    if not shop:
        return jsonify({'error': 'Shop not found.'}), 404

    medicines = Medicine.query.filter_by(shop_id=shop.id).order_by(Medicine.created_at.desc()).all()
    return jsonify([{
        'id': m.id,
        'name': m.name,
        'price': m.price,
        'category': m.category,
        'stock_quantity': m.stock_quantity,
        'is_available': m.is_available,
        'average_rating': m.average_rating,
    } for m in medicines]), 200


# ─────────────────────────────────────────────────────────────────
# ADMIN Endpoints
# ─────────────────────────────────────────────────────────────────

@mobile_api_bp.route('/admin/stats', methods=['GET'])
@jwt_required
def admin_stats(current_user):
    if current_user.role != 'SuperAdmin':
        return jsonify({'error': 'Forbidden'}), 403

    total_hostels = Hostel.query.count()
    total_owners = User.query.filter_by(role='HostelOwner').count()
    total_residents = Resident.query.count()
    active_residents = Resident.query.filter_by(status='Active').count()
    pending_residents = Resident.query.filter_by(status='Pending').count()
    total_capacity = sum(h.total_capacity for h in Hostel.query.all())
    occupied_rooms = len(set(r.room_number for r in Resident.query.filter(Resident.room_number.isnot(None), Resident.room_number != '').all())) or active_residents
    
    total_payments = Payment.query.count()
    pending_payments = Payment.query.filter_by(status='Pending').count()
    verified_payments = Payment.query.filter_by(status='Verified').count()
    total_rent_collected = float(db.session.query(db.func.sum(Payment.amount)).filter(Payment.status == 'Verified').scalar() or 0.0)
    pending_rent_amount = float(db.session.query(db.func.sum(Payment.amount)).filter(Payment.status == 'Pending').scalar() or 0.0)
    
    total_shops = Shop.query.count()
    pending_shops = Shop.query.filter_by(verification_status='Pending').count()
    total_orders = MedicineOrder.query.count()

    return jsonify({
        'hostels': total_hostels,
        'owners': total_owners,
        'residents': {
            'total': total_residents,
            'active': active_residents,
            'pending': pending_residents
        },
        'capacity': {
            'total': total_capacity,
            'occupied': occupied_rooms,
            'available': max(0, total_capacity - active_residents)
        },
        'payments': {
            'total': total_payments,
            'verified': verified_payments,
            'pending': pending_payments,
            'total_rent_collected': total_rent_collected,
            'pending_rent_amount': pending_rent_amount
        },
        'shops': {'total': total_shops, 'pending': pending_shops},
        'orders': total_orders,
    }), 200


@mobile_api_bp.route('/admin/residents', methods=['GET'])
@jwt_required
def admin_all_residents(current_user):
    if current_user.role != 'SuperAdmin':
        return jsonify({'error': 'Forbidden'}), 403

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('q', '').strip()

    query = Resident.query
    if search:
        query = query.join(Hostel).filter(
            (Resident.full_name.ilike(f'%{search}%')) |
            (Resident.room_number.ilike(f'%{search}%')) |
            (Hostel.hostel_name.ilike(f'%{search}%'))
        )
    pagination = query.order_by(Resident.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'residents': [{
            'id': r.id,
            'full_name': r.full_name,
            'email': r.user.email if r.user else None,
            'room_number': r.room_number,
            'status': r.status,
            'hostel_name': r.hostel.hostel_name if r.hostel else None,
            'payment_status': r.payment_status,
        } for r in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'page': page,
    }), 200


@mobile_api_bp.route('/admin/owners', methods=['GET'])
@jwt_required
def admin_owners(current_user):
    if current_user.role != 'SuperAdmin':
        return jsonify({'error': 'Forbidden'}), 403

    owners = User.query.filter_by(role='HostelOwner').order_by(User.created_at.desc()).all()
    return jsonify([{
        'id': o.id,
        'email': o.email,
        'full_name': o.full_name,
        'phone': o.phone,
        'hostel_count': len(o.hostels),
        'created_at': o.created_at.strftime('%Y-%m-%d') if o.created_at else None,
    } for o in owners]), 200


@mobile_api_bp.route('/admin/shops', methods=['GET'])
@jwt_required
def admin_shops(current_user):
    if current_user.role != 'SuperAdmin':
        return jsonify({'error': 'Forbidden'}), 403

    shops = Shop.query.order_by(Shop.created_at.desc()).all()
    return jsonify([{
        'id': s.id,
        'name': s.shop_name,
        'owner_email': s.owner.email if s.owner else None,
        'location': s.location,
        'verification_status': s.verification_status,
        'rating_avg': s.rating_avg,
    } for s in shops]), 200


@mobile_api_bp.route('/admin/shops/<int:shop_id>/verify', methods=['POST'])
@jwt_required
def admin_verify_shop(current_user, shop_id):
    if current_user.role != 'SuperAdmin':
        return jsonify({'error': 'Forbidden'}), 403

    shop = Shop.query.get_or_404(shop_id)
    data = request.get_json(silent=True) or {}
    action = (data.get('action') or '').strip()  # 'approve' or 'reject'

    if action == 'approve':
        shop.verification_status = 'Approved'
    elif action == 'reject':
        shop.verification_status = 'Rejected'
    else:
        return jsonify({'error': "action must be 'approve' or 'reject'."}), 400

    db.session.commit()
    _log(current_user.id, f'Mobile: {action}d shop {shop.shop_name}')
    return jsonify({'message': f'Shop {shop.verification_status}.'}), 200


# ─────────────────────────────────────────────────────────────────
# PUBLIC Endpoints (no JWT required)
# ─────────────────────────────────────────────────────────────────

@mobile_api_bp.route('/hostels/public', methods=['GET'])
def public_hostels():
    """Public hostel discovery — no auth required."""
    search = request.args.get('q', '').strip().lower()
    hostels = Hostel.query.all()
    if search:
        hostels = [
            h for h in hostels
            if search in h.hostel_name.lower()
            or search in h.location.lower()
            or (h.hostel_code and search in h.hostel_code.lower())
        ]
    return jsonify([{
        'id': h.id,
        'name': h.hostel_name,
        'location': h.location,
        'code': h.hostel_code,
        'capacity': h.total_capacity,
        'available_rooms': h.available_rooms,
        'facilities': h.facilities_list,
        'rent': h.rent,
    } for h in hostels]), 200
