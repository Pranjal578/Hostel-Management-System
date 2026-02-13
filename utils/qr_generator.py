import qrcode
import os
from flask import url_for

def generate_qr_code(resident_id, base_url='http://127.0.0.1:5000'):
    """
    Generate QR code for resident profile
    
    Args:
        resident_id: The ID of the resident
        base_url: Base URL of the application
    
    Returns:
        str: Filename of the generated QR code
    """
    # Create QR code directory if it doesn't exist
    qr_dir = 'static/qr'
    if not os.path.exists(qr_dir):
        os.makedirs(qr_dir)
    
    # Generate profile URL
    profile_url = f"{base_url}/profile/{resident_id}"
    
    # Create QR code instance
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    
    # Add data to QR code
    qr.add_data(profile_url)
    qr.make(fit=True)
    
    # Create QR code image
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Save QR code
    qr_filename = f"{resident_id}.png"
    qr_path = os.path.join(qr_dir, qr_filename)
    img.save(qr_path)
    
    return qr_filename

def delete_qr_code(resident_id):
    """
    Delete QR code for a resident
    
    Args:
        resident_id: The ID of the resident
    """
    qr_path = f"static/qr/{resident_id}.png"
    if os.path.exists(qr_path):
        os.remove(qr_path)
