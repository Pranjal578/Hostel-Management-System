from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.models.db import db, User, Resident, Hostel
from app.routes.auth import role_required, log_security_action
from app.utils.photo_handler import save_photo, validate_photo

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/', methods=['GET'])
@role_required('Resident', 'HostelOwner', 'SuperAdmin')
def index():
    """Render Settings Dashboard"""
    user_id = session['user_id']
    user = User.query.get_or_404(user_id)
    
    resident = None
    if user.role == 'Resident':
        resident = Resident.query.filter_by(user_id=user_id).first_or_404()
        
    return render_template('otp_settings.html', user=user, resident=resident)


@settings_bp.route('/profile', methods=['POST'])
@role_required('Resident', 'HostelOwner', 'SuperAdmin')
def update_profile():
    """Update user contact details (Residents cannot change room or hostel details)"""
    user_id = session['user_id']
    user = User.query.get_or_404(user_id)
    
    if user.role == 'Resident':
        resident = Resident.query.filter_by(user_id=user_id).first_or_404()
        
        try:
            phone = request.form.get('phone', '').strip()
            
            # Check phone uniqueness excluding self
            all_residents = Resident.query.all()
            for r in all_residents:
                if r.id != resident.id and r.phone_decrypted == phone:
                    flash('Phone number is already in use by another resident.', 'danger')
                    return redirect(url_for('settings.index'))

            # Write editable fields
            resident.phone_decrypted = phone
            resident.permanent_address_decrypted = request.form.get('permanent_address', '').strip()
            resident.city = request.form.get('city', '').strip()
            resident.state = request.form.get('state', '').strip()
            resident.pincode = request.form.get('pincode', '').strip()
            
            resident.emergency_contact_name = request.form.get('emergency_contact_name', '').strip()
            resident.emergency_contact_phone = request.form.get('emergency_contact_phone', '').strip()
            resident.emergency_contact_relation = request.form.get('emergency_contact_relation', '').strip()
            resident.emergency_contact_address = request.form.get('emergency_contact_address', '').strip() or None
            
            resident.guardian_name = request.form.get('guardian_name', '').strip() or None
            resident.guardian_phone = request.form.get('guardian_phone', '').strip() or None
            resident.guardian_email = request.form.get('guardian_email', '').strip() or None
            resident.guardian_relation = request.form.get('guardian_relation', '').strip() or None

            # Handle optional photo upload
            photo_file = request.files.get('profile_photo')
            if photo_file and photo_file.filename:
                is_valid, error_msg = validate_photo(photo_file)
                if not is_valid:
                    flash(f'Photo error: {error_msg}', 'warning')
                else:
                    success, error = save_photo(photo_file, resident.id, db, resident)
                    if not success:
                        flash(f'Photo upload error: {error}', 'warning')

            db.session.commit()
            log_security_action(user_id, "Updated profile contact details")
            flash('Profile details updated successfully!', 'success')
            
        except Exception as e:
            db.session.rollback()
            flash(f'Failed to update profile: {str(e)}', 'danger')
            
    else:
        # HostelOwner profile update (only updates user email)
        email = request.form.get('email', '').strip()
        confirm_password = request.form.get('confirm_password')
        
        if not confirm_password or not user.check_password(confirm_password):
            flash('Re-authentication failed. Incorrect password.', 'danger')
            return redirect(url_for('settings.index'))
            
        if email:
            existing = User.query.filter_by(email=email).first()
            if existing and existing.id != user.id:
                flash('Email is already registered by another user.', 'danger')
                return redirect(url_for('settings.index'))
            user.email = email
            db.session.commit()
            log_security_action(user_id, "Updated account login email")
            flash('Login email updated successfully!', 'success')
            
    return redirect(url_for('settings.index'))


@settings_bp.route('/security', methods=['POST'])
@role_required('Resident', 'HostelOwner', 'SuperAdmin')
def update_security():
    """Verify current password and change login credentials"""
    user_id = session['user_id']
    user = User.query.get_or_404(user_id)
    
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_new_password = request.form.get('confirm_new_password')
    
    if not current_password or not new_password:
        flash('All password fields are required.', 'warning')
        return redirect(url_for('settings.index'))
        
    if not user.check_password(current_password):
        flash('Incorrect current password.', 'danger')
        return redirect(url_for('settings.index'))
        
    if new_password != confirm_new_password:
        flash('New passwords do not match.', 'danger')
        return redirect(url_for('settings.index'))
        
    if len(new_password) < 6:
        flash('New password must be at least 6 characters long.', 'danger')
        return redirect(url_for('settings.index'))
        
    # Apply password change
    user.set_password(new_password)
    db.session.commit()
    
    # Update current session's password version so this session stays active
    session['password_version'] = user.password_version
    
    log_security_action(user_id, "Changed account password (re-authenticated)")
    flash('Password changed successfully! Keep it secure.', 'success')
    return redirect(url_for('settings.index'))


@settings_bp.route('/otp', methods=['POST'])
@role_required('Resident', 'HostelOwner', 'SuperAdmin')
def update_otp():
    """Update Multi-Factor OTP delivery method (2FA is mandatory for all accounts)"""
    user_id = session['user_id']
    user = User.query.get_or_404(user_id)
    
    otp_method = request.form.get('otp_method', 'email').strip()
    confirm_password = request.form.get('confirm_password')
    
    if not confirm_password or not user.check_password(confirm_password):
        flash('Re-authentication failed. Incorrect password.', 'danger')
        return redirect(url_for('settings.index'))
        
    user.setup_otp(otp_method)
    action_msg = f"Updated 2FA delivery method to {otp_method}"
        
    db.session.commit()
    log_security_action(user_id, action_msg)
    flash(f'MFA Settings updated: {action_msg}. (2FA is mandatory for all system accounts)', 'success')
    return redirect(url_for('settings.index'))
