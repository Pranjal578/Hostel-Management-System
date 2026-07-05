import os
import uuid
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from app.models.db import db, User, Hostel, Resident, Payment, AuditLog, Notice
from app.routes.auth import role_required, log_security_action
from app.utils.photo_handler import validate_photo, sanitize_image_metadata
from app.utils.email_sender import send_payment_status_email
from app.utils.qr_generator import generate_qr_code, delete_qr_code

owner_bp = Blueprint('owner', __name__)

@owner_bp.route('/dashboard')
@role_required('HostelOwner')
def dashboard():
    """Hostel Owner Dashboard - central summary portal"""
    owner_id = session['user_id']
    hostels = Hostel.query.filter_by(owner_id=owner_id).all()
    hostel_ids = [h.id for h in hostels]
    
    residents = Resident.query.filter(Resident.hostel_id.in_(hostel_ids)).all() if hostel_ids else []
    pending_payments = Payment.query.filter(Payment.hostel_id.in_(hostel_ids), Payment.status == 'Pending').all() if hostel_ids else []
    verified_payments = Payment.query.filter(Payment.hostel_id.in_(hostel_ids), Payment.status == 'Verified').all() if hostel_ids else []

    return render_template(
        'admin_dashboard.html',
        is_owner=True,
        hostels=hostels,
        residents=residents,
        pending_payments=pending_payments,
        verified_payments=verified_payments,
        occupied_rooms=len(residents),
        capacity_left=sum(max(0, h.total_capacity - len(h.residents)) for h in hostels)
    )


@owner_bp.route('/hostels', methods=['GET'])
@role_required('HostelOwner')
def hostels_list():
    """Owner's Hostels page - displays hostels managed by them and addition/configuration settings"""
    owner_id = session['user_id']
    hostels = Hostel.query.filter_by(owner_id=owner_id).all()
    return render_template('owner_hostels.html', hostels=hostels)


def _generate_hostel_code():
    """Generate a unique hostel code in the format HOS-YYYY-NNN."""
    year = datetime.utcnow().year
    existing_codes = db.session.query(Hostel.hostel_code).filter(
        Hostel.hostel_code.like(f"HOS-{year}-%")
    ).all()
    seq = len(existing_codes) + 1
    return f"HOS-{year}-{seq:03d}"


@owner_bp.route('/hostel/create', methods=['POST'])
@role_required('HostelOwner')
def create_hostel():
    """Add a new hostel managed under this Owner"""
    owner_id = session['user_id']
    name = request.form.get('hostel_name', '').strip()
    location = request.form.get('location', '').strip()
    capacity = int(request.form.get('total_capacity', 100))
    rent = float(request.form.get('rent', 0.0) or 0.0)
    electricity_bill = float(request.form.get('electricity_bill', 0.0) or 0.0)

    # Facilities: collect from multi-select or text field
    facilities_list = request.form.getlist('facilities')
    if not facilities_list:
        raw = request.form.get('facilities_text', '').strip()
        facilities_list = [f.strip() for f in raw.split(',') if f.strip()]
    facilities_str = ','.join(facilities_list) if facilities_list else None

    hostel_code = _generate_hostel_code()

    new_hostel = Hostel(
        hostel_name=name,
        location=location,
        total_capacity=capacity,
        owner_id=owner_id,
        facilities=facilities_str,
        hostel_code=hostel_code,
        rent=rent,
        electricity_bill=electricity_bill
    )
    db.session.add(new_hostel)
    db.session.commit()

    # Generate hostel-info QR code
    from app.utils.qr_generator import generate_hostel_qr
    try:
        qr_path = generate_hostel_qr(new_hostel)
        new_hostel.hostel_qr_code = qr_path
        db.session.commit()
    except Exception as e:
        print(f"[WARN] Hostel QR generation failed: {e}")

    log_security_action(owner_id, f"Added new hostel '{name}' [{hostel_code}]")
    flash(f"Hostel '{name}' created successfully with code {hostel_code}!", 'success')
    return redirect(url_for('owner.hostels_list'))


@owner_bp.route('/hostel/delete/<int:hostel_id>', methods=['POST'])
@role_required('HostelOwner')
def delete_hostel(hostel_id):
    """Delete a hostel (Owner only)"""
    owner_id = session['user_id']
    hostel = Hostel.query.filter_by(id=hostel_id, owner_id=owner_id).first_or_404()
    name = hostel.hostel_name
    
    residents_count = Resident.query.filter_by(hostel_id=hostel_id).count()
    if residents_count > 0:
        flash(f"Cannot delete hostel '{name}' because it contains active residents.", 'danger')
        return redirect(url_for('owner.hostels_list'))

    # Clean up hostel QR code file
    from app.utils.qr_generator import delete_hostel_qr
    delete_hostel_qr(hostel_id)

    db.session.delete(hostel)
    db.session.commit()

    log_security_action(owner_id, f"Deleted hostel '{name}'")
    flash(f"Hostel '{name}' deleted successfully.", 'success')
    return redirect(url_for('owner.hostels_list'))


@owner_bp.route('/residents', methods=['GET'])
@role_required('HostelOwner')
def residents_list():
    """List all residents in any of the owner's hostels"""
    owner_id = session['user_id']
    hostels = Hostel.query.filter_by(owner_id=owner_id).all()
    hostel_ids = [h.id for h in hostels]
    residents = Resident.query.filter(Resident.hostel_id.in_(hostel_ids)).all() if hostel_ids else []

    # Search filter logic
    search_query = request.args.get('search', '').strip()
    if search_query:
        filtered_residents = []
        for r in residents:
            if (search_query.lower() in r.full_name.lower() or 
                search_query.lower() in r.room_number.lower() or
                search_query in r.phone_decrypted):
                filtered_residents.append(r)
        residents = filtered_residents

    return render_template(
        'owner_residents.html',
        residents=residents,
        hostels=hostels,
        search_query=search_query
    )


@owner_bp.route('/payments', methods=['GET'])
@role_required('HostelOwner')
def payments_list():
    """Payments management portal - reviewing pending and verified payments"""
    owner_id = session['user_id']
    hostels = Hostel.query.filter_by(owner_id=owner_id).all()
    hostel_ids = [h.id for h in hostels]
    
    pending_payments = Payment.query.filter(Payment.hostel_id.in_(hostel_ids), Payment.status == 'Pending').order_by(Payment.created_at.desc()).all() if hostel_ids else []
    verified_payments = Payment.query.filter(Payment.hostel_id.in_(hostel_ids), Payment.status == 'Verified').order_by(Payment.created_at.desc()).all() if hostel_ids else []
    rejected_payments = Payment.query.filter(Payment.hostel_id.in_(hostel_ids), Payment.status == 'Rejected').order_by(Payment.created_at.desc()).all() if hostel_ids else []

    return render_template(
        'owner_payments.html',
        hostels=hostels,
        pending_payments=pending_payments,
        verified_payments=verified_payments,
        rejected_payments=rejected_payments
    )


@owner_bp.route('/notices', methods=['GET'])
@role_required('HostelOwner')
def notices_list():
    """Manage notice broadcasts"""
    owner_id = session['user_id']
    hostels = Hostel.query.filter_by(owner_id=owner_id).all()
    hostel_ids = [h.id for h in hostels]
    notices = Notice.query.filter(Notice.hostel_id.in_(hostel_ids)).order_by(Notice.created_at.desc()).all() if hostel_ids else []
    return render_template('owner_notices.html', notices=notices, hostels=hostels)


@owner_bp.route('/chat', methods=['GET'])
@role_required('HostelOwner')
def chat_dashboard():
    """WhatsApp-style chat dashboard for Owner to talk to residents"""
    owner_id = session['user_id']
    hostels = Hostel.query.filter_by(owner_id=owner_id).all()
    hostel_ids = [h.id for h in hostels]
    residents = Resident.query.filter(Resident.hostel_id.in_(hostel_ids)).all() if hostel_ids else []
    return render_template('owner_chat.html', residents=residents)


@owner_bp.route('/payment-qr/<int:hostel_id>', methods=['POST'])
@role_required('HostelOwner')
def upload_payment_qr(hostel_id):
    """Upload payment QR code image for a specific hostel"""
    owner_id = session['user_id']
    hostel = Hostel.query.filter_by(id=hostel_id, owner_id=owner_id).first_or_404()

    file = request.files.get('payment_qr')
    if not file or file.filename == '':
        flash('No QR file selected.', 'warning')
        return redirect(url_for('owner.hostels_list'))

    is_valid, error_msg = validate_photo(file)
    if not is_valid:
        flash(f'Invalid image: {error_msg}', 'danger')
        return redirect(url_for('owner.hostels_list'))

    try:
        clean_stream = sanitize_image_metadata(file)
        
        upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'payment_qrs')
        os.makedirs(upload_dir, exist_ok=True)
        
        file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'jpg'
        filename = f"hostel_{hostel.id}_{uuid.uuid4().hex[:8]}.{file_ext}"
        filepath = os.path.join(upload_dir, filename)

        with open(filepath, 'wb') as f:
            f.write(clean_stream.read())

        if hostel.payment_qr_code:
            old_path = os.path.join(current_app.root_path, hostel.payment_qr_code.lstrip('/'))
            if os.path.exists(old_path):
                try:
                    os.remove(old_path)
                except Exception:
                    pass

        hostel.payment_qr_code = f"/static/uploads/payment_qrs/{filename}"
        db.session.commit()

        log_security_action(owner_id, f"Uploaded new payment QR code image for hostel '{hostel.hostel_name}'")
        flash('Payment QR code updated successfully!', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Failed to upload QR code: {str(e)}', 'danger')

    return redirect(url_for('owner.hostels_list'))


@owner_bp.route('/payment/verify/<int:payment_id>', methods=['POST'])
@role_required('HostelOwner')
def verify_payment(payment_id):
    """Verify pending payment receipt"""
    owner_id = session['user_id']
    hostels = Hostel.query.filter_by(owner_id=owner_id).all()
    hostel_ids = [h.id for h in hostels]
    
    payment = Payment.query.filter(Payment.id == payment_id, Payment.hostel_id.in_(hostel_ids)).first_or_404()
    payment.status = 'Verified'
    db.session.commit()

    log_security_action(owner_id, f"Verified payment ID {payment.id} for Resident {payment.resident.full_name}")

    send_payment_status_email(
        resident_email=payment.resident.user.email,
        resident_name=payment.resident.full_name,
        amount=payment.amount,
        status='Verified'
    )

    flash(f"Payment of ${payment.amount} verified successfully!", 'success')
    return redirect(url_for('owner.payments_list'))


@owner_bp.route('/payment/reject/<int:payment_id>', methods=['POST'])
@role_required('HostelOwner')
def reject_payment(payment_id):
    """Reject pending payment receipt"""
    owner_id = session['user_id']
    hostels = Hostel.query.filter_by(owner_id=owner_id).all()
    hostel_ids = [h.id for h in hostels]
    
    payment = Payment.query.filter(Payment.id == payment_id, Payment.hostel_id.in_(hostel_ids)).first_or_404()
    reason = request.form.get('rejection_reason', '').strip()
    
    payment.status = 'Rejected'
    db.session.commit()

    log_security_action(owner_id, f"Rejected payment ID {payment.id} for Resident {payment.resident.full_name}. Reason: {reason}")

    send_payment_status_email(
        resident_email=payment.resident.user.email,
        resident_name=payment.resident.full_name,
        amount=payment.amount,
        status='Rejected',
        reason=reason
    )

    flash(f"Payment of ${payment.amount} has been rejected.", 'warning')
    return redirect(url_for('owner.payments_list'))


@owner_bp.route('/resident/delete/<int:resident_id>', methods=['POST'])
@role_required('HostelOwner')
def delete_resident(resident_id):
    """Delete a resident profile and credentials"""
    owner_id = session['user_id']
    hostels = Hostel.query.filter_by(owner_id=owner_id).all()
    hostel_ids = [h.id for h in hostels]
    
    resident = Resident.query.filter(Resident.id == resident_id, Resident.hostel_id.in_(hostel_ids)).first_or_404()
    user = resident.user
    resident_name = resident.full_name

    try:
        if resident.profile_image and resident.profile_image != 'default_profile.png':
            photo_path = os.path.join(current_app.root_path, 'static', 'images', resident.profile_image)
            if os.path.exists(photo_path):
                try:
                    os.remove(photo_path)
                except Exception:
                    pass

        delete_qr_code(resident.id)

        db.session.delete(user)
        db.session.commit()

        log_security_action(owner_id, f"Removed resident profile: {resident_name}")
        flash(f"Resident '{resident_name}' removed successfully.", 'success')

    except Exception as e:
        db.session.rollback()
        flash(f"Failed to delete resident: {str(e)}", 'danger')

    return redirect(url_for('owner.residents_list'))


@owner_bp.route('/resident/edit/<int:resident_id>', methods=['GET', 'POST'])
@role_required('HostelOwner')
def edit_resident(resident_id):
    """Hostel Owner editing resident details"""
    owner_id = session['user_id']
    hostels = Hostel.query.filter_by(owner_id=owner_id).all()
    hostel_ids = [h.id for h in hostels]
    
    resident = Resident.query.filter(Resident.id == resident_id, Resident.hostel_id.in_(hostel_ids)).first_or_404()
    
    if request.method == 'POST':
        try:
            email = request.form.get('email', '').strip()
            phone = request.form.get('phone', '').strip()
            room_number = request.form.get('room_number', '').strip()
            aadhar_raw = request.form.get('aadhar_id', '').replace('-', '')
            
            existing_user = User.query.filter_by(email=email).first()
            if existing_user and existing_user.id != resident.user_id:
                flash('Email is already in use by another user.', 'danger')
                return render_template('edit_resident.html', resident=resident, clear_email=True)
                
            all_residents = Resident.query.all()
            for r in all_residents:
                if r.id != resident.id and r.phone_decrypted == phone:
                    flash('Phone number is already in use by another resident.', 'danger')
                    return render_template('edit_resident.html', resident=resident, clear_phone=True)
                    
            existing_room = Resident.query.filter_by(hostel_id=resident.hostel_id, room_number=room_number).first()
            if existing_room and existing_room.id != resident.id:
                flash(f'Room {room_number} is already occupied.', 'danger')
                return render_template('edit_resident.html', resident=resident, clear_room=True)
                
            aadhar_formatted = None
            if aadhar_raw:
                if aadhar_raw.isdigit() and len(aadhar_raw) == 12:
                    aadhar_formatted = f"{aadhar_raw[:4]}-{aadhar_raw[4:8]}-{aadhar_raw[8:12]}"
                else:
                    flash('Aadhar ID must be exactly 12 digits.', 'warning')
                    return render_template('edit_resident.html', resident=resident, clear_aadhar=True)

            dob = datetime.strptime(request.form['date_of_birth'], '%Y-%m-%d').date()
            doj = datetime.strptime(request.form['date_of_joining'], '%Y-%m-%d').date()

            resident.user.email = email
            resident.full_name = request.form.get('full_name', '').strip()
            resident.gender = request.form.get('gender')
            resident.date_of_birth = dob
            resident.date_of_joining = doj
            resident.room_number = room_number
            resident.phone_decrypted = phone
            resident.permanent_address_decrypted = request.form.get('permanent_address', '').strip()
            if aadhar_formatted:
                resident.aadhar_id_decrypted = aadhar_formatted
            else:
                resident.aadhar_id = None
                
            resident.emergency_contact_name = request.form.get('emergency_contact_name', '').strip()
            resident.emergency_contact_phone = request.form.get('emergency_contact_phone', '').strip()
            resident.emergency_contact_relation = request.form.get('emergency_contact_relation')
            resident.guardian_name = request.form.get('guardian_name', '').strip() or None
            resident.guardian_phone = request.form.get('guardian_phone', '').strip() or None
            resident.guardian_email = request.form.get('guardian_email', '').strip() or None
            resident.guardian_relation = request.form.get('guardian_relation', '').strip() or None
            resident.emergency_contact_address = request.form.get('emergency_contact_address', '').strip() or None
            
            db.session.commit()
            log_security_action(owner_id, f"Updated resident profile for {resident.full_name}")
            flash('Resident details updated successfully!', 'success')
            return redirect(url_for('owner.residents_list'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Failed to update resident details: {str(e)}', 'danger')
            return render_template('edit_resident.html', resident=resident)
            
    return render_template('edit_resident.html', resident=resident)


@owner_bp.route('/notice/send', methods=['POST'])
@role_required('HostelOwner')
def send_notice():
    """Post a notice to all residents of a selected hostel"""
    owner_id = session['user_id']
    hostel_id = request.form.get('hostel_id')
    
    # Ensure owner manages this hostel
    hostel = Hostel.query.filter_by(id=hostel_id, owner_id=owner_id).first()
    if not hostel:
        flash('Unauthorized or invalid hostel selected.', 'danger')
        return redirect(url_for('owner.notices_list'))

    title = request.form.get('notice_title', '').strip()
    message = request.form.get('notice_message', '').strip()

    if not title or not message:
        flash('Notice title and message are required.', 'warning')
        return redirect(url_for('owner.notices_list'))

    notice = Notice(hostel_id=hostel.id, title=title, message=message)
    db.session.add(notice)
    db.session.commit()

    residents = Resident.query.filter_by(hostel_id=hostel.id).all()
    from app.utils.email_sender import send_notice_email
    for resident in residents:
        try:
            send_notice_email(
                resident_email=resident.user.email,
                resident_name=resident.full_name,
                hostel_name=hostel.hostel_name,
                notice_title=title,
                notice_message=message
            )
        except Exception as e:
            print(f"[WARN] Notice email failed: {e}")

    log_security_action(owner_id, f"Posted notice '{title}' for hostel '{hostel.hostel_name}'")
    flash(f"Notice '{title}' posted successfully to {len(residents)} resident(s).", 'success')
    return redirect(url_for('owner.notices_list'))


@owner_bp.route('/notice/delete/<int:notice_id>', methods=['POST'])
@role_required('HostelOwner')
def delete_notice(notice_id):
    """Delete a posted notice"""
    owner_id = session['user_id']
    hostels = Hostel.query.filter_by(owner_id=owner_id).all()
    hostel_ids = [h.id for h in hostels]
    
    notice = Notice.query.filter(Notice.id == notice_id, Notice.hostel_id.in_(hostel_ids)).first_or_404()
    db.session.delete(notice)
    db.session.commit()

    log_security_action(owner_id, f"Deleted notice ID {notice_id}")
    flash('Notice deleted.', 'success')
    return redirect(url_for('owner.notices_list'))
