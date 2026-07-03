from flask import Blueprint, jsonify, session
from app.models.db import db, Resident, Hostel, Payment, User
from app.routes.auth import role_required

api_bp = Blueprint('api', __name__)

@api_bp.route('/resident-details/<int:resident_id>', methods=['GET'])
@role_required('HostelOwner', 'SuperAdmin')
def get_resident_details(resident_id):
    """Retrieve full details of a resident by ID for QR scanners (Admin/Owner only)"""
    resident = Resident.query.get_or_404(resident_id)
    
    # Enforce Hostel Owner scope isolation
    user = User.query.get(session['user_id'])
    if user.role == 'HostelOwner':
        hostel = Hostel.query.filter_by(owner_id=user.id).first()
        if not hostel or resident.hostel_id != hostel.id:
            return jsonify({'error': 'Access denied. Resident belongs to a different hostel.'}), 403

    # Fetch payments history
    payments = Payment.query.filter_by(resident_id=resident.id).order_by(Payment.created_at.desc()).all()
    payments_list = []
    for p in payments:
        payments_list.append({
            'amount': p.amount,
            'payment_date': p.payment_date.strftime('%Y-%m-%d'),
            'transaction_id': p.transaction_id,
            'status': p.status
        })

    # Prepare response JSON payload
    data = {
        'id': resident.id,
        'full_name': resident.full_name,
        'email': resident.user.email,
        'phone': resident.phone_decrypted,
        'date_of_birth': resident.date_of_birth.strftime('%Y-%m-%d'),
        'gender': resident.gender,
        'room_number': resident.room_number,
        'date_of_joining': resident.date_of_joining.strftime('%Y-%m-%d'),
        'permanent_address': resident.permanent_address_decrypted,
        'city': resident.city,
        'state': resident.state,
        'pincode': resident.pincode,
        'emergency_contact_name': resident.emergency_contact_name,
        'emergency_contact_phone': resident.emergency_contact_phone,
        'emergency_contact_relation': resident.emergency_contact_relation,
        'guardian_name': resident.guardian_name,
        'guardian_phone': resident.guardian_phone,
        'guardian_email': resident.guardian_email,
        'profile_image': resident.profile_image,
        'payments': payments_list
    }
    
    return jsonify(data)
