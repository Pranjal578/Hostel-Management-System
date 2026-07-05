from flask import Blueprint, jsonify, session, request
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


@api_bp.route('/residents/search', methods=['GET'])
@role_required('SuperAdmin')
def search_residents_globally():
    """Real-time global search for residents across all hostels"""
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])
        
    residents = Resident.query.join(Hostel).filter(
        (Resident.full_name.ilike(f'%{query}%')) |
        (Resident.room_number.ilike(f'%{query}%')) |
        (Hostel.hostel_name.ilike(f'%{query}%'))
    ).options(db.joinedload(Resident.payments)).limit(50).all()
    
    results = []
    for r in residents:
        results.append({
            'id': r.id,
            'full_name': r.full_name,
            'room_number': r.room_number,
            'hostel_name': r.hostel.hostel_name,
            'hostel_id': r.hostel_id,
            'email': r.user.email,
            'payment_status': r.payment_status
        })
        
    return jsonify(results)


@api_bp.route('/chat/messages/<int:recipient_id>', methods=['GET'])
@role_required('HostelOwner', 'Resident')
def get_chat_messages(recipient_id):
    """Retrieve chat history between current user and recipient"""
    from app.models.db import Message
    current_user_id = session['user_id']
    messages = Message.query.filter(
        ((Message.sender_id == current_user_id) & (Message.receiver_id == recipient_id)) |
        ((Message.sender_id == recipient_id) & (Message.receiver_id == current_user_id))
    ).order_by(Message.created_at.asc()).all()
    
    # Mark incoming messages as read
    unread_incoming = [m for m in messages if m.receiver_id == current_user_id and not m.is_read]
    for m in unread_incoming:
        m.is_read = True
    if unread_incoming:
        db.session.commit()

    return jsonify([{
        'id': m.id,
        'sender_id': m.sender_id,
        'receiver_id': m.receiver_id,
        'message_content': m.message_content,
        'created_at': m.created_at.strftime('%I:%M %p | %b %d'),
        'is_read': m.is_read
    } for m in messages])


@api_bp.route('/chat/messages/<int:recipient_id>', methods=['POST'])
@role_required('HostelOwner', 'Resident')
def send_chat_message(recipient_id):
    """Send a new message to a recipient"""
    from app.models.db import Message
    current_user_id = session['user_id']
    
    # Check JSON or form request
    content = ""
    if request.is_json:
        content = request.json.get('message_content', '').strip()
    else:
        content = request.form.get('message_content', '').strip()
        
    if not content:
        return jsonify({'error': 'Message content cannot be empty'}), 400
        
    msg = Message(
        sender_id=current_user_id,
        receiver_id=recipient_id,
        message_content=content
    )
    db.session.add(msg)
    db.session.commit()
    
    return jsonify({
        'id': msg.id,
        'sender_id': msg.sender_id,
        'receiver_id': msg.receiver_id,
        'message_content': msg.message_content,
        'created_at': msg.created_at.strftime('%I:%M %p | %b %d'),
        'is_read': msg.is_read
    })

