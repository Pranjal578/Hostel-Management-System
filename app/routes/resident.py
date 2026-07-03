import os
import io
import uuid
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from app.models.db import db, Resident, Payment, Hostel, User
from app.routes.auth import role_required, log_security_action
from app.utils.photo_handler import validate_photo, sanitize_image_metadata
from app.utils.email_sender import send_payment_submitted_email

resident_bp = Blueprint('resident', __name__)

@resident_bp.route('/dashboard')
@role_required('Resident')
def dashboard():
    """Resident main settings/dashboard page"""
    user_id = session['user_id']
    resident = Resident.query.filter_by(user_id=user_id).first_or_404()
    payments = Payment.query.filter_by(resident_id=resident.id).order_by(Payment.created_at.desc()).all()
    
    # Check if a recent payment exists for the current calendar month
    current_month_paid = False
    now = datetime.now()
    for p in payments:
        if p.payment_date.month == now.month and p.payment_date.year == now.year and p.status in ['Verified', 'Pending']:
            current_month_paid = True
            break

    return render_template(
        'resident_profile.html',
        resident=resident,
        payments=payments,
        current_month_paid=current_month_paid,
        is_public=False
    )


@resident_bp.route('/pay', methods=['POST'])
@role_required('Resident')
def submit_payment():
    """Submit a payment proof receipt screenshot/PDF for verification"""
    user_id = session['user_id']
    resident = Resident.query.filter_by(user_id=user_id).first_or_404()
    
    amount = request.form.get('amount')
    tx_id = request.form.get('transaction_id', '').strip()
    pay_date_str = request.form.get('payment_date')
    file = request.files.get('screenshot')

    if not all([amount, tx_id, pay_date_str, file]):
        flash('All form fields are required.', 'warning')
        return redirect(url_for('resident.dashboard'))

    # Validate payment date
    try:
        payment_date = datetime.strptime(pay_date_str, '%Y-%m-%d').date()
    except Exception:
        flash('Invalid payment date format.', 'danger')
        return redirect(url_for('resident.dashboard'))

    # Check file size & formats
    filename = file.filename
    if not filename or '.' not in filename:
        flash('Invalid receipt attachment.', 'danger')
        return redirect(url_for('resident.dashboard'))
        
    ext = filename.rsplit('.', 1)[1].lower()
    if ext not in ['jpg', 'jpeg', 'png', 'pdf']:
        flash('Invalid file format. Only JPG, PNG, and PDF receipt proofs allowed.', 'danger')
        return redirect(url_for('resident.dashboard'))

    # File size validation (limit to 5MB)
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    if file_size > 5 * 1024 * 1024:
        flash('Receipt attachment is too large. Maximum size is 5MB.', 'danger')
        return redirect(url_for('resident.dashboard'))

    try:
        # Create output directory outside web root (instance folder)
        upload_dir = os.path.join(current_app.instance_path, 'uploads', 'payments')
        os.makedirs(upload_dir, exist_ok=True)
        
        secure_name = f"payment_{uuid.uuid4().hex[:12]}.{ext}"
        filepath = os.path.join(upload_dir, secure_name)

        if ext in ['jpg', 'jpeg', 'png']:
            # Sanitize image metadata (GPS/EXIF) using Pillow
            clean_stream = sanitize_image_metadata(file)
            with open(filepath, 'wb') as f:
                f.write(clean_stream.read())
        else:
            # For PDFs, save directly with secure filename (metadata stripping is image-specific)
            file.seek(0)
            file.save(filepath)

        # Create Payment entry in database with secure serving path
        payment = Payment(
            resident_id=resident.id,
            hostel_id=resident.hostel_id,
            amount=float(amount),
            payment_date=payment_date,
            transaction_id=tx_id,
            screenshot_path=f"/secure-receipt/{secure_name}",
            status='Pending'
        )
        db.session.add(payment)
        db.session.commit()

        # Log security audit action
        log_security_action(user_id, f"Uploaded payment receipt proof for transaction: {tx_id}")

        # Send notification email to the Hostel Owner
        owner_email = resident.hostel.owner.email
        review_url = url_for('owner.dashboard', _external=True)
        send_payment_submitted_email(
            owner_email=owner_email,
            resident_name=resident.full_name,
            amount=amount,
            review_url=review_url
        )

        flash('Payment submitted successfully! Waiting for owner verification.', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred: {str(e)}', 'danger')

    return redirect(url_for('resident.dashboard'))
