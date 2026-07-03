from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.models.db import db, User, Hostel, Resident
from app.routes.auth import role_required, log_security_action

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
@role_required('SuperAdmin')
def dashboard():
    """SuperAdmin central control dashboard"""
    hostels = Hostel.query.all()
    owners = User.query.filter_by(role='HostelOwner').all()
    residents_count = Resident.query.count()
    
    # Calculate statistics
    total_capacity = sum(h.total_capacity for h in hostels)
    
    return render_template('admin_dashboard.html', 
                           hostels=hostels, 
                           owners=owners, 
                           residents_count=residents_count,
                           total_capacity=total_capacity)


@admin_bp.route('/owner/create', methods=['GET', 'POST'])
@role_required('SuperAdmin')
def create_owner():
    """Register a new Hostel Owner user account"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('admin.dashboard'))

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email is already registered.', 'danger')
            return redirect(url_for('admin.dashboard'))

        # Create Hostel Owner account
        new_owner = User(email=email, role='HostelOwner')
        new_owner.set_password(password)
        db.session.add(new_owner)
        db.session.commit()

        log_security_action(session['user_id'], f"Created new HostelOwner user account: {email}")
        flash(f'Hostel Owner account created for {email}!', 'success')
        return redirect(url_for('admin.dashboard'))

    return render_template('admin_login.html') # Form modal is on dashboard


@admin_bp.route('/hostel/create', methods=['POST'])
@role_required('SuperAdmin')
def create_hostel():
    """Create a new hostel and assign it to an owner"""
    name = request.form.get('hostel_name', '').strip()
    location = request.form.get('location', '').strip()
    capacity = int(request.form.get('total_capacity', 100))
    owner_id = request.form.get('owner_id')

    if not owner_id:
        flash('Please select an owner first.', 'warning')
        return redirect(url_for('admin.dashboard'))

    # Verify owner exists and is an owner
    owner = User.query.get(owner_id)
    if not owner or owner.role != 'HostelOwner':
        flash('Selected user is not a valid Hostel Owner.', 'danger')
        return redirect(url_for('admin.dashboard'))

    new_hostel = Hostel(
        hostel_name=name,
        location=location,
        total_capacity=capacity,
        owner_id=owner_id
    )
    db.session.add(new_hostel)
    db.session.commit()

    log_security_action(session['user_id'], f"Created new hostel '{name}' assigned to owner {owner.email}")
    flash(f"Hostel '{name}' has been created successfully!", 'success')
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/hostel/delete/<int:hostel_id>', methods=['POST'])
@role_required('SuperAdmin')
def delete_hostel(hostel_id):
    """Delete a hostel and clean up references"""
    hostel = Hostel.query.get_or_404(hostel_id)
    name = hostel.hostel_name
    
    # We must restrict deleting hostels with active residents to prevent orphan profiles, 
    # or handle cascade deletion. Let's prevent deletion if there are active residents.
    residents_count = Resident.query.filter_by(hostel_id=hostel_id).count()
    if residents_count > 0:
        flash(f"Cannot delete hostel '{name}' because it contains active residents. Remove residents first.", 'danger')
        return redirect(url_for('admin.dashboard'))

    db.session.delete(hostel)
    db.session.commit()

    log_security_action(session['user_id'], f"Deleted hostel '{name}'")
    flash(f"Hostel '{name}' was deleted successfully.", 'success')
    return redirect(url_for('admin.dashboard'))


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
        return redirect(url_for('admin.dashboard'))

    db.session.delete(owner)
    db.session.commit()

    log_security_action(session['user_id'], f"Deleted owner account: {email}")
    flash(f"Owner {email} deleted successfully.", 'success')
    return redirect(url_for('admin.dashboard'))
