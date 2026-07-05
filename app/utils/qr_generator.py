import qrcode
import json
import os
from flask import current_app

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

def generate_qr_code(resident_id, base_url=None):
    if base_url is None:
        base_url = current_app.config.get('BASE_URL', 'http://127.0.0.1:5000')
    
    qr_dir = os.path.join(BASE_DIR, 'static', 'qr')
    if not os.path.exists(qr_dir):
        os.makedirs(qr_dir)
    
    profile_url = f"{base_url}/profile/{resident_id}"
    
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
    qr.add_data(profile_url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    qr_filename = f"{resident_id}.png"
    qr_path = os.path.join(qr_dir, qr_filename)
    img.save(qr_path)
    
    return qr_filename

def delete_qr_code(resident_id):
    qr_path = os.path.join(BASE_DIR, 'static', 'qr', f"{resident_id}.png")
    if os.path.exists(qr_path):
        os.remove(qr_path)


def generate_hostel_qr(hostel, base_url=None):
    """Generate a public info QR code for a hostel, encoding key details as JSON."""
    if base_url is None:
        try:
            base_url = current_app.config.get('BASE_URL', 'http://127.0.0.1:5000')
        except RuntimeError:
            base_url = 'http://127.0.0.1:5000'

    qr_dir = os.path.join(BASE_DIR, 'static', 'qr')
    os.makedirs(qr_dir, exist_ok=True)

    view_url = f"{base_url}/hostel/view/{hostel.id}"

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4
    )
    qr.add_data(view_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    qr_filename = f"hostel_{hostel.id}.png"
    qr_path = os.path.join(qr_dir, qr_filename)
    img.save(qr_path)

    return f"/static/qr/{qr_filename}"


def delete_hostel_qr(hostel_id):
    """Delete the hostel-level QR code image file."""
    qr_path = os.path.join(BASE_DIR, 'static', 'qr', f"hostel_{hostel_id}.png")
    if os.path.exists(qr_path):
        os.remove(qr_path)