from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.models.db import db, User, Hostel, Resident, Payment
from app.routes.auth import role_required, log_security_action
from app.utils.qr_generator import generate_hostel_qr, delete_hostel_qr
from app.utils.validators import (
    validate_email, validate_phone, validate_password,
    validate_text_field, validate_capacity, collect_errors
)
from app import limiter

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
@role_required('SuperAdmin')
def dashboard():
    """SuperAdmin central control dashboard - real summary metrics"""
    hostels = Hostel.query.all()
    owners = User.query.filter_by(role='HostelOwner').all()
    residents = Resident.query.all()
    residents_count = len(residents)
    active_residents_count = sum(1 for r in residents if r.status == 'Active')
    total_capacity = sum(h.total_capacity for h in hostels)
    occupied_rooms = len(set(r.room_number for r in residents if r.room_number and r.status == 'Active')) or active_residents_count
    total_rent_collected = float(db.session.query(db.func.sum(Payment.amount)).filter(Payment.status == 'Verified').scalar() or 0.0)
    pending_rent_amount = float(db.session.query(db.func.sum(Payment.amount)).filter(Payment.status == 'Pending').scalar() or 0.0)
    pending_payments_count = Payment.query.filter_by(status='Pending').count()
    verified_payments_count = Payment.query.filter_by(status='Verified').count()
    
    return render_template('admin_dashboard.html', 
                           hostels=hostels, 
                           owners=owners, 
                           residents=residents,
                           residents_count=residents_count,
                           active_residents_count=active_residents_count,
                           total_capacity=total_capacity,
                           occupied_rooms=occupied_rooms,
                           total_rent_collected=total_rent_collected,
                           pending_rent_amount=pending_rent_amount,
                           pending_payments_count=pending_payments_count,
                           verified_payments_count=verified_payments_count)


@admin_bp.route('/hostels', methods=['GET'])
@role_required('SuperAdmin')
def hostels_list():
    """Manage hostels - list, details, creation and deletion controls"""
    hostels = Hostel.query.all()
    owners = User.query.filter_by(role='HostelOwner').all()
    return render_template('admin_hostels.html', hostels=hostels, owners=owners)


@admin_bp.route('/owners', methods=['GET'])
@role_required('SuperAdmin')
def owners_list():
    """Manage registered hostel owners"""
    owners = User.query.filter_by(role='HostelOwner').all()
    return render_template('admin_owners.html', owners=owners)


@admin_bp.route('/residents', methods=['GET'])
@role_required('SuperAdmin')
def residents_list():
    """View all platform residents organized hostel-wise"""
    hostels = Hostel.query.options(
        db.joinedload(Hostel.residents).joinedload(Resident.payments)
    ).all()
    return render_template('admin_residents.html', hostels=hostels)


@admin_bp.route('/owner/create', methods=['POST'])
@role_required('SuperAdmin')
@limiter.limit("10 per hour")
def create_owner():
    """Register a new Hostel Owner user account"""
    email    = request.form.get('email', '').strip()
    password = request.form.get('password', '')
    confirm_password = request.form.get('confirm_password', '')
    full_name = request.form.get('full_name', '').strip()
    phone    = request.form.get('phone', '').strip()

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
        return redirect(url_for('admin.owners_list'))

    if password != confirm_password:
        flash('Passwords do not match.', 'danger')
        return redirect(url_for('admin.owners_list'))

    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        flash('Email is already registered.', 'danger')
        return redirect(url_for('admin.owners_list'))

    new_owner = User(email=email, role='HostelOwner', full_name=full_name, phone=phone)
    new_owner.set_password(password)
    db.session.add(new_owner)
    db.session.commit()

    log_security_action(session['user_id'], f"Created new HostelOwner user account: {email}")
    flash(f'Hostel Owner account created for {email}!', 'success')
    return redirect(url_for('admin.owners_list'))


def _generate_hostel_code():
    """Generate a unique hostel code in the format HOS-YYYY-NNN."""
    year = datetime.utcnow().year
    existing_codes = db.session.query(Hostel.hostel_code).filter(
        Hostel.hostel_code.like(f"HOS-{year}-%")
    ).all()
    seq = len(existing_codes) + 1
    return f"HOS-{year}-{seq:03d}"


@admin_bp.route('/hostel/create', methods=['POST'])
@role_required('SuperAdmin')
@limiter.limit("20 per hour")
def create_hostel():
    """Create a new hostel and assign it to an owner"""
    name     = request.form.get('hostel_name', '').strip()
    location = request.form.get('location', '').strip()
    capacity_str = request.form.get('total_capacity', '100')
    owner_id = request.form.get('owner_id')
    rent = 0.0
    electricity_bill = 0.0

    # Server-side validation
    field_errors = collect_errors(
        validate_text_field(name, 'Hostel name', 150),
        validate_text_field(location, 'Location', 250),
        validate_capacity(capacity_str),
    )
    if field_errors:
        for err in field_errors:
            flash(err, 'danger')
        return redirect(url_for('admin.hostels_list'))

    capacity = int(capacity_str)

    # Facilities: collect from multi-select or text field
    facilities_list = request.form.getlist('facilities')
    if not facilities_list:
        raw = request.form.get('facilities_text', '').strip()
        facilities_list = [f.strip() for f in raw.split(',') if f.strip()]
    facilities_str = ','.join(facilities_list) if facilities_list else None

    if not owner_id:
        flash('Please select an owner first.', 'warning')
        return redirect(url_for('admin.hostels_list'))

    owner = User.query.get(owner_id)
    if not owner or owner.role != 'HostelOwner':
        flash('Selected user is not a valid Hostel Owner.', 'danger')
        return redirect(url_for('admin.hostels_list'))

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
    try:
        qr_path = generate_hostel_qr(new_hostel)
        new_hostel.hostel_qr_code = qr_path
        db.session.commit()
    except Exception as e:
        print(f"[WARN] Hostel QR generation failed: {e}")

    log_security_action(session['user_id'], f"Created new hostel '{name}' [{hostel_code}] assigned to owner {owner.email}")
    flash(f"Hostel '{name}' created with code {hostel_code}!", 'success')
    return redirect(url_for('admin.hostels_list'))


@admin_bp.route('/hostel/delete/<int:hostel_id>', methods=['POST'])
@role_required('SuperAdmin')
def delete_hostel(hostel_id):
    """Delete a hostel and clean up references"""
    hostel = Hostel.query.get_or_404(hostel_id)
    name = hostel.hostel_name
    
    residents_count = Resident.query.filter_by(hostel_id=hostel_id).count()
    if residents_count > 0:
        flash(f"Cannot delete hostel '{name}' because it contains active residents. Remove residents first.", 'danger')
        return redirect(url_for('admin.hostels_list'))

    # Clean up hostel QR code file
    delete_hostel_qr(hostel_id)

    db.session.delete(hostel)
    db.session.commit()

    log_security_action(session['user_id'], f"Deleted hostel '{name}'")
    flash(f"Hostel '{name}' was deleted successfully.", 'success')
    return redirect(url_for('admin.hostels_list'))


@admin_bp.route('/owner/delete/<int:owner_id>', methods=['POST'])
@role_required('SuperAdmin')
def delete_owner(owner_id):
    """Delete a hostel owner user"""
    owner = User.query.get_or_404(owner_id)
    email = owner.email

    # Prevent deleting owners if they have active hostels assigned to them
    hostel = Hostel.query.filter_by(owner_id=owner_id).first()
    if hostel:
        flash(f"Cannot delete owner {email} because they still manage hostel '{hostel.hostel_name}'. Reassign the hostel first.", 'danger')
        return redirect(url_for('admin.owners_list'))

    db.session.delete(owner)
    db.session.commit()

    log_security_action(session['user_id'], f"Deleted owner account: {email}")
    flash(f"Owner {email} deleted successfully.", 'success')
    return redirect(url_for('admin.owners_list'))


# ─── Pharmacy / Shop Approval ───────────────────────────────────────────────

@admin_bp.route('/shops')
@role_required('SuperAdmin')
def shops_list():
    """List all registered shops with their verification status"""
    from app.models.db import Shop
    pending_shops = Shop.query.filter_by(verification_status='Pending').all()
    approved_shops = Shop.query.filter_by(verification_status='Approved').all()
    rejected_shops = Shop.query.filter_by(verification_status='Rejected').all()
    return render_template('admin_shops.html',
                           pending_shops=pending_shops,
                           approved_shops=approved_shops,
                           rejected_shops=rejected_shops)


@admin_bp.route('/shops/<int:shop_id>/approve', methods=['POST'])
@role_required('SuperAdmin')
def approve_shop(shop_id):
    """Approve a pending shop, making it publicly visible on the marketplace"""
    from app.models.db import Shop
    shop = Shop.query.get_or_404(shop_id)
    shop.verification_status = 'Approved'
    db.session.commit()
    log_security_action(session['user_id'], f"Approved shop '{shop.shop_name}' (ID {shop.id})")
    flash(f'Shop "{shop.shop_name}" approved and is now live on the marketplace.', 'success')
    return redirect(url_for('admin.shops_list'))


@admin_bp.route('/shops/<int:shop_id>/reject', methods=['POST'])
@role_required('SuperAdmin')
def reject_shop(shop_id):
    """Reject a pending or previously approved shop"""
    from app.models.db import Shop
    shop = Shop.query.get_or_404(shop_id)
    shop.verification_status = 'Rejected'
    db.session.commit()
    log_security_action(session['user_id'], f"Rejected shop '{shop.shop_name}' (ID {shop.id})")
    flash(f'Shop "{shop.shop_name}" has been rejected.', 'warning')
    return redirect(url_for('admin.shops_list'))
