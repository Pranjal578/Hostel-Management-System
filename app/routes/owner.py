import os
import uuid
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from app.models.db import db, User, Hostel, Resident, Payment, AuditLog
from app.routes.auth import role_required, log_security_action
from app.utils.photo_handler import validate_photo, sanitize_image_metadata
from app.utils.email_sender import send_payment_status_email
from app.utils.qr_generator import generate_qr_code, delete_qr_code

owner_bp = Blueprint('owner', __name__)

@owner_bp.route('/dashboard')
@role_required('HostelOwner')
def dashboard():
    """Hostel Owner Dashboard - managing residents and verifying payments"""
    owner_id = session['user_id']
    hostel = Hostel.query.filter_by(owner_id=owner_id).first()
    
    if not hostel:
        return render_template('admin_dashboard.html', no_hostel=True)

    residents = Resident.query.filter_by(hostel_id=hostel.id).all()
    pending_payments = Payment.query.filter_by(hostel_id=hostel.id, status='Pending').all()
    verified_payments = Payment.query.filter_by(hostel_id=hostel.id, status='Verified').all()

    # Search filter logic
    search_query = request.args.get('search', '').strip()
    if search_query:
        # Filter residents list in memory since values are encrypted (like phone)
        # and name is plain
        filtered_residents = []
        for r in residents:
            if (search_query.lower() in r.full_name.lower() or 
                search_query.lower() in r.room_number.lower() or
                search_query in r.phone_decrypted):
                filtered_residents.append(r)
        residents = filtered_residents

    return render_template(
        'admin_dashboard.html',
        is_owner=True,
        hostel=hostel,
        residents=residents,
        pending_payments=pending_payments,
        verified_payments=verified_payments,
        occupied_rooms=len(residents),
        capacity_left=max(0, hostel.total_capacity - len(residents)),
        search_query=search_query
    )


@owner_bp.route('/payment-qr', methods=['POST'])
@role_required('HostelOwner')
def upload_payment_qr():
    """Upload payment QR code image for residents to pay"""
    owner_id = session['user_id']
    hostel = Hostel.query.filter_by(owner_id=owner_id).first()
    
    if not hostel:
        flash('No hostel assigned.', 'danger')
        return redirect(url_for('owner.dashboard'))

    file = request.files.get('payment_qr')
    if not file or file.filename == '':
        flash('No QR file selected.', 'warning')
        return redirect(url_for('owner.dashboard'))

    is_valid, error_msg = validate_photo(file)
    if not is_valid:
        flash(f'Invalid image: {error_msg}', 'danger')
        return redirect(url_for('owner.dashboard'))

    try:
        # Sanitize metadata
        clean_stream = sanitize_image_metadata(file)
        
        # Save to static/uploads/payment_qrs/
        upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'payment_qrs')
        os.makedirs(upload_dir, exist_ok=True)
        
        file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'jpg'
        filename = f"hostel_{hostel.id}_{uuid.uuid4().hex[:8]}.{file_ext}"
        filepath = os.path.join(upload_dir, filename)

        with open(filepath, 'wb') as f:
            f.write(clean_stream.read())

        # Delete old QR code if exists
        if hostel.payment_qr_code:
            old_path = os.path.join(current_app.root_path, hostel.payment_qr_code.lstrip('/'))
            if os.path.exists(old_path):
                try:
                    os.remove(old_path)
                except Exception:
                    pass

        # Update in database
        hostel.payment_qr_code = f"/static/uploads/payment_qrs/{filename}"
        db.session.commit()

        log_security_action(owner_id, f"Uploaded new payment QR code image for hostel '{hostel.hostel_name}'")
        flash('Payment QR code updated successfully!', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Failed to upload QR code: {str(e)}', 'danger')

    return redirect(url_for('owner.dashboard'))


@owner_bp.route('/payment/verify/<int:payment_id>', methods=['POST'])
@role_required('HostelOwner')
def verify_payment(payment_id):
    """Verify pending payment receipt"""
    owner_id = session['user_id']
    hostel = Hostel.query.filter_by(owner_id=owner_id).first()
    
    if not hostel:
        flash('Unauthorized operation.', 'danger')
        return redirect(url_for('owner.dashboard'))

    payment = Payment.query.filter_by(id=payment_id, hostel_id=hostel.id).first_or_404()
    payment.status = 'Verified'
    db.session.commit()

    # Log action
    log_security_action(owner_id, f"Verified payment ID {payment.id} for Resident {payment.resident.full_name}")

    # Notify Resident
    send_payment_status_email(
        resident_email=payment.resident.user.email,
        resident_name=payment.resident.full_name,
        amount=payment.amount,
        status='Verified'
    )

    flash(f"Payment of ${payment.amount} verified successfully!", 'success')
    return redirect(url_for('owner.dashboard'))


@owner_bp.route('/payment/reject/<int:payment_id>', methods=['POST'])
@role_required('HostelOwner')
def reject_payment(payment_id):
    """Reject pending payment receipt"""
    owner_id = session['user_id']
    hostel = Hostel.query.filter_by(owner_id=owner_id).first()
    
    if not hostel:
        flash('Unauthorized operation.', 'danger')
        return redirect(url_for('owner.dashboard'))

    payment = Payment.query.filter_by(id=payment_id, hostel_id=hostel.id).first_or_404()
    reason = request.form.get('rejection_reason', '').strip()
    
    payment.status = 'Rejected'
    db.session.commit()

    # Log action
    log_security_action(owner_id, f"Rejected payment ID {payment.id} for Resident {payment.resident.full_name}. Reason: {reason}")

    # Notify Resident
    send_payment_status_email(
        resident_email=payment.resident.user.email,
        resident_name=payment.resident.full_name,
        amount=payment.amount,
        status='Rejected',
        reason=reason
    )

    flash(f"Payment of ${payment.amount} has been rejected.", 'warning')
    return redirect(url_for('owner.dashboard'))


@owner_bp.route('/resident/delete/<int:resident_id>', methods=['POST'])
@role_required('HostelOwner')
def delete_resident(resident_id):
    """Delete a resident profile and credentials"""
    owner_id = session['user_id']
    hostel = Hostel.query.filter_by(owner_id=owner_id).first()
    
    if not hostel:
        flash('Unauthorized operation.', 'danger')
        return redirect(url_for('owner.dashboard'))

    resident = Resident.query.filter_by(id=resident_id, hostel_id=hostel.id).first_or_404()
    user = resident.user
    resident_name = resident.full_name

    try:
        # Delete profile photo file
        if resident.profile_image and resident.profile_image != 'default_profile.png':
            photo_path = os.path.join(current_app.root_path, 'static', 'images', resident.profile_image)
            if os.path.exists(photo_path):
                try:
                    os.remove(photo_path)
                except Exception:
                    pass

        # Delete QR code image file
        delete_qr_code(resident.id)

        # Delete User (cascades database relations)
        db.session.delete(user)
        db.session.commit()

        log_security_action(owner_id, f"Removed resident profile and credentials: {resident_name}")
        flash(f"Resident '{resident_name}' removed successfully.", 'success')

    except Exception as e:
        db.session.rollback()
        flash(f"Failed to delete resident: {str(e)}", 'danger')

    return redirect(url_for('owner.dashboard'))


@owner_bp.route('/resident/edit/<int:resident_id>', methods=['GET', 'POST'])
@role_required('HostelOwner')
def edit_resident(resident_id):
    """Hostel Owner editing resident details (including room number)"""
    owner_id = session['user_id']
    hostel = Hostel.query.filter_by(owner_id=owner_id).first()
    
    if not hostel:
        flash('Unauthorized operation.', 'danger')
        return redirect(url_for('owner.dashboard'))

    resident = Resident.query.filter_by(id=resident_id, hostel_id=hostel.id).first_or_404()
    
    if request.method == 'POST':
        try:
            email = request.form.get('email', '').strip()
            phone = request.form.get('phone', '').strip()
            room_number = request.form.get('room_number', '').strip()
            aadhar_raw = request.form.get('aadhar_id', '').replace('-', '')
            
            # 1. Email validation
            existing_user = User.query.filter_by(email=email).first()
            if existing_user and existing_user.id != resident.user_id:
                flash('Email is already in use by another user.', 'danger')
                return render_template('edit_resident.html', resident=resident, clear_email=True)
                
            # 2. Phone validation
            all_residents = Resident.query.all()
            for r in all_residents:
                if r.id != resident.id and r.phone_decrypted == phone:
                    flash('Phone number is already in use by another resident.', 'danger')
                    return render_template('edit_resident.html', resident=resident, clear_phone=True)
                    
            # 3. Room number validation
            existing_room = Resident.query.filter_by(hostel_id=hostel.id, room_number=room_number).first()
            if existing_room and existing_room.id != resident.id:
                flash(f'Room {room_number} is already occupied in this hostel.', 'danger')
                return render_template('edit_resident.html', resident=resident, clear_room=True)
                
            # 4. Aadhar validation
            aadhar_formatted = None
            if aadhar_raw:
                if aadhar_raw.isdigit() and len(aadhar_raw) == 12:
                    aadhar_formatted = f"{aadhar_raw[:4]}-{aadhar_raw[4:8]}-{aadhar_raw[8:12]}"
                else:
                    flash('Aadhar ID must be exactly 12 digits.', 'warning')
                    return render_template('edit_resident.html', resident=resident, clear_aadhar=True)

            # 5. Parse DOB and DOJ
            dob = datetime.strptime(request.form['date_of_birth'], '%Y-%m-%d').date()
            doj = datetime.strptime(request.form['date_of_joining'], '%Y-%m-%d').date()

            # Apply changes
            resident.user.email = email
            resident.full_name = request.form.get('full_name', '').strip()
            resident.gender = request.form.get('gender')
            resident.date_of_birth = dob
            resident.date_of_joining = doj
            resident.room_number = room_number
            
            # Using encrypted field setters
            resident.phone_decrypted = phone
            resident.permanent_address_decrypted = request.form.get('permanent_address', '').strip()
            if aadhar_formatted:
                resident.aadhar_id_decrypted = aadhar_formatted
            else:
                resident.aadhar_id = None
                
            # Emergency contacts
            resident.emergency_contact_name = request.form.get('emergency_contact_name', '').strip()
            resident.emergency_contact_phone = request.form.get('emergency_contact_phone', '').strip()
            resident.emergency_contact_relation = request.form.get('emergency_contact_relation')
            
            # Guardian Details
            resident.guardian_name = request.form.get('guardian_name', '').strip() or None
            resident.guardian_phone = request.form.get('guardian_phone', '').strip() or None
            resident.guardian_email = request.form.get('guardian_email', '').strip() or None
            resident.guardian_relation = request.form.get('guardian_relation', '').strip() or None
            
            resident.emergency_contact_address = request.form.get('emergency_contact_address', '').strip() or None
            
            db.session.commit()
            log_security_action(owner_id, f"Updated resident profile for {resident.full_name}")
            flash('Resident details updated successfully!', 'success')
            return redirect(url_for('owner.dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Failed to update resident details: {str(e)}', 'danger')
            return render_template('edit_resident.html', resident=resident)
            
    return render_template('edit_resident.html', resident=resident)
