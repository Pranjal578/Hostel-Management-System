from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.models.db import db, User, Hostel, Resident
from app.routes.auth import role_required, log_security_action
from app.utils.qr_generator import generate_hostel_qr, delete_hostel_qr

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
@role_required('SuperAdmin')
def dashboard():
    """SuperAdmin central control dashboard - high level summary metrics"""
    hostels = Hostel.query.all()
    owners = User.query.filter_by(role='HostelOwner').all()
    residents_count = Resident.query.count()
    total_capacity = sum(h.total_capacity for h in hostels)
    
    return render_template('admin_dashboard.html', 
                           hostels=hostels, 
                           owners=owners, 
                           residents_count=residents_count,
                           total_capacity=total_capacity)


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
def create_owner():
    """Register a new Hostel Owner user account"""
    email = request.form.get('email', '').strip()
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')
    full_name = request.form.get('full_name', '').strip()
    phone = request.form.get('phone', '').strip()

    if not full_name or not phone:
        flash('Full name and phone number are required.', 'danger')
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
def create_hostel():
    """Create a new hostel and assign it to an owner"""
    name = request.form.get('hostel_name', '').strip()
    location = request.form.get('location', '').strip()
    capacity = int(request.form.get('total_capacity', 100))
    owner_id = request.form.get('owner_id')
    rent = 0.0
    electricity_bill = 0.0

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
