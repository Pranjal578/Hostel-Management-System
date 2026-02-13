from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
from models.db import db, Resident
from utils.qr_generator import generate_qr_code, delete_qr_code
from config import Config
from datetime import datetime
from functools import wraps
import os

app = Flask(__name__)
app.config.from_object(Config)

# Initialize database
db.init_app(app)

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

# ============= PUBLIC ROUTES =============

@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Resident registration"""
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
                emergency_contact_relation=request.form['emergency_contact_relation']
            )
            
            # Set password
            resident.set_password(request.form['password'])
            
            # Save to database
            db.session.add(resident)
            db.session.commit()
            
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
    """Resident login"""
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        resident = Resident.query.filter_by(email=email).first()
        
        if resident and resident.check_password(password):
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
    """Edit resident profile"""
    resident = Resident.query.get(session['resident_id'])
    
    if request.method == 'POST':
        try:
            # Update allowed fields only
            resident.phone = request.form['phone']
            resident.permanent_address = request.form['permanent_address']
            resident.city = request.form['city']
            resident.state = request.form['state']
            resident.pincode = request.form['pincode']
            resident.emergency_contact_name = request.form['emergency_contact_name']
            resident.emergency_contact_phone = request.form['emergency_contact_phone']
            resident.emergency_contact_relation = request.form['emergency_contact_relation']
            
            # Update password if provided
            if request.form.get('new_password'):
                resident.set_password(request.form['new_password'])
            
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('resident_dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Update failed: {str(e)}', 'danger')
    
    return render_template('edit_profile.html', resident=resident)

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
    
    qr_path = f"static/qr/{resident_id}.png"
    if os.path.exists(qr_path):
        return send_file(qr_path, as_attachment=True, download_name=f'qr_code_{resident_id}.png')
    else:
        flash('QR code not found!', 'danger')
        return redirect(url_for('resident_dashboard'))

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
    app.run(debug=True, host='0.0.0.0', port=5000)
